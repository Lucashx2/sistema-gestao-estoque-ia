# Sistema de Gestão de Estoque Inteligente (SGE) 🚀

API RESTful para controle de estoque com autenticação segura e módulo de inteligência artificial para previsão de demanda.

## 📋 Funcionalidades

- **Gestão de Produtos:** CRUD completo.
- **Controle de Estoque Transacional:** Entradas e Saídas com atualização atômica e prevenção de inconsistências (Race Conditions).
- **Autenticação Segura:** Sistema de Login/Registro com JWT (JSON Web Tokens) e Hashing de senhas (Bcrypt).
- **Dashboard Analytics:** KPIs em tempo real sobre valor em estoque e alertas de reposição.
- **IA de Previsão de Demanda:** Algoritmo de Machine Learning (Regressão Linear) que analisa o histórico de movimentações para prever vendas futuras.

## 🛠 Tecnologias

- **Language:** Python 3.13+
- **Framework:** FastAPI
- **Database:** PostgreSQL & SQLAlchemy ORM
- **Auth:** PyJWT & Passlib
- **Data Science:** Pandas & Scikit-Learn

## 🚀 Como Rodar

1. Clone o repositório.
2. Crie um ambiente virtual: `python -m venv venv`
3. Instale as dependências: `pip install -r requirements.txt`
4. Configure o banco de dados no arquivo `database.py`.
5. Execute a API: `uvicorn main:app --reload`
6. Acesse a documentação automática: `http://localhost:8000/docs`
