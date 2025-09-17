#!/usr/bin/env python3
"""
Script para executar o GPU Monitor
Oferece diferentes opções de execução
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

def check_nvidia_smi():
    """Verifica se nvidia-smi está disponível"""
    try:
        result = subprocess.run(['nvidia-smi', '--version'], 
                              capture_output=True, text=True, check=True)
        print("✅ nvidia-smi encontrado")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ nvidia-smi não encontrado ou não funcional")
        print("   Certifique-se de que os drivers NVIDIA estão instalados")
        return False

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import fastapi
        import uvicorn
        import websockets
        import pydantic
        print("✅ Dependências principais encontradas")
        return True
    except ImportError as e:
        print(f"❌ Dependência não encontrada: {e}")
        print("   Execute: pip install -r requirements.txt")
        return False

def run_server(host="0.0.0.0", port=8000, reload=False):
    """Executa o servidor FastAPI"""
    print(f"🚀 Iniciando servidor em http://{host}:{port}")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "server:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido pelo usuário")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar servidor: {e}")

def run_monitor_only():
    """Executa apenas o monitor (sem servidor web)"""
    print("📊 Executando apenas o monitor de GPU")
    try:
        subprocess.run([sys.executable, "gpu_monitor.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Monitor interrompido pelo usuário")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar monitor: {e}")

def run_test_client():
    """Executa o cliente de teste"""
    print("🧪 Executando cliente de teste")
    try:
        subprocess.run([sys.executable, "test_client.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar cliente de teste: {e}")

def install_dependencies():
    """Instala as dependências"""
    print("📦 Instalando dependências...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependências instaladas com sucesso")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="GPU Monitor - Sistema de monitoramento de GPU",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run.py                    # Executa servidor completo
  python run.py --monitor-only     # Apenas monitor (sem web)
  python run.py --test             # Cliente de teste
  python run.py --install          # Instala dependências
  python run.py --port 8080        # Servidor na porta 8080
  python run.py --host 127.0.0.1   # Servidor apenas local
        """
    )
    
    parser.add_argument(
        "--monitor-only", 
        action="store_true",
        help="Executa apenas o monitor (sem servidor web)"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Executa cliente de teste"
    )
    
    parser.add_argument(
        "--install", 
        action="store_true",
        help="Instala dependências do requirements.txt"
    )
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Host do servidor (padrão: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", 
        type=int,
        default=8000,
        help="Porta do servidor (padrão: 8000)"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Habilita reload automático (desenvolvimento)"
    )
    
    parser.add_argument(
        "--skip-checks", 
        action="store_true",
        help="Pula verificações de dependências"
    )
    
    args = parser.parse_args()
    
    print("🖥️  GPU Monitor - Sistema de Monitoramento")
    print("=" * 50)
    
    # Instalar dependências se solicitado
    if args.install:
        install_dependencies()
        return
    
    # Verificações de sistema (se não puladas)
    if not args.skip_checks:
        if not check_nvidia_smi():
            response = input("Continuar mesmo assim? (s/N): ").lower().strip()
            if response not in ['s', 'sim', 'y', 'yes']:
                return
        
        if not check_dependencies():
            print("\nTente executar: python run.py --install")
            return
    
    # Executa a opção escolhida
    if args.test:
        run_test_client()
    elif args.monitor_only:
        run_monitor_only()
    else:
        run_server(args.host, args.port, args.reload)

if __name__ == "__main__":
    main()
