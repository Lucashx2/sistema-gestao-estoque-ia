from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import timedelta
import models
import schemas
import auth
import analytics
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SGE API", version="1.0.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Auth Helpers ---

def get_user_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not auth.verify_password(password, user.senha_hash):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "online"}

@app.post("/usuarios/", response_model=schemas.Usuario, tags=["Auth"])
def create_user(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    hashed_password = auth.get_password_hash(user.senha)
    db_user = models.Usuario(email=user.email, nome=user.nome, senha_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    
    access_token = auth.create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/produtos/", response_model=schemas.Produto, status_code=201, tags=["Produtos"])
def create_produto(produto: schemas.ProdutoCreate, db: Session = Depends(get_db), current_user: schemas.Usuario = Depends(get_current_user)):
    if db.query(models.Produto).filter(models.Produto.sku == produto.sku).first():
        raise HTTPException(status_code=400, detail="SKU já existente")
            
    novo_produto = models.Produto(**produto.dict())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

@app.get("/produtos/", response_model=List[schemas.Produto], tags=["Produtos"])
def list_produtos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Produto).offset(skip).limit(limit).all()

@app.get("/produtos/{produto_id}", response_model=schemas.Produto, tags=["Produtos"])
def get_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).options(joinedload(models.Produto.movimentacoes)).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@app.delete("/produtos/{produto_id}", status_code=204, tags=["Produtos"])
def delete_produto(produto_id: int, db: Session = Depends(get_db), current_user: schemas.Usuario = Depends(get_current_user)):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(produto)
    db.commit()
    return {"ok": True}

@app.post("/movimentacoes/", response_model=schemas.Movimentacao, tags=["Estoque"])
def create_movimentacao(mov: schemas.MovimentacaoCreate, db: Session = Depends(get_db), current_user: schemas.Usuario = Depends(get_current_user)):
    # Row locking para consistência
    db_produto = db.query(models.Produto).filter(models.Produto.id == mov.produto_id).with_for_update().first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    novo_estoque = db_produto.estoque_atual
    if mov.tipo in [models.TipoMovimentacao.saida, models.TipoMovimentacao.ajuste_negativo]:
        if db_produto.estoque_atual < mov.quantidade:
            raise HTTPException(status_code=400, detail="Estoque insuficiente")
        novo_estoque -= mov.quantidade
    else:
        novo_estoque += mov.quantidade
        
    try:
        db_mov = models.Movimentacao(**mov.dict(), usuario_id=current_user.id)
        db.add(db_mov)
        db_produto.estoque_atual = novo_estoque
        db.commit()
        db.refresh(db_mov)
        return db_mov
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats", tags=["Analytics"])
def dashboard_stats(db: Session = Depends(get_db), current_user: schemas.Usuario = Depends(get_current_user)):
    return analytics.get_dashboard_stats(db)

@app.get("/produtos/{produto_id}/previsao", tags=["Analytics"])
def previsao_demanda(produto_id: int, db: Session = Depends(get_db), current_user: schemas.Usuario = Depends(get_current_user)):
    resultado = analytics.prever_demanda(db, produto_id)
    if resultado.get("status") == "erro":
         raise HTTPException(status_code=400, detail=resultado["mensagem"])
    return resultado