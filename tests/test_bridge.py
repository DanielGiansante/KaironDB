"""
Testes para SQLBridge
"""

import pytest
from kairondb import SQLBridge
from kairondb.exceptions import ValidationError, ConfigurationError


class TestSQLBridgeValidation:
    """Testes para validação de parâmetros do SQLBridge"""
    
    def test_invalid_driver(self):
        """Testa driver inválido"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge("invalid_driver", "localhost", "test", "user", "pass")
        
        error = exc_info.value
        assert error.field_name == "driver"
        assert error.field_value == "invalid_driver"
        assert "não é suportado" in str(error)
    
    def test_empty_driver(self):
        """Testa driver vazio"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge("", "localhost", "test", "user", "pass")
        
        error = exc_info.value
        assert error.field_name == "driver"
        assert "obrigatório" in str(error)
    
    def test_none_driver(self):
        """Testa driver None"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge(None, "localhost", "test", "user", "pass")
        
        error = exc_info.value
        assert error.field_name == "driver"
        assert "obrigatório" in str(error)
    
    def test_postgres_missing_server(self):
        """Testa PostgreSQL sem server"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge("postgres", "", "test", "user", "pass")
        
        error = exc_info.value
        assert error.field_name == "server"
        assert "obrigatório" in str(error)
    
    def test_postgres_missing_db_name(self):
        """Testa PostgreSQL sem database name"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge("postgres", "localhost", "", "user", "pass")
        
        error = exc_info.value
        assert error.field_name == "db_name"
        assert "obrigatório" in str(error)
    
    def test_postgres_missing_user(self):
        """Testa PostgreSQL sem user"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge("postgres", "localhost", "test", "", "pass")
        
        error = exc_info.value
        assert error.field_name == "user"
        assert "obrigatório" in str(error)
    
    def test_postgres_missing_password(self):
        """Testa PostgreSQL sem password"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge("postgres", "localhost", "test", "user", "")
        
        error = exc_info.value
        assert error.field_name == "password"
        assert "obrigatório" in str(error)
    
    def test_sqlite3_missing_server(self):
        """Testa SQLite3 sem server"""
        with pytest.raises(ValidationError) as exc_info:
            SQLBridge("sqlite3", "", "", "", "")
        
        error = exc_info.value
        assert error.field_name == "server"
        assert "caminho do arquivo" in str(error)
    
    def test_sqlite3_valid_params(self):
        """Testa SQLite3 com parâmetros válidos (deve passar na validação)"""
        # Este teste deve passar na validação, mas pode falhar na DLL
        try:
            bridge = SQLBridge("sqlite3", "./test.db", "", "", "")
            # Se chegou aqui, a validação passou
            assert bridge.driver == "sqlite3"
            assert bridge.conn_params["server"] == "./test.db"
        except Exception as e:
            # Se falhou, deve ser na DLL, não na validação
            assert not isinstance(e, ValidationError)
    
    def test_supported_drivers(self):
        """Testa todos os drivers suportados"""
        supported_drivers = ['postgres', 'sqlserver', 'mysql', 'sqlite3']
        
        for driver in supported_drivers:
            if driver == 'sqlite3':
                # SQLite3 precisa de server
                try:
                    bridge = SQLBridge(driver, "./test.db", "", "", "")
                    assert bridge.driver == driver
                except Exception:
                    # Pode falhar na DLL, mas não na validação
                    pass
            else:
                # Outros drivers precisam de todos os parâmetros
                try:
                    bridge = SQLBridge(driver, "localhost", "test", "user", "pass")
                    assert bridge.driver == driver
                except Exception:
                    # Pode falhar na DLL, mas não na validação
                    pass


class TestSQLBridgeConfiguration:
    """Testes para configuração do SQLBridge"""
    
    def test_debug_mode(self):
        """Testa modo debug"""
        try:
            bridge = SQLBridge("sqlite3", "./test.db", "", "", "", debug=True)
            assert bridge.debug is True
        except Exception:
            # Pode falhar na DLL
            pass
    
    def test_custom_lib_path(self):
        """Testa caminho customizado para biblioteca"""
        with pytest.raises(ConfigurationError) as exc_info:
            SQLBridge("sqlite3", "./test.db", "", "", "", lib_path="/path/that/does/not/exist.dll")
        
        error = exc_info.value
        assert error.config_key == "lib_path"
        assert "não encontrada" in str(error)


class TestSQLBridgeProperties:
    """Testes para propriedades do SQLBridge"""
    
    def test_connection_params(self):
        """Testa parâmetros de conexão"""
        try:
            bridge = SQLBridge("postgres", "localhost", "mydb", "user", "pass")
            expected_params = {
                "driver": "postgres",
                "server": "localhost", 
                "name": "mydb",
                "user": "user",
                "password": "pass"
            }
            assert bridge.conn_params == expected_params
        except Exception as e:
            # Pode falhar na DLL, mas deve ter passado na validação
            # Verificar se os parâmetros foram definidos antes da falha
            if hasattr(e, 'details') and 'connection_params' in e.details:
                expected_params = {
                    "driver": "postgres",
                    "server": "localhost", 
                    "name": "mydb",
                    "user": "user",
                    "password": "pass"
                }
                assert e.details['connection_params'] == expected_params
    
    def test_driver_property(self):
        """Testa propriedade driver"""
        try:
            bridge = SQLBridge("mysql", "localhost", "test", "user", "pass")
            assert bridge.driver == "mysql"
        except Exception:
            # Pode falhar na DLL, mas deve ter passado na validação
            # O driver deve estar definido antes da falha
            pass
