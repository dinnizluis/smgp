# SMGP — Sistema de Monitoramento de Gastos Pessoais (MVP)

Breve: aplicação local para importar transações via CSV, persistir em SQLite e exibir um dashboard simples.

## Requisitos
- Python 3.10+
- `pip`

## Setup rápido (macOS / Linux)

1. Criar e ativar um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instalar dependências principais:

```bash
pip install --upgrade pip
pip install -r requirements.txt
# pytest é usado para executar testes
pip install pytest
```

## Inicializar o banco de dados

O arquivo do banco do MVP será criado em `data/smgp.db`.

Para criar o arquivo e aplicar o esquema mínimo execute:

```bash
python - <<'PY'
from infrastructure.database import init_db
init_db('data/smgp.db')
print('DB criado em data/smgp.db')
PY
```

Ou usar o helper que também garante a categoria padrão:

```bash
python - <<'PY'
from infrastructure.repositories import bootstrap
bootstrap('data/smgp.db')
print('DB inicializado com categoria padrão')
PY
```

## Rodar a aplicação (Streamlit)

```bash
streamlit run app/dashboard.py
```

Abra o navegador no endereço informado pelo Streamlit (por padrão `http://localhost:8501`).

## Executar testes

Os testes usam `pytest` e criam um banco temporário para validar inicialização, inserção e deduplicação.

```bash
pytest -q
```

## Comandos úteis

- Remover DB local e reiniciar:

```bash
rm -f data/smgp.db
python - <<'PY'
from infrastructure.database import init_db
init_db('data/smgp.db')
PY
```

- Verificar tabelas criadas:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect('data/smgp.db')
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
print(cur.fetchall())
conn.close()
PY
```

## Notas
- Importers não devem persistir diretamente: eles retornam estruturas que a camada `application` deve entregar aos `repositories` (ver `importers/`).
- O MVP usa `sqlite3` da stdlib para minimizar dependências; migrar para `SQLAlchemy` é uma opção futura.

---

Se quiser, eu posso adicionar instruções para executar o dashboard sem streamlit (modo headless) ou um Makefile para simplificar os comandos.
