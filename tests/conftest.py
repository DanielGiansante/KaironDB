"""
Configuração global para testes pytest
"""

import pytest
import sys
from pathlib import Path

# Adicionar src ao path para importar o módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def sample_user_data():
    """Dados de exemplo para testes de usuário"""
    return {
        "name": "João Silva",
        "email": "joao@test.com",
        "age": 30
    }

@pytest.fixture
def sample_connection_params():
    """Parâmetros de conexão de exemplo para testes"""
    return {
        "driver": "sqlite3",
        "server": "./test.db",
        "db_name": "",
        "user": "",
        "password": ""
    }
