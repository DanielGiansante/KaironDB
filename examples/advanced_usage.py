#!/usr/bin/env python3
"""
Exemplos de Uso Avançado do KaironDB

Este arquivo contém exemplos práticos de como usar as funcionalidades
avançadas do KaironDB, incluindo pooling de conexões, cache, migrations,
profiling e dashboard de métricas.
"""

import asyncio
import time
import os
import sys
from typing import List, Dict, Any

# Adicionar o diretório 'src' ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kairondb import (
    SQLBridge, Model, StringField, IntegerField, DateTimeField, EmailField,
    Q, ValidationError, ConnectionError
)


# ============================================================================
# 1. CONFIGURAÇÃO AVANÇADA COM TODAS AS FUNCIONALIDADES
# ============================================================================

async def exemplo_configuracao_completa():
    """Exemplo de configuração com todas as funcionalidades ativadas."""
    print("🚀 Configuração Completa do KaironDB")
    print("=" * 50)
    
    # Configuração do pool de conexões
    pool_config = {
        'min_connections': 2,
        'max_connections': 10,
        'connection_timeout': 30.0,
        'idle_timeout': 300.0,
        'health_check_interval': 60.0
    }
    
    # Configuração do cache
    cache_config = {
        'max_size': 1000,
        'default_ttl': 300.0,  # 5 minutos
        'policy': 'lru'
    }
    
    # Configuração do profiling
    profiling_config = {
        'enable_profiling': True,
        'enable_metrics': True,
        'log_level': 'INFO'
    }
    
    # Configuração das otimizações
    optimization_config = {
        'enable_json_optimization': True,
        'enable_lazy_loading': True,
        'enable_caching': True,
        'cache_size': 1000
    }
    
    # Configuração do dashboard
    dashboard_config = {
        'enable_real_time': True,
        'update_interval': 1.0,
        'enable_alerts': True,
        'alert_thresholds': {
            'slow_query': 1.0,
            'high_error_rate': 0.1,
            'low_cache_hit_rate': 0.7
        }
    }
    
    try:
        # Criar bridge com todas as funcionalidades
        bridge = SQLBridge(
            driver="sqlite3",
            server=":memory:",
            db_name="advanced_example",
            user="",
            password="",
            debug=True,
            # Funcionalidades avançadas
            enable_advanced_pool=True,
            pool_config=pool_config,
            enable_query_cache=True,
            cache_config=cache_config,
            enable_migrations=True,
            migrations_dir="examples/migrations",
            # Performance e monitoramento
            enable_profiling=True,
            profiling_config=profiling_config,
            enable_optimizations=True,
            optimization_config=optimization_config,
            enable_dashboard=True,
            dashboard_config=dashboard_config
        )
        
        print("✅ Bridge criada com todas as funcionalidades")
        
        # Iniciar dashboard
        await bridge.start_dashboard()
        print("📊 Dashboard iniciado")
        
        # Executar algumas operações para demonstrar funcionalidades
        await demonstrar_operacoes_basicas(bridge)
        await demonstrar_transacoes(bridge)
        await demonstrar_cache(bridge)
        await demonstrar_profiling(bridge)
        await demonstrar_metricas(bridge)
        
        # Parar dashboard
        await bridge.stop_dashboard()
        print("🛑 Dashboard parado")
        
        # Fechar bridge
        await bridge.close()
        print("🔒 Bridge fechada")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("ℹ️  Nota: Este exemplo requer a DLL do KaironDB")


# ============================================================================
# 2. OPERAÇÕES BÁSICAS COM QUERIES COMPLEXAS
# ============================================================================

async def demonstrar_operacoes_basicas(bridge: SQLBridge):
    """Demonstra operações básicas com queries complexas."""
    print("\n📝 Operações Básicas")
    print("-" * 30)
    
    # Criar tabela
    await bridge.exec("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            idade INTEGER,
            ativo BOOLEAN DEFAULT 1,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir dados
    usuarios = [
        {"nome": "João Silva", "email": "joao@example.com", "idade": 30},
        {"nome": "Maria Santos", "email": "maria@example.com", "idade": 25},
        {"nome": "Pedro Costa", "email": "pedro@example.com", "idade": 35},
        {"nome": "Ana Oliveira", "email": "ana@example.com", "idade": 28},
        {"nome": "Carlos Lima", "email": "carlos@example.com", "idade": 42}
    ]
    
    for usuario in usuarios:
        await bridge.insert("usuarios", usuario)
    
    print(f"✅ {len(usuarios)} usuários inseridos")
    
    # Query simples
    todos_usuarios = await bridge.select("usuarios", ["*"])
    print(f"📊 Total de usuários: {len(todos_usuarios.get('data', []))}")
    
    # Query com filtros usando Q objects
    usuarios_ativos = await bridge.select(
        "usuarios", 
        ["nome", "email", "idade"],
        Q("ativo", "=", True) & Q("idade", ">", 25)
    )
    print(f"👥 Usuários ativos com mais de 25 anos: {len(usuarios_ativos.get('data', []))}")
    
    # Query com ordenação e limite
    usuarios_ordenados = await bridge.select(
        "usuarios",
        ["nome", "idade"],
        Q("ativo", "=", True),
        order_by="idade DESC",
        limit=3
    )
    print(f"🏆 Top 3 usuários mais velhos: {len(usuarios_ordenados.get('data', []))}")
    
    # Atualização em lote
    await bridge.update(
        "usuarios",
        {"ativo": False},
        Q("idade", ">", 40)
    )
    print("🔄 Usuários com mais de 40 anos desativados")
    
    # Contagem
    usuarios_ativos = await bridge.select(
        "usuarios",
        ["COUNT(*) as total"],
        Q("ativo", "=", True)
    )
    total_ativos = usuarios_ativos.get('data', [{}])[0].get('total', 0)
    print(f"📈 Usuários ativos restantes: {total_ativos}")


# ============================================================================
# 3. SISTEMA DE TRANSAÇÕES
# ============================================================================

async def demonstrar_transacoes(bridge: SQLBridge):
    """Demonstra o uso de transações."""
    print("\n🔄 Sistema de Transações")
    print("-" * 30)
    
    # Transação bem-sucedida
    print("✅ Transação bem-sucedida:")
    async with bridge.transaction() as tx:
        await tx.insert("usuarios", {
            "nome": "Transação Teste",
            "email": "transacao@example.com",
            "idade": 30
        })
        await tx.update("usuarios", {"ativo": True}, {"nome": "Transação Teste"})
        print("  - Usuário inserido e ativado na transação")
    
    # Transação com rollback
    print("❌ Transação com rollback:")
    try:
        async with bridge.transaction() as tx:
            await tx.insert("usuarios", {
                "nome": "Rollback Teste",
                "email": "rollback@example.com",
                "idade": 30
            })
            # Simular erro
            await tx.insert("usuarios", {
                "nome": "Erro Duplicado",
                "email": "joao@example.com",  # Email duplicado
                "idade": 30
            })
    except Exception as e:
        print(f"  - Erro capturado: {e}")
        print("  - Transação revertida automaticamente")
    
    # Verificar se o usuário do rollback não foi inserido
    resultado = await bridge.select("usuarios", ["nome"], {"nome": "Rollback Teste"})
    if not resultado.get('data'):
        print("  - Confirmação: usuário do rollback não foi inserido")


# ============================================================================
# 4. SISTEMA DE CACHE
# ============================================================================

async def demonstrar_cache(bridge: SQLBridge):
    """Demonstra o sistema de cache."""
    print("\n💾 Sistema de Cache")
    print("-" * 30)
    
    # Query que será cacheada
    print("🔍 Executando query (primeira vez - sem cache):")
    start_time = time.time()
    resultado1 = await bridge.select("usuarios", ["*"], {"ativo": True})
    tempo1 = time.time() - start_time
    print(f"  - Tempo: {tempo1:.4f}s")
    print(f"  - Resultados: {len(resultado1.get('data', []))}")
    
    # Mesma query (deve usar cache)
    print("⚡ Executando mesma query (segunda vez - com cache):")
    start_time = time.time()
    resultado2 = await bridge.select("usuarios", ["*"], {"ativo": True})
    tempo2 = time.time() - start_time
    print(f"  - Tempo: {tempo2:.4f}s")
    print(f"  - Melhoria: {tempo1/tempo2:.1f}x mais rápido")
    
    # Invalidação de cache
    print("🗑️ Invalidando cache da tabela 'usuarios':")
    invalidados = await bridge.invalidate_cache(table="usuarios")
    print(f"  - Entradas invalidadas: {invalidados}")
    
    # Query após invalidação
    print("🔄 Executando query após invalidação:")
    start_time = time.time()
    resultado3 = await bridge.select("usuarios", ["*"], {"ativo": True})
    tempo3 = time.time() - start_time
    print(f"  - Tempo: {tempo3:.4f}s")
    
    # Métricas do cache
    cache_metrics = bridge.get_cache_metrics()
    if cache_metrics:
        print(f"📊 Métricas do cache:")
        print(f"  - Hits: {cache_metrics.get('hits', 0)}")
        print(f"  - Misses: {cache_metrics.get('misses', 0)}")
        print(f"  - Hit Rate: {cache_metrics.get('hit_rate', 0):.2%}")


# ============================================================================
# 5. SISTEMA DE PROFILING
# ============================================================================

async def demonstrar_profiling(bridge: SQLBridge):
    """Demonstra o sistema de profiling."""
    print("\n🔍 Sistema de Profiling")
    print("-" * 30)
    
    # Executar várias operações para gerar métricas
    operacoes = [
        ("SELECT simples", lambda: bridge.select("usuarios", ["nome"])),
        ("SELECT com filtro", lambda: bridge.select("usuarios", ["*"], {"ativo": True})),
        ("SELECT com ordenação", lambda: bridge.select("usuarios", ["nome", "idade"], order_by="idade DESC")),
        ("UPDATE", lambda: bridge.update("usuarios", {"ativo": True}, {"idade": ">", "value": 30})),
        ("COUNT", lambda: bridge.select("usuarios", ["COUNT(*) as total"]))
    ]
    
    for nome, operacao in operacoes:
        start_time = time.time()
        await operacao()
        end_time = time.time()
        print(f"  - {nome}: {end_time - start_time:.4f}s")
    
    # Métricas de performance
    perf_metrics = bridge.get_performance_metrics()
    if perf_metrics:
        print(f"\n📊 Métricas de Performance:")
        print(f"  - Total de operações: {perf_metrics.get('total_metrics', 0)}")
        print(f"  - Duração média: {perf_metrics.get('average_duration', 0):.4f}s")
        print(f"  - Duração total: {perf_metrics.get('total_duration', 0):.4f}s")
        
        # Detalhes por operação
        operations = perf_metrics.get('operations', {})
        if operations:
            print(f"  - Detalhes por operação:")
            for op, stats in operations.items():
                print(f"    * {op}: {stats['count']} execuções, "
                      f"média {stats['average_duration']:.4f}s")
    
    # Métricas de queries
    query_metrics = bridge.get_query_metrics()
    if query_metrics:
        print(f"\n📈 Métricas de Queries:")
        print(f"  - Total de queries: {query_metrics.get('total_queries', 0)}")
        print(f"  - Tempo médio: {query_metrics.get('average_execution_time', 0):.4f}s")
        
        # Detalhes por tabela
        tables = query_metrics.get('tables', {})
        if tables:
            print(f"  - Queries por tabela:")
            for table, stats in tables.items():
                print(f"    * {table}: {stats['count']} queries, "
                      f"tempo total {stats['total_time']:.4f}s")


# ============================================================================
# 6. DASHBOARD E MÉTRICAS
# ============================================================================

async def demonstrar_metricas(bridge: SQLBridge):
    """Demonstra o dashboard e métricas."""
    print("\n📊 Dashboard e Métricas")
    print("-" * 30)
    
    # Aguardar um pouco para o dashboard coletar dados
    await asyncio.sleep(2)
    
    # Resumo do dashboard
    summary = bridge.get_dashboard_summary()
    if summary:
        print(f"📈 Resumo do Sistema:")
        print(f"  - Status: {summary.get('status', 'unknown')}")
        print(f"  - Score: {summary.get('score', 0)}")
        print(f"  - Queries executadas: {summary.get('total_queries', 0)}")
        print(f"  - Operações executadas: {summary.get('total_operations', 0)}")
        print(f"  - Cache Hit Rate: {summary.get('cache_hit_rate', 0):.2%}")
        print(f"  - Alertas ativos: {summary.get('active_alerts', 0)}")
        print(f"  - Uptime: {summary.get('uptime', 0):.2f}s")
    
    # Métricas do pool de conexões
    pool_metrics = await bridge.get_advanced_pool_metrics()
    if pool_metrics:
        print(f"\n🏊 Métricas do Pool de Conexões:")
        print(f"  - Conexões atuais: {pool_metrics.get('current_connections', 0)}")
        print(f"  - Conexões máximas: {pool_metrics.get('max_connections', 0)}")
        print(f"  - Conexões ociosas: {pool_metrics.get('idle_connections', 0)}")
        print(f"  - Conexões ativas: {pool_metrics.get('active_connections', 0)}")
        print(f"  - Pico de conexões: {pool_metrics.get('peak_connections', 0)}")
    
    # Estatísticas de otimização
    opt_stats = bridge.get_optimization_stats()
    if opt_stats:
        print(f"\n⚡ Estatísticas de Otimização:")
        for key, value in opt_stats.items():
            print(f"  - {key}: {value}")


# ============================================================================
# 7. MODELOS AVANÇADOS COM VALIDAÇÃO
# ============================================================================

class Usuario(Model):
    """Modelo de usuário com validações avançadas."""
    nome = StringField(required=True, max_length=100)
    email = EmailField(required=True)
    idade = IntegerField(min_value=18, max_value=120)
    ativo = IntegerField(default=1)
    criado_em = DateTimeField(auto_now_add=True)


async def demonstrar_modelos_avancados():
    """Demonstra o uso de modelos avançados."""
    print("\n🏗️ Modelos Avançados")
    print("-" * 30)
    
    # Criar usuários com validação
    try:
        usuario1 = Usuario(
            nome="João Silva",
            email="joao@example.com",
            idade=30
        )
        print("✅ Usuário 1 criado com sucesso")
        
        usuario2 = Usuario(
            nome="Maria Santos",
            email="maria@example.com",
            idade=25
        )
        print("✅ Usuário 2 criado com sucesso")
        
        # Tentar criar usuário inválido
        try:
            usuario_invalido = Usuario(
                nome="",  # Nome vazio
                email="email-invalido",  # Email inválido
                idade=15  # Idade inválida
            )
        except ValidationError as e:
            print(f"❌ Validação funcionando: {e}")
        
    except Exception as e:
        print(f"❌ Erro na criação de modelos: {e}")


# ============================================================================
# 8. EXEMPLO DE MIGRATION
# ============================================================================

async def demonstrar_migrations(bridge: SQLBridge):
    """Demonstra o sistema de migrations."""
    print("\n🔄 Sistema de Migrations")
    print("-" * 30)
    
    # Criar migration
    migration_id = await bridge.create_migration(
        name="Adicionar campo telefone",
        up_sql="ALTER TABLE usuarios ADD COLUMN telefone TEXT",
        down_sql="ALTER TABLE usuarios DROP COLUMN telefone"
    )
    print(f"✅ Migration criada: {migration_id}")
    
    # Listar migrations
    migrations = bridge.list_migrations()
    print(f"📋 Migrations disponíveis: {len(migrations)}")
    
    # Executar migrations
    try:
        executed = await bridge.run_migrations()
        print(f"🚀 Migrations executadas: {len(executed)}")
    except Exception as e:
        print(f"ℹ️  Nota: {e}")


# ============================================================================
# 9. FUNÇÃO PRINCIPAL
# ============================================================================

async def main():
    """Função principal que executa todos os exemplos."""
    print("🎯 EXEMPLOS AVANÇADOS DO KAIRONDB")
    print("=" * 60)
    print()
    
    # Executar exemplos
    await exemplo_configuracao_completa()
    await demonstrar_modelos_avancados()
    
    print("\n✅ Todos os exemplos foram executados!")
    print("\n📚 Funcionalidades demonstradas:")
    print("  • Configuração completa com todas as funcionalidades")
    print("  • Operações básicas com queries complexas")
    print("  • Sistema de transações com rollback")
    print("  • Sistema de cache com invalidação")
    print("  • Sistema de profiling e métricas")
    print("  • Dashboard em tempo real")
    print("  • Modelos com validação avançada")
    print("  • Sistema de migrations")


if __name__ == "__main__":
    asyncio.run(main())
