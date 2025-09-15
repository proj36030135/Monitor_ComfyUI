# Backend de Observabilidade ComfyUI - MVP

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://sqlalchemy.org)

Backend local-first para observabilidade de runs/gerações feitas com pipelines do ComfyUI. O serviço coleta e persiste amostras de métricas (GPU/CPU/RAM/processo), marca eventos (início/fim de sessão e run), agrega séries temporais para visualização, exporta dados e aplica políticas de retenção.

## Stack Tecnológica

- **API**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy 2.0 
- **Migrações**: Alembic
- **Validação**: Pydantic v2
- **Banco**: SQLite (WAL mode)
- **Execução**: Local no PC do usuário (host loopback)

## Instalação e Configuração

### 1. Requisitos

- Python 3.9+
- pip ou pipenv

### 2. Instalação

```bash
# Clonar o repositório
git clone <repository-url>
cd monitor-comfyui

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual (Windows)
.venv\\Scripts\\activate

# Ativar ambiente virtual (Linux/Mac)
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração do Banco de Dados

```bash
# Executar migrações iniciais
alembic upgrade head
```

## Execução Local

### Desenvolvimento

```bash
# Com reload automático
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload

# Ou usando variáveis de ambiente
uvicorn app.main:app --host $APP_HOST --port $APP_PORT --reload
```

### Produção

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --workers 1
```

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações da aplicação
APP_HOST=127.0.0.1
APP_PORT=8080

# Configurações do banco de dados  
DB_URL=sqlite:///./app.db
DB_ECHO=false

# CORS (desenvolvimento)
CORS_ORIGINS=http://localhost,http://127.0.0.1

# Outros
MAX_BODY_MB=5
```

### Descrição das Variáveis

| Variável | Padrão | Descrição |
|----------|---------|-----------|
| `APP_HOST` | `127.0.0.1` | Host do servidor |
| `APP_PORT` | `8080` | Porta do servidor |
| `DB_URL` | `sqlite:///./app.db` | URL de conexão do banco |
| `DB_ECHO` | `false` | Exibir queries SQL no log |
| `CORS_ORIGINS` | `http://localhost,http://127.0.0.1` | Origins permitidas para CORS |
| `MAX_BODY_MB` | `5` | Tamanho máximo do body da requisição |

## Endpoints Disponíveis

### Health Check

```bash
# Verificar saúde do serviço
curl http://127.0.0.1:8080/health
```

### Documentação

- **Swagger UI**: http://127.0.0.1:8080/docs
- **ReDoc**: http://127.0.0.1:8080/redoc
- **OpenAPI Schema**: http://127.0.0.1:8080/openapi.json

## Estrutura do Projeto

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação FastAPI principal
│   ├── db.py                # Configuração do banco de dados
│   ├── crud/                # Operações CRUD
│   ├── services/            # Camada de serviços (retenção, agregações)
│   └── routers/             # Roteadores da API
├── alembic/                 # Migrações do banco
├── alembic.ini              # Configuração do Alembic
├── requirements.txt         # Dependências Python
└── README.md               # Este arquivo
```

## Desenvolvimento

### Formatação e Linting

```bash
# Formatação com Black
black app/ alembic/

# Linting com Ruff
ruff check app/ alembic/

# Correção automática com Ruff
ruff check --fix app/ alembic/
```

### Testes

```bash
# Executar testes
pytest

# Com coverage
pytest --cov=app tests/
```

### Migrações

```bash
# Criar nova migração
alembic revision --autogenerate -m "Descrição da migração"

# Aplicar migrações
alembic upgrade head

# Reverter migração
alembic downgrade -1

# Ver histórico
alembic history
```

## Arquitetura

### Componentes

- **API HTTP (FastAPI)**: Roteadores para `sessions`, `runs`, `ingest`, `samples`, `export`, `profiles`, `preferences`, `health`
- **Camada de Serviços**: Regras de retenção, agregações, downsample
- **Persistência (SQLite)**: Esquema relacional otimizado para leituras por janela temporal

### Padrões e Convenções

- **Timestamps**: epoch **ms** (INTEGER)
- **IDs**: `uuid4` (TEXT)
- **Serialização**: JSON (UTF-8)
- **CORS**: restrito a `http://localhost`/`127.0.0.1`

## Configurações SQLite

O banco está configurado com:
- **WAL mode**: Para melhor concorrência (leitores não bloqueiam escritores)
- **synchronous=NORMAL**: Performance balanceada
- **foreign_keys=ON**: Integridade referencial
- **temp_store=MEMORY**: Performance otimizada
- **Cache otimizado**: ~40MB de cache para performance

## Resolução de Problemas

### Erro de conexão com banco

```bash
# Verificar se o arquivo do banco existe
ls -la app.db

# Recriar banco se necessário
rm app.db
alembic upgrade head
```

### Erro de importação

```bash
# Verificar se o ambiente virtual está ativo
which python

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Problemas com CORS

Verifique se as origins estão configuradas corretamente na variável `CORS_ORIGINS`.

## Suporte

Para dúvidas, problemas ou sugestões, consulte a documentação técnica detalhada no DSD ou abra uma issue no repositório.

## Roadmap

- [ ] Implementação dos endpoints de sessões
- [ ] Sistema de ingestão de métricas
- [ ] Agregações e downsample
- [ ] Sistema de export
- [ ] Políticas de retenção
- [ ] Interface web (viewer)

---

**Versão**: 0.1.0  
**Status**: MVP em desenvolvimento  
**Stack**: FastAPI + SQLAlchemy 2.0 + SQLite (WAL)
