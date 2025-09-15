"""Esquemas Pydantic para validação e serialização de dados.

Define os modelos de entrada e saída da API, incluindo
validações e transformações de dados.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field


class SessionStatus(str, Enum):
    """Status possíveis de uma sessão."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class RunStatus(str, Enum):
    """Status possíveis de um run."""
    PENDING = "pending"
    RUNNING = "running"
    CONCLUDED = "concluded"
    FAILED = "failed"
    CANCELED = "canceled"
    INTERRUPTED = "interrupted"


# === Base Models ===

class TimestampMixin(BaseModel):
    """Mixin para campos de timestamp."""
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_timestamps(cls, v, info):
        """Converte timestamps para int se necessário."""
        field_name = info.field_name
        if field_name and field_name.endswith('_ms') and v is not None:
            if isinstance(v, datetime):
                return int(v.timestamp() * 1000)
            elif isinstance(v, (int, float)):
                return int(v)
        return v


# === Tag Schemas ===

class TagBase(BaseModel):
    """Schema base para tags."""
    name: str = Field(..., min_length=1, max_length=50, description="Nome da tag")
    description: Optional[str] = Field(None, max_length=200, description="Descrição da tag")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Cor hex da tag")


class TagCreate(TagBase):
    """Schema para criação de tag."""
    pass


class TagUpdate(BaseModel):
    """Schema para atualização de tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class Tag(TagBase, TimestampMixin):
    """Schema completo de tag."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at_ms: int


# === Profile Schemas ===

class ProfileBase(BaseModel):
    """Schema base para perfis."""
    name: str = Field(..., min_length=1, max_length=100, description="Nome do perfil")
    description: Optional[str] = Field(None, max_length=500, description="Descrição do perfil")
    prefs_json: Optional[str] = Field(None, description="Configurações JSON do perfil")
    is_default: bool = Field(False, description="Se é o perfil padrão")


class ProfileCreate(ProfileBase):
    """Schema para criação de perfil."""
    
    @field_validator('prefs_json')
    @classmethod
    def validate_prefs_json(cls, v):
        """Valida se prefs_json é um JSON válido."""
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("prefs_json deve ser um JSON válido")
        return v


class ProfileUpdate(BaseModel):
    """Schema para atualização de perfil."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    prefs_json: Optional[str] = None
    is_default: Optional[bool] = None
    
    @field_validator('prefs_json')
    @classmethod
    def validate_prefs_json(cls, v):
        """Valida se prefs_json é um JSON válido."""
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("prefs_json deve ser um JSON válido")
        return v


class Profile(ProfileBase, TimestampMixin):
    """Schema completo de perfil."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at_ms: int
    updated_at_ms: int


# === Session Schemas ===

class SessionBase(BaseModel):
    """Schema base para sessões."""
    name: str = Field(..., min_length=1, max_length=200, description="Nome da sessão")
    note: Optional[str] = Field(None, max_length=1000, description="Nota sobre a sessão")


class SessionCreate(SessionBase):
    """Schema para criação de sessão."""
    profile_id: Optional[str] = Field(None, description="ID do perfil a ser aplicado")
    tags: Optional[List[str]] = Field(default_factory=list, description="Lista de nomes de tags")


class SessionUpdate(BaseModel):
    """Schema para atualização de sessão."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    note: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="Lista de nomes de tags")


class SessionSummary(BaseModel):
    """Resumo de métricas de uma sessão."""
    total_samples: int = Field(..., description="Total de amostras")
    total_runs: int = Field(..., description="Total de runs")
    duration_ms: Optional[int] = Field(None, description="Duração total em ms")
    metric_groups: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Estatísticas por grupo de métrica")


class Session(SessionBase, TimestampMixin):
    """Schema completo de sessão."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: SessionStatus
    started_at_ms: Optional[int] = None
    ended_at_ms: Optional[int] = None
    profile_id: Optional[str] = None
    created_at_ms: int
    updated_at_ms: int
    
    # Campos computados
    tags: List[str] = Field(default_factory=list, description="Tags da sessão")
    
    @computed_field
    @property
    def duration_ms(self) -> Optional[int]:
        """Calcula duração da sessão."""
        if self.started_at_ms and self.ended_at_ms:
            return self.ended_at_ms - self.started_at_ms
        return None


class SessionWithSummary(Session):
    """Sessão com resumo de métricas."""
    summary: Optional[SessionSummary] = None


# === Run Schemas ===

class RunBase(BaseModel):
    """Schema base para runs."""
    note: Optional[str] = Field(None, max_length=1000, description="Nota sobre o run")


class RunCreate(RunBase):
    """Schema para criação de run (via eventos)."""
    tags: Optional[List[str]] = Field(default_factory=list, description="Lista de nomes de tags")


class RunUpdate(BaseModel):
    """Schema para atualização de run."""
    status: Optional[RunStatus] = None
    note: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="Lista de nomes de tags")


class Run(RunBase, TimestampMixin):
    """Schema completo de run."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    session_id: str
    status: RunStatus
    start_ms: int
    end_ms: Optional[int] = None
    duration_ms: Optional[int] = None
    
    # Campos computados
    tags: List[str] = Field(default_factory=list, description="Tags do run")


# === Sample Schemas ===

class MetricSample(BaseModel):
    """Schema para uma amostra de métrica."""
    metric_group: str = Field(..., min_length=1, max_length=50, description="Grupo da métrica (ex: 'gpu', 'cpu')")
    metric_name: str = Field(..., min_length=1, max_length=50, description="Nome da métrica (ex: 'util%', 'mem.used')")
    value: float = Field(..., description="Valor da métrica")
    device_index: Optional[int] = Field(None, ge=0, description="Índice do dispositivo (para métricas por dispositivo)")


class SampleBatch(BaseModel):
    """Schema para lote de amostras."""
    session_id: str = Field(..., description="ID da sessão")
    ts_ms: int = Field(..., description="Timestamp em milissegundos")
    metrics: List[MetricSample] = Field(..., min_items=1, description="Lista de métricas")
    
    @field_validator('ts_ms')
    @classmethod
    def validate_timestamp(cls, v):
        """Valida se timestamp não está muito no futuro."""
        current_ms = int(datetime.now().timestamp() * 1000)
        max_future_ms = 5 * 60 * 1000  # 5 minutos
        
        if v > current_ms + max_future_ms:
            raise ValueError(f"Timestamp muito no futuro: {v}")
        
        return v


class Sample(TimestampMixin):
    """Schema completo de amostra."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: str
    run_id: Optional[str] = None
    ts_ms: int
    metric_group: str
    metric_name: str
    value: float
    device_index: Optional[int] = None


# === Event Schemas ===

class EventCreate(BaseModel):
    """Schema para criação de evento."""
    session_id: str = Field(..., description="ID da sessão")
    ts_ms: int = Field(..., description="Timestamp em milissegundos")
    event_type: str = Field(..., min_length=1, max_length=50, description="Tipo do evento")
    run_id: Optional[str] = Field(None, description="ID do run (se aplicável)")
    status: Optional[str] = Field(None, max_length=50, description="Status associado")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais")
    
    @field_validator('ts_ms')
    @classmethod
    def validate_timestamp(cls, v):
        """Valida se timestamp não está muito no futuro."""
        current_ms = int(datetime.now().timestamp() * 1000)
        max_future_ms = 5 * 60 * 1000  # 5 minutos
        
        if v > current_ms + max_future_ms:
            raise ValueError(f"Timestamp muito no futuro: {v}")
        
        return v


class Event(TimestampMixin):
    """Schema completo de evento."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: str
    ts_ms: int
    event_type: str
    run_id: Optional[str] = None
    status: Optional[str] = None
    meta_json: Optional[str] = None
    
    @computed_field
    @property
    def meta(self) -> Optional[Dict[str, Any]]:
        """Parse JSON metadata."""
        if self.meta_json:
            try:
                return json.loads(self.meta_json)
            except json.JSONDecodeError:
                return None
        return None


# === Query Schemas ===

class SessionQuery(BaseModel):
    """Schema para consulta de sessões."""
    status: Optional[SessionStatus] = None
    tag: Optional[str] = None
    profile_id: Optional[str] = None
    from_ms: Optional[int] = Field(None, description="Timestamp inicial")
    to_ms: Optional[int] = Field(None, description="Timestamp final")
    q: Optional[str] = Field(None, max_length=100, description="Busca textual")
    limit: int = Field(50, ge=1, le=500, description="Limite de resultados")
    offset: int = Field(0, ge=0, description="Offset para paginação")


class SampleQuery(BaseModel):
    """Schema para consulta de amostras."""
    from_ms: Optional[int] = Field(None, description="Timestamp inicial")
    to_ms: Optional[int] = Field(None, description="Timestamp final")
    metric_group: Optional[str] = Field(None, max_length=50)
    metric_name: Optional[str] = Field(None, max_length=50)
    device_index: Optional[int] = Field(None, ge=0)
    run_id: Optional[str] = None
    downsample: Optional[Literal["avg", "min", "max"]] = Field(None, description="Tipo de agregação")
    bucket_ms: int = Field(1000, ge=100, le=3600000, description="Tamanho do bucket em ms")
    limit: int = Field(50000, ge=1, le=100000, description="Limite de resultados")


# === Response Schemas ===

class HealthResponse(BaseModel):
    """Schema para resposta de health check."""
    status: Literal["ok", "degraded", "error"]
    service: str
    version: str
    timestamp: int
    database: Dict[str, Any]
    environment: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Schema padrão para respostas de erro."""
    error: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem descritiva")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")


class SuccessResponse(BaseModel):
    """Schema padrão para respostas de sucesso."""
    message: str = Field(..., description="Mensagem de sucesso")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais")


# === Preferences Schema ===

class PreferencesBase(BaseModel):
    """Schema base para preferências."""
    interval_ms_default: int = Field(1000, ge=100, le=60000, description="Intervalo padrão em ms")
    metrics_default_json: Optional[str] = Field(None, description="Métricas padrão (JSON)")
    windows_default_json: Optional[str] = Field(None, description="Janelas padrão (JSON)")
    thresholds_json: Optional[str] = Field(None, description="Thresholds (JSON)")
    retention_policy_json: Optional[str] = Field(None, description="Política de retenção (JSON)")


class PreferencesUpdate(PreferencesBase):
    """Schema para atualização de preferências."""
    interval_ms_default: Optional[int] = Field(None, ge=100, le=60000)


class Preferences(PreferencesBase, TimestampMixin):
    """Schema completo de preferências."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at_ms: int
    updated_at_ms: int
