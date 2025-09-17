#!/usr/bin/env python3
"""
Script de inicialização do GPU Monitor
Inicia o backend e abre automaticamente a interface web no navegador
"""

import os
import sys
import time
import webbrowser
import subprocess
import threading
import signal
from pathlib import Path
import requests
from urllib.parse import urljoin

# Configurações
BACKEND_HOST = "localhost"
BACKEND_PORT = 8000
FRONTEND_PATH = "viewer/index.html"
BACKEND_SCRIPT = "backend/server.py"
STARTUP_TIMEOUT = 30  # segundos para aguardar o backend iniciar

class GPUMonitorLauncher:
    def __init__(self):
        self.backend_process = None
        self.backend_url = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
        self.frontend_url = f"file:///{os.path.abspath(FRONTEND_PATH).replace(os.sep, '/')}"
        self.running = True
        
    def log(self, message, level="INFO"):
        """Log com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def check_backend_health(self):
        """Verifica se o backend está respondendo"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def wait_for_backend(self, timeout=STARTUP_TIMEOUT):
        """Aguarda o backend ficar disponível"""
        self.log(f"Aguardando backend em {self.backend_url}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_backend_health():
                self.log("✅ Backend está respondendo!")
                return True
            time.sleep(1)
        
        self.log("❌ Timeout: Backend não respondeu no tempo esperado", "ERROR")
        return False
    
    def start_backend(self):
        """Inicia o processo do backend"""
        self.log("🚀 Iniciando backend...")
        
        # Verifica se o script do backend existe
        if not os.path.exists(BACKEND_SCRIPT):
            self.log(f"❌ Script do backend não encontrado: {BACKEND_SCRIPT}", "ERROR")
            return False
        
        try:
            # Muda para o diretório do backend
            backend_dir = os.path.dirname(BACKEND_SCRIPT)
            if backend_dir:
                os.chdir(backend_dir)
                script_name = os.path.basename(BACKEND_SCRIPT)
            else:
                script_name = BACKEND_SCRIPT
            
            # Inicia o processo do backend
            self.backend_process = subprocess.Popen(
                [sys.executable, script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.log(f"Backend iniciado com PID: {self.backend_process.pid}")
            
            # Thread para capturar logs do backend
            def log_backend_output():
                for line in iter(self.backend_process.stdout.readline, ''):
                    if line.strip():
                        self.log(f"[Backend] {line.strip()}")
                        
            threading.Thread(target=log_backend_output, daemon=True).start()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao iniciar backend: {e}", "ERROR")
            return False
    
    def open_browser(self):
        """Abre o navegador com a interface"""
        self.log("🌐 Abrindo navegador...")
        
        # Verifica se o arquivo HTML existe
        if not os.path.exists(FRONTEND_PATH):
            self.log(f"❌ Interface não encontrada: {FRONTEND_PATH}", "ERROR")
            return False
        
        try:
            # Tenta abrir no navegador padrão
            webbrowser.open(self.frontend_url)
            self.log(f"✅ Interface aberta em: {self.frontend_url}")
            return True
        except Exception as e:
            self.log(f"❌ Erro ao abrir navegador: {e}", "ERROR")
            self.log(f"Abra manualmente: {self.frontend_url}")
            return False
    
    def setup_signal_handlers(self):
        """Configura handlers para sinais de interrupção"""
        def signal_handler(signum, frame):
            self.log("\n🛑 Interrupção recebida. Finalizando...")
            self.running = False
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def cleanup(self):
        """Limpa recursos e finaliza processos"""
        if self.backend_process:
            self.log("🧹 Finalizando backend...")
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                self.log("✅ Backend finalizado")
            except subprocess.TimeoutExpired:
                self.log("⚠️ Forçando finalização do backend...")
                self.backend_process.kill()
            except Exception as e:
                self.log(f"❌ Erro ao finalizar backend: {e}", "ERROR")
    
    def run(self):
        """Executa o launcher completo"""
        self.log("🖥️ GPU Monitor - Iniciando aplicação...")
        self.log("=" * 60)
        
        # Configura handlers de sinal
        self.setup_signal_handlers()
        
        # Verifica se já há um backend rodando
        if self.check_backend_health():
            self.log("⚠️ Backend já está rodando!")
            response = input("Deseja abrir apenas o navegador? (S/n): ").lower().strip()
            if response in ['', 's', 'sim', 'y', 'yes']:
                self.open_browser()
                return
        
        # Inicia o backend
        if not self.start_backend():
            return
        
        # Aguarda o backend ficar disponível
        if not self.wait_for_backend():
            self.cleanup()
            return
        
        # Abre o navegador
        self.open_browser()
        
        # Mantém a aplicação rodando
        self.log("✅ Aplicação iniciada com sucesso!")
        self.log("🔗 Backend: " + self.backend_url)
        self.log("🌐 Frontend: " + self.frontend_url)
        self.log("")
        self.log("💡 Dicas:")
        self.log("   - Use Ctrl+C para finalizar a aplicação")
        self.log("   - O backend roda em segundo plano")
        self.log("   - A interface atualiza automaticamente")
        self.log("")
        
        try:
            # Loop principal - mantém a aplicação viva
            while self.running:
                time.sleep(1)
                
                # Verifica se o backend ainda está rodando
                if self.backend_process and self.backend_process.poll() is not None:
                    self.log("❌ Backend foi finalizado inesperadamente", "ERROR")
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

def main():
    """Função principal"""
    # Verifica se estamos no diretório correto
    if not os.path.exists("viewer") or not os.path.exists("backend"):
        print("❌ Execute este script a partir do diretório raiz do projeto")
        print("   Deve conter as pastas 'viewer' e 'backend'")
        sys.exit(1)
    
    # Verifica dependências básicas
    try:
        import requests
    except ImportError:
        print("❌ Biblioteca 'requests' não encontrada")
        print("   Execute: pip install requests")
        sys.exit(1)
    
    # Inicia o launcher
    launcher = GPUMonitorLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
