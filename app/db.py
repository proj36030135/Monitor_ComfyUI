"""Database configuration and session management."""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Base para todos os modelos SQLAlchemy
Base = declarative_base()

# URL da base de dados (SQLite por padrão)
DATABASE_URL = os.getenv("DB_URL", "sqlite:///./app.db")

# Configurações do engine SQLite otimizadas
engine_kwargs = {
    "echo": bool(os.getenv("DB_ECHO", "").lower() == "true"),
    "pool_pre_ping": True,
}

# Para SQLite, configuramos parâmetros específicos
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,  # Permite uso em threads múltiplas
        "timeout": 20,  # Timeout de conexão em segundos
    }

# Criar engine
engine = create_engine(DATABASE_URL, **engine_kwargs)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configura PRAGMAs otimizados para SQLite conforme DSD."""
    if engine.url.drivername.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        # WAL mode para melhor concorrência (leitores não bloqueiam escritores)
        cursor.execute("PRAGMA journal_mode=WAL")
        # Synchronous NORMAL para performance balanceada
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Foreign keys habilitadas para integridade referencial
        cursor.execute("PRAGMA foreign_keys=ON")
        # Temporary store em memória para performance
        cursor.execute("PRAGMA temp_store=MEMORY")
        # Cache size otimizado (páginas de 4KB, ~40MB de cache)
        cursor.execute("PRAGMA cache_size=10000")
        # Configurações adicionais de performance
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator:
    """Dependency provider para sessões de banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa o banco de dados criando as tabelas."""
    # Importar todos os modelos aqui para garantir que sejam criados
    from . import models  # noqa
    Base.metadata.create_all(bind=engine)
