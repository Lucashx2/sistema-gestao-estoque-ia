from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from models import TipoMovimentacao

# --- Movimentação ---
class MovimentacaoBase(BaseModel):
    produto_id: int
    tipo: TipoMovimentacao
    quantidade: int
    motivo: Optional[str] = None

class MovimentacaoCreate(MovimentacaoBase):
    pass

class Movimentacao(MovimentacaoBase):
    id: int
    data_hora: datetime
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Produto ---
class ProdutoBase(BaseModel):
    sku: str
    nome: str
    descricao: Optional[str] = None
    preco_custo: float
    preco_venda: float
    estoque_minimo: int = 0

class ProdutoCreate(ProdutoBase):
    pass

class Produto(ProdutoBase):
    id: int
    estoque_atual: int
    movimentacoes: List[Movimentacao] = [] 

    class Config:
        from_attributes = True

# --- Usuário ---
class UsuarioBase(BaseModel):
    email: str
    nome: str

class UsuarioCreate(UsuarioBase):
    senha: str

class Usuario(UsuarioBase):
    id: int

    class Config:
        from_attributes = True

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None