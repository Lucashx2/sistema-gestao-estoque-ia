from sqlalchemy.orm import Session
import models
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def get_dashboard_stats(db: Session):
    """Retorna KPIs gerais de estoque e alertas de nível mínimo."""
    produtos = db.query(models.Produto).all()
    
    total_produtos = len(produtos)
    valor_total_estoque = sum([p.preco_custo * p.estoque_atual for p in produtos])
    produtos_baixo_estoque = [p for p in produtos if p.estoque_atual <= p.estoque_minimo]
    
    return {
        "total_produtos": total_produtos,
        "valor_total_estoque": round(valor_total_estoque, 2),
        "qtd_baixo_estoque": len(produtos_baixo_estoque),
        "lista_baixo_estoque": [{"id": p.id, "nome": p.nome, "estoque": p.estoque_atual} for p in produtos_baixo_estoque]
    }

def prever_demanda(db: Session, produto_id: int):
    """Gera previsão de vendas (30 dias) usando Regressão Linear baseada no histórico de saídas."""
    movimentacoes = db.query(models.Movimentacao).filter(
        models.Movimentacao.produto_id == produto_id,
        models.Movimentacao.tipo == models.TipoMovimentacao.saida
    ).all()
    
    if len(movimentacoes) < 3:
        return {"status": "erro", "mensagem": "Dados insuficientes para previsão (mínimo 3 pontos de dados)."}

    data = []
    data_inicial = movimentacoes[0].data_hora.date()

    for mov in movimentacoes:
        dias = (mov.data_hora.date() - data_inicial).days
        data.append({"dia": dias, "qtd": mov.quantidade})
    
    df = pd.DataFrame(data)
    df_agrupado = df.groupby("dia").sum().reset_index()
    
    X = df_agrupado[["dia"]]
    y = df_agrupado["qtd"]
    
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    ultimo_dia = df_agrupado["dia"].max()
    futuro_dia = np.array([[ultimo_dia + 30]])
    
    previsao = modelo.predict(futuro_dia)
    qtd_prevista = max(0, int(previsao[0]))
    tendencia = "Crescimento" if modelo.coef_[0] > 0 else "Queda"
    
    return {
        "status": "sucesso",
        "previsao_30_dias": qtd_prevista,
        "tendencia": tendencia,
        "historico_processado": len(df_agrupado)
    }