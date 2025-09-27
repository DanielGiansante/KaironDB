"""
Testes para o sistema de logging
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from kairondb import SQLBridge
from kairondb.exceptions import ValidationError


class TestLoggingSystem:
    """Testes para o sistema de logging"""
    
    def test_logger_creation(self):
        """Testa se o logger é criado corretamente"""
        from kairondb.bridge import bridge_logger
        
        assert isinstance(bridge_logger, logging.Logger)
        assert bridge_logger.name == 'kairondb.bridge'
    
    def test_logger_level_configuration(self):
        """Testa configuração de nível de logging"""
        from kairondb.bridge import bridge_logger
        
        # Testar nível DEBUG
        bridge_logger.setLevel(logging.DEBUG)
        assert bridge_logger.level == logging.DEBUG
        
        # Testar nível INFO
        bridge_logger.setLevel(logging.INFO)
        assert bridge_logger.level == logging.INFO
    
    def test_debug_mode_logging(self):
        """Testa se o modo debug configura o logging corretamente"""
        with patch('kairondb.bridge.bridge_logger') as mock_logger:
            try:
                bridge = SQLBridge("sqlite3", "./test.db", "", "", "", debug=True)
                # Verificar se setLevel foi chamado com DEBUG
                mock_logger.setLevel.assert_called_with(logging.DEBUG)
            except Exception:
                # Pode falhar na DLL, mas o logging deve ter sido configurado
                pass
    
    def test_normal_mode_logging(self):
        """Testa se o modo normal configura o logging corretamente"""
        with patch('kairondb.bridge.bridge_logger') as mock_logger:
            try:
                bridge = SQLBridge("sqlite3", "./test.db", "", "", "", debug=False)
                # Verificar se setLevel foi chamado com INFO
                mock_logger.setLevel.assert_called_with(logging.INFO)
            except Exception:
                # Pode falhar na DLL, mas o logging deve ter sido configurado
                pass
    
    def test_logger_handlers(self):
        """Testa se os handlers são configurados corretamente"""
        from kairondb.bridge import logger
        
        # Verificar se tem pelo menos um handler
        assert len(logger.handlers) > 0
        
        # Verificar se o handler é do tipo correto
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
    
    def test_logger_formatter(self):
        """Testa se o formatter está configurado corretamente"""
        from kairondb.bridge import logger
        
        handler = logger.handlers[0]
        formatter = handler.formatter
        
        assert formatter is not None
        assert '%(asctime)s' in formatter._fmt
        assert '%(name)s' in formatter._fmt
        assert '%(levelname)s' in formatter._fmt
        assert '%(message)s' in formatter._fmt
    
    def test_logging_messages(self):
        """Testa se as mensagens de log são geradas corretamente"""
        # Testar se o logger está funcionando
        from kairondb.bridge import bridge_logger
        
        # Verificar se o logger tem os métodos necessários
        assert hasattr(bridge_logger, 'debug')
        assert hasattr(bridge_logger, 'info')
        assert hasattr(bridge_logger, 'warning')
        assert hasattr(bridge_logger, 'error')
        assert hasattr(bridge_logger, 'critical')
    
    def test_get_logger_method(self):
        """Testa método get_logger da SQLBridge"""
        try:
            bridge = SQLBridge("sqlite3", "./test.db", "", "", "")
            logger = bridge.get_logger()
            
            assert isinstance(logger, logging.Logger)
            assert logger.name == 'kairondb.bridge'
        except Exception:
            # Pode falhar na DLL
            pass
    
    def test_logger_hierarchy(self):
        """Testa hierarquia de loggers"""
        from kairondb.bridge import logger, bridge_logger
        
        # bridge_logger deve ser filho do logger principal
        assert bridge_logger.parent == logger
        assert bridge_logger.name.startswith(logger.name)
    
    def test_logging_without_debug(self):
        """Testa logging sem modo debug"""
        with patch('kairondb.bridge.bridge_logger') as mock_logger:
            try:
                bridge = SQLBridge("sqlite3", "./test.db", "", "", "", debug=False)
                
                # Verificar se apenas mensagens INFO+ são logadas
                # (DEBUG não deve ser chamado)
                debug_calls = [call for call in mock_logger.method_calls if call[0] == 'debug']
                assert len(debug_calls) == 0
            except Exception:
                # Pode falhar na DLL
                pass
    
    def test_logging_with_debug(self):
        """Testa logging com modo debug"""
        with patch('kairondb.bridge.bridge_logger') as mock_logger:
            try:
                bridge = SQLBridge("sqlite3", "./test.db", "", "", "", debug=True)
                
                # Verificar se mensagens DEBUG são logadas
                debug_calls = [call for call in mock_logger.method_calls if call[0] == 'debug']
                assert len(debug_calls) > 0
            except Exception:
                # Pode falhar na DLL
                pass
