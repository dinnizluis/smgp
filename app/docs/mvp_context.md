# **📘 CONTEXTO DO PROJETO — MVP**

## **Sistema de Monitoramento de Gastos Pessoais (MVP v0.1)**

# **1. Visão Geral do Produto**

O projeto consiste em uma aplicação local para monitoramento de gastos pessoais.

Objetivo principal do MVP:

Permitir que o usuário:

- Importe transações via CSV
- Visualize o total gasto na semana atual
- Compare com a semana anterior
- Visualize gastos por categoria
- Edite categorias manualmente

A aplicação será:

- Local
- Single user
- Sem autenticação
- Sem integração bancária automática
- Sem Open Finance

---

# **2. Stack Tecnológica**

- Python 3.10+
- Streamlit (UI)
- SQLite (persistência local)
- Pandas (manipulação de dados)
- VS Code + Copilot

Não usar:

- Frameworks web complexos
- ORMs pesados (SQLAlchemy apenas se necessário)
- Microservices
- Docker neste MVP

---

# **3. Arquitetura do Sistema**

Arquitetura modular em camadas.

Estrutura de pastas:

```
personal-finance-dashboard/
│
├── app/                # Camada de apresentação (Streamlit)
│   ├── dashboard.py
│   └── components.py
│
├── domain/             # Regras de negócio puras
│   ├── models.py
│   └── services.py
│
├── application/        # Orquestração de casos de uso
│   └── use_cases.py
│
├── infrastructure/     # Banco e persistência
│   ├── database.py
│   └── repositories.py
│
├── importers/          # Adapters de entrada (CSV)
│   ├── csv_importer.py
│   └── normalizer.py
│
├── tests/
│
├── main.py
└── requirements.txt
```

---

# **4. Princípios Arquiteturais**

1. Separação clara de responsabilidades.
2. UI nunca acessa banco diretamente.
3. Importers não salvam no banco.
4. Domain não depende de SQLite.
5. Regras de negócio não ficam na camada de UI.

Fluxo esperado:

```
Streamlit (app)
   ↓
Application (use_cases)
   ↓
Importers / Domain
   ↓
Repository (infrastructure)
   ↓
SQLite
```

---

# **5. Modelo de Dados (MVP)**

## **Tabela: categories**

Campos:

- id (TEXT, PK)
- name (TEXT, UNIQUE, NOT NULL)
- created_at (DATETIME)

Categoria padrão obrigatória:

- “Não categorizado”

---

## **Tabela: transactions**

Campos:

- id (TEXT, PK)
- date (DATE, NOT NULL)
- description (TEXT, NOT NULL)
- amount (REAL, NOT NULL)
- account_type (TEXT, NOT NULL) # checking / credit
- category_id (TEXT, FK)
- created_at (DATETIME, NOT NULL)

Regras:

- amount < 0 → saída
- amount > 0 → entrada
- Deduplicação baseada em:
    - date
    - amount
    - description

---

# **6. Funcionalidades do MVP**

## **6.1 Importação de CSV**

O sistema deve:

- Permitir upload via Streamlit
- Ler CSV com colunas:
    - date
    - description
    - amount
- Normalizar:
    - Datas para formato ISO
    - Valores para float
- Retornar lista estruturada de transações
- Persistir no banco via repository

Não deve:

- Salvar diretamente dentro do importer
- Misturar lógica de UI com parsing

---

## **6.2 Deduplicação**

Ao importar:

- Não permitir inserir transações idênticas
- Regra baseada em:
    - date
    - description
    - amount

Pode ser implementada:

- Via constraint
    
    ou
    
- Via verificação antes de insert

---

## **6.3 Consolidação Semanal**

Sistema deve calcular dinamicamente:

- Total da semana atual
- Total da semana anterior
- Variação percentual
- Total por categoria (semana atual)
- Evolução diária da semana

Não criar tabela de consolidação no MVP.

Usar queries com GROUP BY.

Semana baseada em ISO week.

---

## **6.4 Dashboard**

Deve conter:

1. Total da semana atual (em destaque)
2. Comparação com semana anterior
3. Gráfico de barras por categoria (semana atual)
4. Gráfico de linha com evolução diária

Interface simples, funcional, sem foco estético.

---

## **6.5 Categorização Manual**

Usuário deve poder:

- Visualizar transações
- Alterar categoria
- Persistir alteração

Sem regras automáticas neste MVP.

---

# **7. Fora do Escopo (Explícito)**

Não implementar:

- Open Finance
- API bancária
- Machine learning
- Regras automáticas de categorização
- Metas financeiras
- Alertas
- Deploy em nuvem
- Multiusuário
- Autenticação

Qualquer sugestão do Copilot que vá além disso deve ser ignorada.

---

# **8. Definição de Conclusão do MVP**

O MVP estará pronto quando:

- Importar CSV real
- Persistir transações
- Calcular semana atual corretamente
- Exibir dashboard funcional
- Permitir edição manual de categoria
- Ser utilizável por 2 semanas consecutivas

---

# **9. Estratégia de Desenvolvimento**

Prioridade de implementação:

1. Setup técnico
2. Banco e tabelas
3. Importação simples
4. Persistência
5. Consolidação semanal
6. Dashboard básico
7. Categorização manual

Implementar em vertical slices sempre que possível.

---

# **10. Diretrizes para Código**

- Funções pequenas e claras
- Sem lógica pesada dentro do Streamlit
- Repositories isolam SQL
- Importers apenas transformam dados
- Usar tipagem básica (type hints)
- Código legível > código “inteligente”

---

# **11. Objetivo Estratégico do Projeto**

Este projeto é:

- Ferramenta pessoal de controle financeiro
- Exercício de arquitetura limpa
- Potencial portfólio técnico
- Base futura para evolução

Prioridade:

Entregar valor real rapidamente, não perfeição arquitetural.