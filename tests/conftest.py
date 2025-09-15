"""Configuração de fixtures para testes.

Define fixtures comuns para testes unitários e de integração,
incluindo configuração de banco de dados de teste.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db import Base, get_db
from app.main import app
from app.services.seed import init_seeds


@pytest.fixture(scope="function")
def test_db():
    """Cria banco de dados temporário para testes."""
    # Usar banco em memória para evitar problemas de cleanup no Windows
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=test_engine)
    
    # Criar session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    yield TestingSessionLocal
    
    # Cleanup automático com banco em memória
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db):
    """Cria sessão de banco de dados para testes."""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Cria cliente de teste para API."""
    def override_get_db():
        session = test_db()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        # Inicializar seeds no banco de teste
        db = next(override_get_db())
        try:
            init_seeds(db)
        finally:
            db.close()
        
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_session_data():
    """Dados de exemplo para criação de sessão."""
    return {
        "name": "Sessão de Teste",
        "note": "Sessão criada para testes unitários",
        "tags": ["teste", "unitario"]
    }
