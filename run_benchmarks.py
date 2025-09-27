#!/usr/bin/env python3
"""
Script principal para executar todos os benchmarks e testes
"""

import asyncio
import subprocess
import sys
import os
import time
import json
from datetime import datetime

def run_command(command, description, capture_output=True):
    """Executa um comando e retorna o resultado"""
    print(f"🔄 {description}...")
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            return True, result.stdout if capture_output else ""
        else:
            print(f"❌ {description} - Erro: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False, str(e)

def check_docker():
    """Verifica se o Docker está instalado e funcionando"""
    print("🐳 VERIFICANDO DOCKER")
    print("=" * 40)
    
    # Verificar se Docker está instalado
    success, output = run_command("docker --version", "Verificando instalação do Docker")
    if not success:
        print("❌ Docker não está instalado ou não está no PATH")
        return False
    
    # Verificar se Docker está rodando
    success, output = run_command("docker info", "Verificando se Docker está rodando")
    if not success:
        print("❌ Docker não está rodando. Inicie o Docker Desktop e tente novamente.")
        return False
    
    print("✅ Docker está funcionando corretamente")
    return True

def setup_databases():
    """Configura os bancos de dados usando Docker"""
    print("\n📦 CONFIGURANDO BANCOS DE DADOS")
    print("=" * 40)
    
    # Parar containers existentes
    run_command("docker-compose down", "Parando containers existentes", capture_output=False)
    
    # Iniciar containers
    success, output = run_command("docker-compose up -d", "Iniciando containers Docker")
    if not success:
        return False
    
    # Aguardar bancos ficarem disponíveis
    print("⏳ Aguardando bancos ficarem disponíveis...")
    time.sleep(30)  # Aguardar 30 segundos para os bancos iniciarem
    
    # Verificar se os containers estão rodando
    success, output = run_command("docker-compose ps", "Verificando status dos containers")
    if success:
        print("📊 Status dos containers:")
        print(output)
    
    return True

def install_dependencies():
    """Instala dependências necessárias para os testes"""
    print("\n📦 INSTALANDO DEPENDÊNCIAS")
    print("=" * 40)
    
    dependencies = [
        "pytest",
        "pytest-asyncio",
        "asyncpg",
        "aiosqlite",
        "aiomysql",
        "aioodbc"
    ]
    
    for dep in dependencies:
        success, output = run_command(f"pip install {dep}", f"Instalando {dep}")
        if not success:
            print(f"⚠️  Falha ao instalar {dep}, mas continuando...")

def run_tests():
    """Executa todos os testes"""
    print("\n🧪 EXECUTANDO TESTES")
    print("=" * 40)
    
    # Testes de bancos reais
    print("\n📊 Testes com Bancos Reais:")
    success, output = run_command(
        "python -m pytest tests/test_real_databases.py -v --tb=short",
        "Executando testes com bancos reais"
    )
    
    if success:
        print("✅ Testes com bancos reais concluídos")
    else:
        print("❌ Alguns testes com bancos reais falharam")
        print(output)
    
    # Testes de benchmark
    print("\n⚡ Testes de Benchmark:")
    success, output = run_command(
        "python -m pytest tests/test_benchmark_comparison.py -v --tb=short -s",
        "Executando testes de benchmark"
    )
    
    if success:
        print("✅ Testes de benchmark concluídos")
    else:
        print("❌ Alguns testes de benchmark falharam")
        print(output)
    
    return success

def generate_report():
    """Gera relatório final dos testes"""
    print("\n📋 GERANDO RELATÓRIO")
    print("=" * 40)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"benchmark_report_{timestamp}.json"
    
    report = {
        "timestamp": timestamp,
        "environment": {
            "os": os.name,
            "python_version": sys.version,
            "platform": sys.platform
        },
        "tests_executed": [
            "test_real_databases.py",
            "test_benchmark_comparison.py"
        ],
        "databases_tested": [
            "PostgreSQL 15",
            "SQL Server 2022", 
            "MySQL 8.0"
        ],
        "libraries_compared": [
            "KaironDB",
            "AsyncPG",
            "AioSQLite"
        ]
    }
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ Relatório salvo em: {report_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar relatório: {e}")

def cleanup():
    """Limpa recursos após os testes"""
    print("\n🧹 LIMPEZA")
    print("=" * 40)
    
    # Parar containers
    run_command("docker-compose down", "Parando containers Docker", capture_output=False)
    
    # Remover arquivos temporários
    temp_files = [
        "benchmark_test.db",
        "test_*.db"
    ]
    
    for pattern in temp_files:
        try:
            if os.path.exists(pattern):
                os.remove(pattern)
                print(f"✅ Removido: {pattern}")
        except Exception as e:
            print(f"⚠️  Erro ao remover {pattern}: {e}")

def main():
    """Função principal"""
    print("🚀 KAIRONDB - SUITE DE TESTES E BENCHMARKS")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Verificar Docker
        if not check_docker():
            print("\n❌ Docker não está disponível. Instale o Docker Desktop e tente novamente.")
            return 1
        
        # 2. Instalar dependências
        install_dependencies()
        
        # 3. Configurar bancos de dados
        if not setup_databases():
            print("\n❌ Falha ao configurar bancos de dados.")
            return 1
        
        # 4. Executar testes
        if not run_tests():
            print("\n⚠️  Alguns testes falharam, mas continuando...")
        
        # 5. Gerar relatório
        generate_report()
        
        print("\n🎉 SUITE DE TESTES CONCLUÍDA!")
        print("=" * 60)
        print("📊 Resultados disponíveis em:")
        print("   • docs/BENCHMARK_RESULTS.md")
        print("   • benchmark_report_*.json")
        print("\n💡 Para executar testes específicos:")
        print("   • python -m pytest tests/test_real_databases.py -v")
        print("   • python -m pytest tests/test_benchmark_comparison.py -v -s")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Testes interrompidos pelo usuário")
        return 1
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1
    finally:
        # Limpeza final
        cleanup()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
