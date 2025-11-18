from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class TipoMovimentacao(enum.Enum):
    entrada = "entrada"
    saida = "saida"
    ajuste_positivo = "ajuste_positivo"
    ajuste_negativo = "ajuste_negativo"

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, index=True)
    descricao = Column(String, nullable=True)
    preco_custo = Column(Float, nullable=False)
    preco_venda = Column(Float, nullable=False)
    estoque_atual = Column(Integer, default=0)
    estoque_minimo = Column(Integer, default=0)
    
    movimentacoes = relationship("Movimentacao", back_populates="produto")

class Movimentacao(Base):
    __tablename__ = "movimentacoes"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    quantidade = Column(Integer, nullable=False)
    data_hora = Column(DateTime(timezone=True), server_default=func.now())
    motivo = Column(String, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    produto = relationship("Produto", back_populates="movimentacoes")