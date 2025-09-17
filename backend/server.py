#!/usr/bin/env python3
"""
Backend API para monitoramento de GPU
Servidor FastAPI com WebSocket para streaming de dados
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gpu_monitor import GPUMonitor

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Modelos Pydantic para API
class GPUData(BaseModel):
    id: int
    timestamp: str
    device_index: int
    util_percent: float
    mem_used_mb: float
    mem_total_mb: float
    temp_celsius: float
    power_watts: float

class GPUDataResponse(BaseModel):
    data: List[GPUData]
    count: int

class SessionCreate(BaseModel):
    name: str
    description: str = ""

class SessionResponse(BaseModel):
    id: int
    name: str
    description: str
    start_time: Optional[str]
    end_time: Optional[str]
    is_active: bool
    created_at: str
    measurement_count: int
    first_measurement: Optional[str]
    last_measurement: Optional[str]

class SessionsResponse(BaseModel):
    sessions: List[SessionResponse]
    count: int

class ConnectionManager:
    """Gerencia conexões WebSocket ativas"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Nova conexão WebSocket: {len(self.active_connections)} ativa(s)")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Conexão WebSocket fechada: {len(self.active_connections)} ativa(s)")
    
    async def broadcast(self, message: str):
        """Envia mensagem para todas as conexões ativas"""
        if not self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Erro ao enviar para conexão: {e}")
                disconnected.add(connection)
        
        # Remove conexões que falharam
        for connection in disconnected:
            self.active_connections.discard(connection)

# Instâncias globais
monitor = GPUMonitor()
manager = ConnectionManager()

# Task de monitoramento em background
monitoring_task = None

async def background_monitoring():
    """Task de monitoramento contínuo em background"""
    logger.info("Iniciando monitoramento em background")
    
    while True:
        try:
            # Coleta dados da GPU
            gpu_data_list = monitor.get_gpu_data()
            
            if gpu_data_list:
                # Salva no banco de dados
                monitor.save_gpu_data(gpu_data_list)
                
                # Prepara dados para broadcast
                broadcast_data = {
                    "type": "gpu_data",
                    "timestamp": datetime.now().isoformat(),
                    "data": gpu_data_list
                }
                
                # Envia para todas as conexões WebSocket
                await manager.broadcast(json.dumps(broadcast_data))
                
                logger.debug(f"Dados enviados para {len(manager.active_connections)} conexão(ões)")
            
            # Aguarda 2 segundos antes da próxima coleta
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Erro no monitoramento em background: {e}")
            await asyncio.sleep(5)  # Aguarda mais tempo em caso de erro

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    global monitoring_task
    
    # Startup
    logger.info("Iniciando aplicação...")
    monitoring_task = asyncio.create_task(background_monitoring())
    
    yield
    
    # Shutdown
    logger.info("Finalizando aplicação...")
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            logger.info("Task de monitoramento cancelada")

# Criar aplicação FastAPI
app = FastAPI(
    title="GPU Monitor API",
    description="API para monitoramento de GPU com streaming em tempo real",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "GPU Monitor Backend API",
        "version": "1.0.0",
        "endpoints": {
            "current": "/api/gpu/current",
            "history": "/api/gpu/history",
            "stats": "/api/gpu/stats",
            "health": "/api/health",
            "websocket": "/ws",
            "sessions": {
                "list": "/api/sessions",
                "create": "POST /api/sessions",
                "start": "POST /api/sessions/{id}/start",
                "stop": "POST /api/sessions/stop",
                "current": "/api/sessions/current",
                "data": "/api/sessions/{id}/data",
                "delete": "DELETE /api/sessions/{id}"
            }
        },
        "frontend": "Acesse o frontend em viewer/index.html"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para streaming de dados em tempo real"""
    await manager.connect(websocket)
    
    try:
        # Envia dados iniciais
        latest_data = monitor.get_latest_data(1)
        if latest_data:
            initial_message = {
                "type": "initial_data",
                "timestamp": datetime.now().isoformat(),
                "data": latest_data
            }
            await websocket.send_text(json.dumps(initial_message))
        
        # Mantém conexão viva e escuta por mensagens do cliente
        while True:
            try:
                # Aguarda mensagem do cliente (para manter conexão viva)
                data = await websocket.receive_text()
                logger.debug(f"Mensagem recebida do cliente: {data}")
                
                # Processa comandos do cliente se necessário
                try:
                    client_msg = json.loads(data)
                    if client_msg.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
                except json.JSONDecodeError:
                    pass  # Ignora mensagens que não são JSON
                
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"Erro na conexão WebSocket: {e}")
    finally:
        manager.disconnect(websocket)

@app.get("/api/gpu/current", response_model=GPUDataResponse)
async def get_current_gpu_data():
    """Retorna os dados mais recentes de todas as GPUs"""
    try:
        data = monitor.get_latest_data(10)  # Últimas 10 leituras
        
        gpu_data_list = []
        for item in data:
            gpu_data_list.append(GPUData(**item))
        
        return GPUDataResponse(data=gpu_data_list, count=len(gpu_data_list))
        
    except Exception as e:
        logger.error(f"Erro ao obter dados atuais: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/gpu/history", response_model=GPUDataResponse)
async def get_gpu_history(
    hours: int = Query(default=1, ge=1, le=168, description="Horas de histórico (1-168)"),
    device_index: Optional[int] = Query(default=None, ge=0, description="Índice da GPU específica"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Limite de registros")
):
    """Retorna histórico de dados da GPU"""
    try:
        # Calcula intervalo de tempo
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        data = monitor.get_data_by_timerange(
            start_time.isoformat(),
            end_time.isoformat(),
            device_index
        )
        
        # Limita o número de registros
        data = data[:limit]
        
        gpu_data_list = []
        for item in data:
            gpu_data_list.append(GPUData(**item))
        
        return GPUDataResponse(data=gpu_data_list, count=len(gpu_data_list))
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/gpu/stats")
async def get_gpu_stats():
    """Retorna estatísticas resumidas das GPUs"""
    try:
        # Dados das últimas 24 horas
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        data = monitor.get_data_by_timerange(
            start_time.isoformat(),
            end_time.isoformat()
        )
        
        if not data:
            return {"message": "Nenhum dado disponível"}
        
        # Agrupa por device_index
        stats_by_device = {}
        for item in data:
            device_idx = item['device_index']
            if device_idx not in stats_by_device:
                stats_by_device[device_idx] = {
                    'device_index': device_idx,
                    'util_percent': [],
                    'mem_used_mb': [],
                    'temp_celsius': [],
                    'power_watts': [],
                    'count': 0
                }
            
            stats_by_device[device_idx]['util_percent'].append(item['util_percent'])
            stats_by_device[device_idx]['mem_used_mb'].append(item['mem_used_mb'])
            stats_by_device[device_idx]['temp_celsius'].append(item['temp_celsius'])
            stats_by_device[device_idx]['power_watts'].append(item['power_watts'])
            stats_by_device[device_idx]['count'] += 1
        
        # Calcula estatísticas
        result = []
        for device_idx, stats in stats_by_device.items():
            util_values = stats['util_percent']
            mem_values = stats['mem_used_mb']
            temp_values = stats['temp_celsius']
            power_values = stats['power_watts']
            
            device_stats = {
                'device_index': device_idx,
                'sample_count': stats['count'],
                'utilization': {
                    'avg': sum(util_values) / len(util_values),
                    'min': min(util_values),
                    'max': max(util_values)
                },
                'memory_used_mb': {
                    'avg': sum(mem_values) / len(mem_values),
                    'min': min(mem_values),
                    'max': max(mem_values)
                },
                'temperature_celsius': {
                    'avg': sum(temp_values) / len(temp_values),
                    'min': min(temp_values),
                    'max': max(temp_values)
                },
                'power_watts': {
                    'avg': sum(power_values) / len(power_values),
                    'min': min(power_values),
                    'max': max(power_values)
                }
            }
            result.append(device_stats)
        
        return {
            'period_hours': 24,
            'total_samples': len(data),
            'devices': result
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate):
    """Cria uma nova sessão de medição"""
    try:
        session_id = monitor.create_session(session_data.name, session_data.description)
        
        # Recupera a sessão criada para retornar
        sessions = monitor.get_sessions(limit=1)
        created_session = next((s for s in sessions if s['id'] == session_id), None)
        
        if not created_session:
            raise HTTPException(status_code=500, detail="Erro ao criar sessão")
        
        return SessionResponse(**created_session)
        
    except Exception as e:
        logger.error(f"Erro ao criar sessão: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/sessions", response_model=SessionsResponse)
async def get_sessions(limit: int = Query(default=50, ge=1, le=100)):
    """Retorna lista de sessões"""
    try:
        sessions = monitor.get_sessions(limit)
        
        session_responses = []
        for session in sessions:
            session_responses.append(SessionResponse(**session))
        
        return SessionsResponse(sessions=session_responses, count=len(session_responses))
        
    except Exception as e:
        logger.error(f"Erro ao obter sessões: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/sessions/{session_id}/start")
async def start_session(session_id: int):
    """Inicia uma sessão de medição"""
    try:
        monitor.start_session(session_id)
        
        # Notifica clientes WebSocket sobre a mudança de sessão
        broadcast_data = {
            "type": "session_started",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        await manager.broadcast(json.dumps(broadcast_data))
        
        return {"message": f"Sessão {session_id} iniciada", "session_id": session_id}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao iniciar sessão: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/sessions/stop")
async def stop_current_session():
    """Para a sessão atual"""
    try:
        old_session_id = monitor.current_session_id
        monitor.stop_current_session()
        
        # Notifica clientes WebSocket sobre a mudança de sessão
        broadcast_data = {
            "type": "session_stopped",
            "timestamp": datetime.now().isoformat(),
            "session_id": old_session_id
        }
        await manager.broadcast(json.dumps(broadcast_data))
        
        return {"message": "Sessão finalizada", "session_id": old_session_id}
        
    except Exception as e:
        logger.error(f"Erro ao finalizar sessão: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/sessions/{session_id}/data", response_model=GPUDataResponse)
async def get_session_data(session_id: int):
    """Retorna dados de uma sessão específica"""
    try:
        data = monitor.get_session_data(session_id)
        
        gpu_data_list = []
        for item in data:
            gpu_data_list.append(GPUData(**item))
        
        return GPUDataResponse(data=gpu_data_list, count=len(gpu_data_list))
        
    except Exception as e:
        logger.error(f"Erro ao obter dados da sessão: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int):
    """Deleta uma sessão e todos os seus dados"""
    try:
        monitor.delete_session(session_id)
        
        return {"message": f"Sessão {session_id} deletada"}
        
    except Exception as e:
        logger.error(f"Erro ao deletar sessão: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/sessions/current")
async def get_current_session():
    """Retorna informações da sessão atual"""
    try:
        if not monitor.current_session_id:
            return {"message": "Nenhuma sessão ativa", "session_id": None}
        
        sessions = monitor.get_sessions(limit=100)
        current_session = next((s for s in sessions if s['id'] == monitor.current_session_id), None)
        
        if current_session:
            return {"message": "Sessão ativa encontrada", "session": SessionResponse(**current_session)}
        else:
            return {"message": "Sessão ativa não encontrada", "session_id": monitor.current_session_id}
        
    except Exception as e:
        logger.error(f"Erro ao obter sessão atual: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/health")
async def health_check():
    """Endpoint de verificação de saúde"""
    try:
        # Testa coleta de dados
        gpu_data = monitor.get_gpu_data()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "gpu_count": len(gpu_data),
            "websocket_connections": len(manager.active_connections),
            "database": "connected"
        }
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail="Sistema não saudável")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Iniciando servidor GPU Monitor Backend...")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
