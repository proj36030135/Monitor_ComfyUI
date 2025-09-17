#!/usr/bin/env python3
"""
Script para inicializar o GPU Monitor completo: Backend FastAPI + Frontend Next.js
Gerencia ambos os processos e fornece logs unificados
"""

import os
import sys
import time
import signal
import subprocess
import threading
import requests
import webbrowser
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gpu_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

class Colors:
    """Cores para output no terminal"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class FullStackManager:
    """Gerencia backend e frontend simultaneamente"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        
    def print_banner(self):
        """Mostra banner de inicialização"""
        banner = f"""
{Colors.BLUE}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    🖥️  GPU Monitor FullStack                 ║
║                                                              ║
║  Backend:  FastAPI + WebSocket + SQLite                     ║
║  Frontend: Next.js + ShadCN UI + TypeScript                 ║
║                                                              ║
║  🚀 Iniciando aplicação completa...                          ║
╚══════════════════════════════════════════════════════════════╝
{Colors.ENDC}
        """
        print(banner)
    
    def check_requirements(self):
        """Verifica se as dependências estão instaladas"""
        logger.info("🔍 Verificando dependências...")
        
        # Verificar Python
        try:
            import uvicorn, fastapi, sqlalchemy, psutil
            logger.info(f"✅ Backend dependencies OK")
        except ImportError as e:
            logger.error(f"❌ Backend dependency missing: {e}")
            logger.info("💡 Execute: pip install -r backend/requirements.txt")
            return False
        
        # Verificar Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, cwd=self.frontend_dir)
            if result.returncode == 0:
                logger.info(f"✅ Node.js {result.stdout.strip()}")
            else:
                logger.error("❌ Node.js não encontrado")
                return False
        except FileNotFoundError:
            logger.error("❌ Node.js não está instalado")
            return False
        
        # Verificar dependências do frontend
        if not (self.frontend_dir / "node_modules").exists():
            logger.warning("⚠️  Frontend dependencies not installed")
            logger.info("📦 Installing frontend dependencies...")
            result = subprocess.run(["npm", "install"], cwd=self.frontend_dir)
            if result.returncode != 0:
                logger.error("❌ Failed to install frontend dependencies")
                return False
        
        logger.info("✅ Todas as dependências estão OK")
        return True
    
    def wait_for_service(self, url, service_name, timeout=30):
        """Aguarda serviço ficar disponível"""
        logger.info(f"⏳ Aguardando {service_name} ficar disponível...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} está disponível!")
                    return True
            except:
                pass
            time.sleep(1)
        
        logger.error(f"❌ {service_name} não ficou disponível em {timeout}s")
        return False
    
    def start_backend(self):
        """Inicia o servidor backend"""
        logger.info("🚀 Iniciando Backend (FastAPI)...")
        
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.backend_dir)
            
            self.backend_process = subprocess.Popen(
                [sys.executable, "server.py"],
                cwd=self.backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread para logs do backend
            def log_backend_output():
                while self.backend_process and self.backend_process.poll() is None:
                    if self.backend_process.stdout:
                        line = self.backend_process.stdout.readline()
                        if line:
                            logger.info(f"[BACKEND] {line.strip()}")
            
            threading.Thread(target=log_backend_output, daemon=True).start()
            
            # Aguardar backend ficar disponível
            if not self.wait_for_service("http://localhost:8000/api/health", "Backend", 30):
                return False
            
            logger.info("✅ Backend iniciado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar backend: {e}")
            return False
    
    def start_frontend(self):
        """Inicia o servidor frontend"""
        logger.info("🚀 Iniciando Frontend (Next.js)...")
        
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread para logs do frontend
            def log_frontend_output():
                while self.frontend_process and self.frontend_process.poll() is None:
                    if self.frontend_process.stdout:
                        line = self.frontend_process.stdout.readline()
                        if line:
                            # Filtrar logs desnecessários do Next.js
                            if not any(skip in line.lower() for skip in ['fast refresh', 'compiled', 'attention:']):
                                logger.info(f"[FRONTEND] {line.strip()}")
            
            threading.Thread(target=log_frontend_output, daemon=True).start()
            
            # Aguardar frontend ficar disponível
            if not self.wait_for_service("http://localhost:3000", "Frontend", 45):
                return False
            
            logger.info("✅ Frontend iniciado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar frontend: {e}")
            return False
    
    def open_browser(self):
        """Abre o navegador automaticamente"""
        logger.info("🌐 Abrindo navegador...")
        try:
            webbrowser.open("http://localhost:3000")
            logger.info("✅ Navegador aberto com sucesso!")
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível abrir o navegador: {e}")
            logger.info("💡 Abra manualmente: http://localhost:3000")
    
    def show_status(self):
        """Mostra status dos serviços"""
        status_info = f"""
{Colors.GREEN}{Colors.BOLD}
🎉 GPU Monitor está rodando com sucesso!
{Colors.ENDC}
{Colors.BLUE}┌─ Serviços Ativos ─────────────────────────────┐
│                                               │
│  🖥️  Backend:   http://localhost:8000         │
│  🌐 Frontend:   http://localhost:3000         │
│  📡 WebSocket:  ws://localhost:8000/ws        │
│  📊 API Docs:   http://localhost:8000/docs    │
│                                               │
│  📝 Logs:       gpu_monitor.log               │
│                                               │
└───────────────────────────────────────────────┘{Colors.ENDC}

{Colors.YELLOW}💡 Dicas:
  • O dashboard conectará automaticamente ao backend
  • Use Ctrl+C para parar ambos os serviços
  • Logs são salvos em gpu_monitor.log
  • Acesse /docs para documentação da API{Colors.ENDC}

{Colors.GREEN}▶️  Pressione Ctrl+C para parar os serviços{Colors.ENDC}
        """
        print(status_info)
    
    def signal_handler(self, signum, frame):
        """Handler para sinais de sistema"""
        logger.info("🛑 Recebido sinal de parada...")
        self.shutdown()
    
    def shutdown(self):
        """Para todos os serviços"""
        logger.info("🔄 Parando serviços...")
        
        if self.frontend_process:
            logger.info("🛑 Parando frontend...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            logger.info("✅ Frontend parado")
        
        if self.backend_process:
            logger.info("🛑 Parando backend...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            logger.info("✅ Backend parado")
        
        logger.info("✅ Todos os serviços foram parados")
        sys.exit(0)
    
    def run(self):
        """Executa a aplicação completa"""
        # Configurar handler de sinais
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.print_banner()
        
        # Verificar dependências
        if not self.check_requirements():
            sys.exit(1)
        
        try:
            # Iniciar backend
            if not self.start_backend():
                sys.exit(1)
            
            # Iniciar frontend
            if not self.start_frontend():
                self.shutdown()
                sys.exit(1)
            
            # Abrir navegador
            time.sleep(2)  # Aguardar um pouco para estabilizar
            self.open_browser()
            
            # Mostrar status
            self.show_status()
            
            # Manter vivo
            while True:
                time.sleep(1)
                
                # Verificar se os processos ainda estão rodando
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("❌ Backend parou inesperadamente")
                    self.shutdown()
                    sys.exit(1)
                
                if self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("❌ Frontend parou inesperadamente")
                    self.shutdown()
                    sys.exit(1)
        
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário")
            self.shutdown()
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            self.shutdown()
            sys.exit(1)

def main():
    """Função principal"""
    manager = FullStackManager()
    manager.run()

if __name__ == "__main__":
    main()
