"""Backend de Observabilidade ComfyUI - Aplicação principal FastAPI."""

import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .db import engine, init_db, get_db
from .routers import sessions
from .services.seed import init_seeds


# Lifespan manager para inicialização/finalização da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    print("Iniciando Backend de Observabilidade ComfyUI...")
    
    # Inicializar banco de dados
    init_db()
    print("Banco de dados inicializado")
    
    # Inicializar dados padrão (seeds)
    db = next(get_db())
    try:
        init_seeds(db)
    finally:
        db.close()
    
    yield
    
    # Shutdown
    print("Encerrando aplicação...")


# Configuração da aplicação FastAPI
app = FastAPI(
    title="Backend de Observabilidade ComfyUI",
    description="Backend local-first para observabilidade de runs/gerações feitas com pipelines do ComfyUI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configuração CORS para desenvolvimento local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",  # Para frontend React/Next.js
        "http://localhost:8000",  # Para desenvolvimento
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(sessions.router)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Endpoint de health check do serviço."""
    start_time = time.time()
    
    # Status da aplicação
    status = {
        "status": "ok",
        "service": "Backend de Observabilidade ComfyUI",
        "version": "0.1.0",
        "timestamp": int(time.time() * 1000),  # epoch ms conforme DSD
    }
    
    # Testar conexão com banco de dados
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            db_latency_ms = round((time.time() - start_time) * 1000, 2)
            status["database"] = {
                "status": "ok",
                "latency_ms": db_latency_ms,
                "url": str(engine.url).replace(str(engine.url.password), "***") if engine.url.password else str(engine.url),
            }
    except Exception as e:
        status["database"] = {
            "status": "error",
            "error": str(e),
        }
        status["status"] = "degraded"
    
    # Informações do ambiente
    status["environment"] = {
        "python_version": os.sys.version,
        "working_directory": os.getcwd(),
        "host": os.getenv("APP_HOST", "127.0.0.1"),
        "port": os.getenv("APP_PORT", "8080"),
    }
    
    return status


@app.get("/")
async def root():
    """Endpoint raiz com informações básicas."""
    return {
        "message": "Backend de Observabilidade ComfyUI",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
