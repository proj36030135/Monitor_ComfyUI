#!/usr/bin/env python3
"""
Cliente de teste para o sistema GPU Monitor
Demonstra como usar a API REST e WebSocket
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime

class GPUMonitorClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    
    def test_health(self):
        """Testa o endpoint de health check"""
        print("=== Testando Health Check ===")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {data['status']}")
                print(f"📊 GPUs detectadas: {data['gpu_count']}")
                print(f"🔌 Conexões WebSocket: {data['websocket_connections']}")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
    
    def test_current_data(self):
        """Testa o endpoint de dados atuais"""
        print("\n=== Testando Dados Atuais ===")
        try:
            response = requests.get(f"{self.base_url}/api/gpu/current")
            if response.status_code == 200:
                data = response.json()
                print(f"📈 Total de registros: {data['count']}")
                
                for gpu_data in data['data'][:3]:  # Mostra apenas os 3 primeiros
                    print(f"GPU {gpu_data['device_index']}:")
                    print(f"  ⚡ Utilização: {gpu_data['util_percent']}%")
                    print(f"  💾 Memória: {gpu_data['mem_used_mb']:.0f}/{gpu_data['mem_total_mb']:.0f}MB")
                    print(f"  🌡️  Temperatura: {gpu_data['temp_celsius']}°C")
                    print(f"  🔋 Potência: {gpu_data['power_watts']}W")
                    print(f"  🕐 Timestamp: {gpu_data['timestamp']}")
                    print()
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
    
    def test_history(self):
        """Testa o endpoint de histórico"""
        print("=== Testando Histórico (última hora) ===")
        try:
            params = {
                'hours': 1,
                'limit': 10
            }
            response = requests.get(f"{self.base_url}/api/gpu/history", params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Registros encontrados: {data['count']}")
                
                if data['data']:
                    print("Últimos registros:")
                    for gpu_data in data['data'][:5]:
                        print(f"  {gpu_data['timestamp']} - GPU {gpu_data['device_index']}: {gpu_data['util_percent']}%")
                else:
                    print("Nenhum dado histórico encontrado")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
    
    def test_stats(self):
        """Testa o endpoint de estatísticas"""
        print("\n=== Testando Estatísticas ===")
        try:
            response = requests.get(f"{self.base_url}/api/gpu/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"📈 Período: {data.get('period_hours', 'N/A')} horas")
                print(f"📊 Total de amostras: {data.get('total_samples', 'N/A')}")
                
                for device in data.get('devices', []):
                    print(f"\nGPU {device['device_index']}:")
                    print(f"  📊 Amostras: {device['sample_count']}")
                    
                    util = device['utilization']
                    print(f"  ⚡ Utilização: {util['avg']:.1f}% (min: {util['min']:.1f}%, max: {util['max']:.1f}%)")
                    
                    temp = device['temperature_celsius']
                    print(f"  🌡️  Temperatura: {temp['avg']:.1f}°C (min: {temp['min']:.1f}°C, max: {temp['max']:.1f}°C)")
                    
                    power = device['power_watts']
                    print(f"  🔋 Potência: {power['avg']:.1f}W (min: {power['min']:.1f}W, max: {power['max']:.1f}W)")
            else:
                print(f"❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
    
    async def test_websocket(self, duration=30):
        """Testa a conexão WebSocket"""
        print(f"\n=== Testando WebSocket por {duration} segundos ===")
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("🔌 Conectado ao WebSocket")
                
                # Envia uma mensagem de teste
                await websocket.send("Hello from test client!")
                
                start_time = datetime.now()
                message_count = 0
                
                while (datetime.now() - start_time).seconds < duration:
                    try:
                        # Aguarda mensagem com timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        message_count += 1
                        
                        if data.get('type') == 'gpu_data':
                            gpu_list = data.get('data', [])
                            if gpu_list:
                                gpu = gpu_list[0]  # Primeira GPU
                                print(f"📡 [{data['timestamp'][:19]}] GPU {gpu['device_index']}: "
                                      f"{gpu['util_percent']}% | {gpu['temp_celsius']}°C | {gpu['power_watts']}W")
                        elif data.get('type') == 'initial_data':
                            print("📨 Dados iniciais recebidos")
                        else:
                            print(f"📨 Mensagem: {message[:100]}...")
                        
                    except asyncio.TimeoutError:
                        print("⏰ Timeout aguardando mensagem")
                    except json.JSONDecodeError:
                        print(f"❌ Erro ao decodificar JSON: {message[:100]}...")
                
                print(f"📊 Total de mensagens recebidas: {message_count}")
                
        except Exception as e:
            print(f"❌ Erro WebSocket: {e}")

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do GPU Monitor Client\n")
    
    client = GPUMonitorClient()
    
    # Testes síncronos
    client.test_health()
    client.test_current_data()
    client.test_history()
    client.test_stats()
    
    # Pergunta se quer testar WebSocket
    print("\n" + "="*50)
    response = input("Deseja testar o WebSocket? (s/N): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        duration = input("Por quantos segundos? (padrão: 30): ").strip()
        try:
            duration = int(duration) if duration else 30
        except ValueError:
            duration = 30
        
        # Teste assíncrono
        asyncio.run(client.test_websocket(duration))
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    main()
