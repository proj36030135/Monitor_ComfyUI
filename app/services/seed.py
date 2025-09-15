"""Serviço para inicialização de dados padrão (seeds).

Cria dados iniciais necessários para o funcionamento do sistema,
incluindo preferências padrão com política de retenção.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select

from ..models import Preferences


def current_timestamp_ms() -> int:
    """Retorna timestamp atual em milissegundos."""
    return int(datetime.now().timestamp() * 1000)


def create_default_preferences(db: DBSession) -> None:
    """Cria as preferências padrão do sistema.
    
    Configura política de retenção, intervalos padrão,
    métricas padrão e outros parâmetros conforme DSD.
    
    Args:
        db: Sessão do banco de dados
    """
    # Verificar se já existem preferências
    existing = db.execute(select(Preferences).where(Preferences.id == 1)).scalar_one_or_none()
    if existing:
        return  # Já existe, não criar novamente
    
    current_ms = current_timestamp_ms()
    
    # Política de retenção padrão conforme DSD
    retention_policy = {
        "max_samples_per_session": 1000000,  # 1M amostras por sessão
        "max_duration_ms": 28800000,  # 8 horas (8 * 60 * 60 * 1000)
        "on_limit": "segment"  # "segment" | "end"
    }
    
    # Métricas padrão para coleta
    metrics_default = {
        "gpu": [
            "util%",
            "mem.used",
            "mem.total",
            "mem.util%",
            "temp.gpu",
            "power.draw"
        ],
        "cpu": [
            "util%",
            "temp",
            "freq"
        ],
        "memory": [
            "used",
            "available",
            "util%"
        ],
        "process": [
            "cpu%",
            "memory_mb",
            "gpu_memory_mb"
        ]
    }
    
    # Janelas de tempo padrão para consultas
    windows_default = {
        "quick": [
            {"name": "1min", "duration_ms": 60000, "bucket_ms": 1000},
            {"name": "5min", "duration_ms": 300000, "bucket_ms": 5000},
            {"name": "15min", "duration_ms": 900000, "bucket_ms": 15000}
        ],
        "extended": [
            {"name": "1h", "duration_ms": 3600000, "bucket_ms": 60000},
            {"name": "4h", "duration_ms": 14400000, "bucket_ms": 240000},
            {"name": "8h", "duration_ms": 28800000, "bucket_ms": 480000}
        ]
    }
    
    # Thresholds padrão para alertas/indicadores
    thresholds = {
        "gpu": {
            "util%": {"warning": 80, "critical": 95},
            "mem.util%": {"warning": 85, "critical": 98},
            "temp.gpu": {"warning": 80, "critical": 90}
        },
        "cpu": {
            "util%": {"warning": 80, "critical": 95},
            "temp": {"warning": 70, "critical": 85}
        },
        "memory": {
            "util%": {"warning": 85, "critical": 95}
        },
        "session": {
            "disconnected_threshold_ms": 5000,  # 5s sem dados = DISCONNECTED
            "degraded_latency_ms": 2000,  # Latência > 2s = DEGRADED
            "degraded_duration_ms": 30000  # Por mais de 30s
        }
    }
    
    # Criar registro de preferências
    preferences = Preferences(
        id=1,  # Singleton
        interval_ms_default=1000,  # 1 segundo
        metrics_default_json=json.dumps(metrics_default, indent=2),
        windows_default_json=json.dumps(windows_default, indent=2),
        thresholds_json=json.dumps(thresholds, indent=2),
        retention_policy_json=json.dumps(retention_policy, indent=2),
        created_at_ms=current_ms,
        updated_at_ms=current_ms
    )
    
    db.add(preferences)
    db.commit()
    
    print("✅ Preferências padrão criadas com sucesso")


def init_seeds(db: DBSession) -> None:
    """Inicializa todos os dados padrão necessários.
    
    Args:
        db: Sessão do banco de dados
    """
    print("🌱 Inicializando dados padrão...")
    
    try:
        # Criar preferências padrão
        create_default_preferences(db)
        
        print("✅ Todos os dados padrão foram inicializados")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar dados padrão: {e}")
        db.rollback()
        raise
