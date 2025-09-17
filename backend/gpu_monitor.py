#!/usr/bin/env python3
"""
Script para monitoramento de GPU usando nvidia-smi
Coleta dados de utilização, memória, temperatura e potência da GPU
"""

import subprocess
import json
import sqlite3
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GPUMonitor:
    def __init__(self, db_path: str = "gpu_monitor.db"):
        self.db_path = db_path
        self.current_session_id = None
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela para dados da GPU (versão original)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gpu_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    device_index INTEGER,
                    util_percent REAL,
                    mem_used_mb REAL,
                    mem_total_mb REAL,
                    temp_celsius REAL,
                    power_watts REAL
                )
            ''')
            
            # Criar tabela para sessões de medição
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS measurement_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Verificar se a coluna session_id já existe
            cursor.execute("PRAGMA table_info(gpu_data)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'session_id' not in columns:
                logger.info("Adicionando coluna session_id à tabela gpu_data...")
                cursor.execute('ALTER TABLE gpu_data ADD COLUMN session_id INTEGER')
                logger.info("Coluna session_id adicionada com sucesso")
            
            # Criar índices para melhorar performance das consultas
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON gpu_data(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_device_timestamp 
                ON gpu_data(device_index, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON gpu_data(session_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_active 
                ON measurement_sessions(is_active)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Banco de dados inicializado: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def get_gpu_data(self) -> List[Dict]:
        """
        Coleta dados da GPU usando nvidia-smi
        Retorna lista de dicionários com dados de cada GPU
        """
        try:
            # Comando nvidia-smi para obter dados em formato CSV
            cmd = [
                'nvidia-smi',
                '--query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw',
                '--format=csv,noheader,nounits'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            gpu_data_list = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [part.strip() for part in line.split(',')]
                    
                    # Tratar valores que podem ser "N/A" ou vazios
                    def safe_float(value, default=0.0):
                        try:
                            return float(value) if value != 'N/A' else default
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_int(value, default=0):
                        try:
                            return int(value) if value != 'N/A' else default
                        except (ValueError, TypeError):
                            return default
                    
                    gpu_data = {
                        'device_index': safe_int(parts[0]),
                        'util_percent': safe_float(parts[1]),
                        'mem_used_mb': safe_float(parts[2]),
                        'mem_total_mb': safe_float(parts[3]),
                        'temp_celsius': safe_float(parts[4]),
                        'power_watts': safe_float(parts[5])
                    }
                    
                    gpu_data_list.append(gpu_data)
            
            return gpu_data_list
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar nvidia-smi: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro ao coletar dados da GPU: {e}")
            return []
    
    def save_gpu_data(self, gpu_data_list: List[Dict]):
        """Salva dados da GPU no banco de dados"""
        if not gpu_data_list:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for gpu_data in gpu_data_list:
                cursor.execute('''
                    INSERT INTO gpu_data 
                    (device_index, util_percent, mem_used_mb, mem_total_mb, temp_celsius, power_watts, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    gpu_data['device_index'],
                    gpu_data['util_percent'],
                    gpu_data['mem_used_mb'],
                    gpu_data['mem_total_mb'],
                    gpu_data['temp_celsius'],
                    gpu_data['power_watts'],
                    self.current_session_id
                ))
            
            conn.commit()
            conn.close()
            
            session_info = f" (sessão {self.current_session_id})" if self.current_session_id else ""
            logger.info(f"Salvos dados de {len(gpu_data_list)} GPU(s){session_info}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados no banco: {e}")
    
    def get_latest_data(self, limit: int = 100) -> List[Dict]:
        """Recupera os dados mais recentes do banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM gpu_data 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Converter para lista de dicionários
            data = []
            for row in rows:
                data.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'device_index': row['device_index'],
                    'util_percent': row['util_percent'],
                    'mem_used_mb': row['mem_used_mb'],
                    'mem_total_mb': row['mem_total_mb'],
                    'temp_celsius': row['temp_celsius'],
                    'power_watts': row['power_watts']
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao recuperar dados do banco: {e}")
            return []
    
    def get_data_by_timerange(self, start_time: str, end_time: str, device_index: Optional[int] = None) -> List[Dict]:
        """Recupera dados por intervalo de tempo"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if device_index is not None:
                cursor.execute('''
                    SELECT * FROM gpu_data 
                    WHERE timestamp BETWEEN ? AND ? 
                    AND device_index = ?
                    ORDER BY timestamp ASC
                ''', (start_time, end_time, device_index))
            else:
                cursor.execute('''
                    SELECT * FROM gpu_data 
                    WHERE timestamp BETWEEN ? AND ? 
                    ORDER BY timestamp ASC
                ''', (start_time, end_time))
            
            rows = cursor.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'device_index': row['device_index'],
                    'util_percent': row['util_percent'],
                    'mem_used_mb': row['mem_used_mb'],
                    'mem_total_mb': row['mem_total_mb'],
                    'temp_celsius': row['temp_celsius'],
                    'power_watts': row['power_watts']
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao recuperar dados por intervalo: {e}")
            return []
    
    async def monitor_continuous(self, interval: int = 5):
        """Monitora continuamente a GPU com intervalo especificado (em segundos)"""
        logger.info(f"Iniciando monitoramento contínuo (intervalo: {interval}s)")
        
        while True:
            try:
                gpu_data_list = self.get_gpu_data()
                if gpu_data_list:
                    self.save_gpu_data(gpu_data_list)
                    
                    # Log resumido
                    for gpu_data in gpu_data_list:
                        logger.info(
                            f"GPU {gpu_data['device_index']}: "
                            f"Util: {gpu_data['util_percent']}%, "
                            f"Mem: {gpu_data['mem_used_mb']:.0f}/{gpu_data['mem_total_mb']:.0f}MB, "
                            f"Temp: {gpu_data['temp_celsius']}°C, "
                            f"Power: {gpu_data['power_watts']}W"
                        )
                else:
                    logger.warning("Nenhum dado da GPU coletado")
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro no monitoramento contínuo: {e}")
                await asyncio.sleep(interval)
    
    # Métodos para gerenciar sessões de medição
    def create_session(self, name: str, description: str = "") -> int:
        """Cria uma nova sessão de medição"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO measurement_sessions (name, description)
                VALUES (?, ?)
            ''', (name, description))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Nova sessão criada: {session_id} - {name}")
            return session_id
            
        except Exception as e:
            logger.error(f"Erro ao criar sessão: {e}")
            raise
    
    def start_session(self, session_id: int):
        """Inicia uma sessão de medição (define como sessão ativa)"""
        try:
            # Finaliza qualquer sessão ativa anterior
            self.stop_current_session()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verifica se a sessão existe
            cursor.execute('SELECT name FROM measurement_sessions WHERE id = ?', (session_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Sessão {session_id} não encontrada")
            
            # Define como sessão ativa
            cursor.execute('''
                UPDATE measurement_sessions 
                SET is_active = 1, start_time = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
            self.current_session_id = session_id
            logger.info(f"Sessão iniciada: {session_id} - {result[0]}")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar sessão: {e}")
            raise
    
    def stop_current_session(self):
        """Para a sessão atual (se houver)"""
        if not self.current_session_id:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE measurement_sessions 
                SET is_active = 0, end_time = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (self.current_session_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Sessão finalizada: {self.current_session_id}")
            self.current_session_id = None
            
        except Exception as e:
            logger.error(f"Erro ao finalizar sessão: {e}")
    
    def get_sessions(self, limit: int = 50) -> List[Dict]:
        """Recupera lista de sessões"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.*, 
                       COUNT(g.id) as measurement_count,
                       MIN(g.timestamp) as first_measurement,
                       MAX(g.timestamp) as last_measurement
                FROM measurement_sessions s
                LEFT JOIN gpu_data g ON s.id = g.session_id
                GROUP BY s.id
                ORDER BY s.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                sessions.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'start_time': row['start_time'],
                    'end_time': row['end_time'],
                    'is_active': bool(row['is_active']),
                    'created_at': row['created_at'],
                    'measurement_count': row['measurement_count'],
                    'first_measurement': row['first_measurement'],
                    'last_measurement': row['last_measurement']
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Erro ao recuperar sessões: {e}")
            return []
    
    def get_session_data(self, session_id: int) -> List[Dict]:
        """Recupera dados de uma sessão específica"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM gpu_data 
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'device_index': row['device_index'],
                    'util_percent': row['util_percent'],
                    'mem_used_mb': row['mem_used_mb'],
                    'mem_total_mb': row['mem_total_mb'],
                    'temp_celsius': row['temp_celsius'],
                    'power_watts': row['power_watts'],
                    'session_id': row['session_id']
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao recuperar dados da sessão: {e}")
            return []
    
    def delete_session(self, session_id: int):
        """Deleta uma sessão e todos os seus dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remove dados da GPU associados à sessão
            cursor.execute('DELETE FROM gpu_data WHERE session_id = ?', (session_id,))
            
            # Remove a sessão
            cursor.execute('DELETE FROM measurement_sessions WHERE id = ?', (session_id,))
            
            conn.commit()
            conn.close()
            
            # Se era a sessão atual, limpa a referência
            if self.current_session_id == session_id:
                self.current_session_id = None
            
            logger.info(f"Sessão deletada: {session_id}")
            
        except Exception as e:
            logger.error(f"Erro ao deletar sessão: {e}")
            raise

def main():
    """Função principal para teste do monitor"""
    monitor = GPUMonitor()
    
    # Teste de coleta única
    print("=== Teste de coleta única ===")
    gpu_data_list = monitor.get_gpu_data()
    if gpu_data_list:
        monitor.save_gpu_data(gpu_data_list)
        print(f"Coletados dados de {len(gpu_data_list)} GPU(s)")
        for i, data in enumerate(gpu_data_list):
            print(f"GPU {i}: {data}")
    else:
        print("Nenhum dado coletado. Verifique se nvidia-smi está disponível.")
    
    # Teste de recuperação de dados
    print("\n=== Últimos dados salvos ===")
    latest_data = monitor.get_latest_data(5)
    for data in latest_data:
        print(f"{data['timestamp']}: GPU {data['device_index']} - {data['util_percent']}%")

if __name__ == "__main__":
    main()
