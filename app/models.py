"""Modelos SQLAlchemy para o Backend de Observabilidade ComfyUI.

Implementa as tabelas conforme especificado no DSD:
- sessions: janelas de observabilidade 
- runs: execuções de pipelines dentro de sessões
- samples: amostras de métricas (séries temporais)
- events: eventos de marco (início/fim de runs, etc)
- tags: rótulos para organização
- profiles: perfis de configuração
- preferences: preferências globais do sistema
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Text, REAL, ForeignKey, 
    CheckConstraint, Index, UniqueConstraint, Boolean
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .db import Base


def generate_uuid() -> str:
    """Gera UUID4 como string para IDs."""
    return str(uuid.uuid4())


def current_timestamp_ms() -> int:
    """Retorna timestamp atual em milissegundos (epoch)."""
    return int(datetime.now().timestamp() * 1000)


class Session(Base):
    """Sessão de observabilidade - janela de tempo contínua de monitoramento.
    
    Uma sessão representa um período de observabilidade ativo onde amostras
    e eventos são coletados. Apenas uma sessão pode estar ativa por vez.
    """
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, 
        nullable=False,
        default="inactive"
    )
    started_at_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ended_at_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    profile_id: Mapped[Optional[str]] = mapped_column(
        String, 
        ForeignKey("profiles.id"), 
        nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    updated_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    
    # Relationships
    runs: Mapped[List["Run"]] = relationship("Run", back_populates="session", cascade="all, delete-orphan")
    samples: Mapped[List["Sample"]] = relationship("Sample", back_populates="session", cascade="all, delete-orphan")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="session", cascade="all, delete-orphan")
    profile: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="sessions")
    session_tags: Mapped[List["SessionTag"]] = relationship("SessionTag", back_populates="session", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('inactive', 'active', 'paused', 'ended')",
            name="ck_session_status"
        ),
        # Índice parcial para garantir apenas uma sessão ativa
        Index(
            "ux_one_active_session",
            "status",
            unique=True,
            postgresql_where=Column("status") == "active",
            sqlite_where=Column("status") == "active"
        ),
        Index("ix_sessions_status", "status"),
        Index("ix_sessions_created_at", "created_at_ms"),
        Index("ix_sessions_profile", "profile_id"),
    )


class Run(Base):
    """Execução de pipeline dentro de uma sessão.
    
    Representa uma execução específica de um pipeline ComfyUI,
    com timestamps de início/fim e status de execução.
    """
    __tablename__ = "runs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="runs")
    samples: Mapped[List["Sample"]] = relationship("Sample", back_populates="run", cascade="all, delete-orphan")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="run", cascade="all, delete-orphan")
    run_tags: Mapped[List["RunTag"]] = relationship("RunTag", back_populates="run", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'concluded', 'failed', 'canceled', 'interrupted')",
            name="ck_run_status"
        ),
        Index("ix_runs_session_time", "session_id", "start_ms"),
        Index("ix_runs_status", "status"),
        Index("ix_runs_session", "session_id"),
    )


class Sample(Base):
    """Amostra de métrica (ponto de série temporal).
    
    Representa um ponto de dados de uma métrica específica em um momento
    no tempo, associado a uma sessão e opcionalmente a um run.
    """
    __tablename__ = "samples"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("runs.id"), nullable=True)
    ts_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_group: Mapped[str] = mapped_column(String, nullable=False)
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(REAL, nullable=False)
    device_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="samples")
    run: Mapped[Optional["Run"]] = relationship("Run", back_populates="samples")
    
    # Constraints
    __table_args__ = (
        Index("ix_samples_session_ts", "session_id", "ts_ms"),
        Index("ix_samples_run_ts", "run_id", "ts_ms"),
        Index("ix_samples_mgroup_name", "metric_group", "metric_name"),
        Index("ix_samples_ts", "ts_ms"),
        Index("ix_samples_device", "device_index"),
    )


class Event(Base):
    """Evento de marco (início/fim de run, pausas, etc).
    
    Registra eventos importantes durante uma sessão, como início/fim
    de runs, pausas, retomadas, etc.
    """
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), nullable=False)
    ts_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("runs.id"), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    meta_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="events")
    run: Mapped[Optional["Run"]] = relationship("Run", back_populates="events")
    
    # Constraints
    __table_args__ = (
        Index("ix_events_session_ts", "session_id", "ts_ms"),
        Index("ix_events_type", "event_type"),
        Index("ix_events_run", "run_id"),
        Index("ix_events_ts", "ts_ms"),
    )


class Tag(Base):
    """Rótulo para organização e categorização.
    
    Tags podem ser aplicadas a sessões e runs para facilitar
    organização e filtragem.
    """
    __tablename__ = "tags"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color #RRGGBB
    created_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    
    # Relationships
    session_tags: Mapped[List["SessionTag"]] = relationship("SessionTag", back_populates="tag", cascade="all, delete-orphan")
    run_tags: Mapped[List["RunTag"]] = relationship("RunTag", back_populates="tag", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        Index("ix_tags_name", "name"),
    )


class SessionTag(Base):
    """Associação entre sessões e tags."""
    __tablename__ = "session_tags"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), nullable=False)
    tag_id: Mapped[str] = mapped_column(String, ForeignKey("tags.id"), nullable=False)
    created_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="session_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="session_tags")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("session_id", "tag_id", name="ux_session_tag"),
        Index("ix_session_tags_session", "session_id"),
        Index("ix_session_tags_tag", "tag_id"),
    )


class RunTag(Base):
    """Associação entre runs e tags."""
    __tablename__ = "run_tags"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.id"), nullable=False)
    tag_id: Mapped[str] = mapped_column(String, ForeignKey("tags.id"), nullable=False)
    created_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    
    # Relationships
    run: Mapped["Run"] = relationship("Run", back_populates="run_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="run_tags")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("run_id", "tag_id", name="ux_run_tag"),
        Index("ix_run_tags_run", "run_id"),
        Index("ix_run_tags_tag", "tag_id"),
    )


class Profile(Base):
    """Perfil de configuração para sessões.
    
    Define configurações padrão que podem ser aplicadas
    a sessões (intervalos, métricas, etc).
    """
    __tablename__ = "profiles"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prefs_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    updated_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    
    # Relationships
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="profile")
    
    # Constraints
    __table_args__ = (
        Index("ix_profiles_name", "name"),
        Index("ix_profiles_default", "is_default"),
    )


class Preferences(Base):
    """Preferências globais do sistema (singleton).
    
    Armazena configurações globais como intervalos padrão,
    métricas padrão, políticas de retenção, etc.
    """
    __tablename__ = "preferences"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)  # Singleton
    interval_ms_default: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    metrics_default_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    windows_default_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thresholds_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retention_policy_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    updated_at_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=current_timestamp_ms)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_preferences_singleton"),
    )
