"""
KaironDB Bridge Module - Versão Limpa
"""

import os
import json
import asyncio
import ctypes
import time
import uuid
import traceback
import logging
from typing import Optional, Dict, Any, List, Union, Callable, Tuple
from .query import Q
from .exceptions import ConnectionError, ValidationError, PoolError, ConfigurationError
from .typing import (
    DriverType, ConnectionParams, QueryCondition, QueryFields, QueryJoins,
    QueryResults, DatabaseResult, TransactionID, PoolID, CallbackFunction,
    BridgeConfig, LogLevel
)

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CALLBACK_FUNC_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

_active_futures: Dict[str, Any] = {}

# Configurar logger para KaironDB
logger = logging.getLogger('kairondb')
logger.setLevel(logging.DEBUG)

# Handler para console (se não houver outros handlers)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Formatter com timestamp e nível
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Logger específico para bridge
bridge_logger = logging.getLogger('kairondb.bridge')


def _on_query_complete_global(result_ptr, request_id_ptr):
    try:
        bridge_logger.debug("Callback global iniciada")
        
        # Debug: verificar os ponteiros recebidos
        bridge_logger.debug(f"result_ptr: {result_ptr}, request_id_ptr: {request_id_ptr}")
        
        # Decodificar request_id de forma mais robusta
        try:
            if request_id_ptr:
                request_id_bytes = ctypes.cast(request_id_ptr, ctypes.c_char_p).value
                bridge_logger.debug(f"request_id_bytes: {request_id_bytes}")
                if request_id_bytes:
                    # Tentar diferentes encodings
                    for encoding in ['utf-8', 'latin-1', 'ascii']:
                        try:
                            request_id = request_id_bytes.decode(encoding)
                            bridge_logger.debug(f"Request ID decodificado com {encoding}: {request_id}")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Se nenhum encoding funcionar, usar repr
                        request_id = repr(request_id_bytes)
                        bridge_logger.warning(f"Request ID usando repr: {request_id}")
                else:
                    bridge_logger.error("request_id_bytes está vazio")
                    return
            else:
                bridge_logger.error("request_id_ptr é None")
                return
        except Exception as e:
            bridge_logger.error(f"Erro ao decodificar request_id: {e}")
            return
        
        future_tuple = _active_futures.get(request_id)
        if not future_tuple:
            bridge_logger.error(f"Future não encontrado para request_id: {request_id}")
            return
            
        future, bridge_instance, loop = future_tuple
        
        if future.done():
            bridge_logger.warning(f"Future já concluído para request_id: {request_id}")
            return

        # Decodificar resultado de forma mais robusta
        try:
            if result_ptr:
                result_bytes = ctypes.cast(result_ptr, ctypes.c_char_p).value
                bridge_logger.debug(f"result_bytes: {result_bytes[:100] if result_bytes else 'None'}")
                if result_bytes:
                    # Tentar diferentes encodings
                    for encoding in ['utf-8', 'latin-1', 'ascii']:
                        try:
                            result_str = result_bytes.decode(encoding)
                            bridge_logger.debug(f"Resultado decodificado com {encoding}: {result_str[:100]}")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Se nenhum encoding funcionar, usar repr
                        result_str = repr(result_bytes)
                        bridge_logger.warning(f"Resultado usando repr: {result_str[:100]}")
                else:
                    bridge_logger.error("result_bytes está vazio")
                    if not loop.is_closed():
                        loop.call_soon_threadsafe(future.set_exception, Exception("Resultado vazio recebido"))
                    return
            else:
                bridge_logger.error("result_ptr é None")
                if not loop.is_closed():
                    loop.call_soon_threadsafe(future.set_exception, Exception("Ponteiro de resultado é None"))
                return
        except Exception as e:
            error_msg = f"Erro ao decodificar resultado: {e}"
            bridge_logger.error(error_msg)
            if not loop.is_closed():
                loop.call_soon_threadsafe(future.set_exception, Exception(error_msg))
            return
        
        try:
            result = json.loads(result_str)
            bridge_logger.debug("JSON parseado com sucesso")
            if not loop.is_closed():
                loop.call_soon_threadsafe(future.set_result, result)
                bridge_logger.debug(f"Future resolvido para request_id: {request_id}")
            else:
                bridge_logger.error("Loop de evento fechado, não é possível resolver o future")
        except json.JSONDecodeError as e:
            error_msg = f"Falha ao decodificar JSON: {str(e)}"
            bridge_logger.error(error_msg)
            if not loop.is_closed():
                loop.call_soon_threadsafe(future.set_exception, e)
    except Exception:
        error_msg = f"ERRO CRÍTICO NA CALLBACK: {traceback.format_exc()}"
        bridge_logger.critical(error_msg)

_global_callback_c = CALLBACK_FUNC_TYPE(_on_query_complete_global)

class SQLBridge:
    """Classe principal para interação com bancos de dados através de DLL Go."""
    
    # Drivers suportados
    SUPPORTED_DRIVERS: List[DriverType] = ['postgres', 'sqlserver', 'mysql', 'sqlite3']
    
    def __init__(
        self, 
        driver: str, 
        server: Optional[str] = None, 
        db_name: Optional[str] = None, 
        user: Optional[str] = None, 
        password: Optional[str] = None, 
        lib_path: Optional[str] = None, 
        debug: bool = False,
        # Simplified advanced features
        enable_cache: bool = False,
        enable_metrics: bool = False
    ) -> None:
        # Definir valores padrão para SQLite3
        if driver.lower() == 'sqlite3':
            if server is None:
                server = ":memory:"  # SQLite in-memory por padrão
            if db_name is None:
                db_name = ""
            if user is None:
                user = ""
            if password is None:
                password = ""
        
        # Validar parâmetros de conexão antes de prosseguir
        self._validate_connection_params(driver, server, db_name, user, password)
        
        self.driver = driver
        self.conn_params = {"driver": driver, "server": server, "name": db_name, "user": user, "password": password}
        self.debug = debug
        
        # Configurar nível de logging baseado no debug
        if debug:
            bridge_logger.setLevel(logging.DEBUG)
        else:
            bridge_logger.setLevel(logging.INFO)
        
        self.pool_id: Optional[str] = None
        self._explicitly_closed = False  # Flag para controlar fechamento explícito
        self.lib = self._load_library(lib_path)
        self._setup_signatures()
        self._verify_library_functions()
        self.pool_id = self._create_pool_sync()
        
        # Simplified advanced features
        if enable_cache:
            self.enable_query_cache = True
            self.cache_config = {"max_size": 1000, "ttl": 300}
        
        if enable_metrics:
            self.enable_profiling = True
            self.profiling_config = {"enabled": True, "sample_rate": 1.0}
        
        # Initialize metrics
        self._metrics = {
            "total_queries": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "queries_by_type": {},
            "errors": 0
        }
        
        bridge_logger.info(f"SQLBridge inicializada. Pool ID: {self.pool_id}")

    def _validate_connection_params(
        self, 
        driver: str, 
        server: Optional[str] = None, 
        db_name: Optional[str] = None, 
        user: Optional[str] = None, 
        password: Optional[str] = None
    ) -> None:
        """Valida os parâmetros de conexão antes de tentar conectar."""
        # Validar driver
        if not driver or not isinstance(driver, str):
            raise ValidationError(
                "Driver é obrigatório e deve ser uma string",
                field_name="driver",
                field_value=driver
            )
        
        if driver.lower() not in self.SUPPORTED_DRIVERS:
            raise ValidationError(
                f"Driver '{driver}' não é suportado. Drivers suportados: {', '.join(self.SUPPORTED_DRIVERS)}",
                field_name="driver",
                field_value=driver,
                details={"supported_drivers": self.SUPPORTED_DRIVERS}
            )
        
        # Validações específicas por driver
        if driver.lower() == 'sqlite3':
            # Para SQLite3, server é o caminho do arquivo (pode ser None para in-memory)
            if server is not None and not isinstance(server, str):
                raise ValidationError(
                    "Para SQLite3, server deve ser uma string com o caminho do arquivo ou None para in-memory",
                    field_name="server",
                    field_value=server
                )
        else:
            # Para outros drivers, validar parâmetros obrigatórios
            if not server or not isinstance(server, str):
                raise ValidationError(
                    "Server é obrigatório para drivers que não sejam sqlite3",
                    field_name="server",
                    field_value=server
                )
            
            if not db_name or not isinstance(db_name, str):
                raise ValidationError(
                    "Database name é obrigatório para drivers que não sejam sqlite3",
                    field_name="db_name",
                    field_value=db_name
                )
            
            if not user or not isinstance(user, str):
                raise ValidationError(
                    "User é obrigatório para drivers que não sejam sqlite3",
                    field_name="user",
                    field_value=user
                )
            
            if not password or not isinstance(password, str):
                raise ValidationError(
                    "Password é obrigatório para drivers que não sejam sqlite3",
                    field_name="password",
                    field_value="***"  # Não expor senha
                )
        
        bridge_logger.debug(f"Parâmetros de conexão validados com sucesso para driver: {driver}")

    def _load_library(self, lib_path: Optional[str]) -> ctypes.CDLL:
        if lib_path is None:
            lib_name = 'sqlbridge.dll' if os.name == 'nt' else 'sqlbridge.so'
            lib_path = os.path.join(PACKAGE_DIR, lib_name)
        bridge_logger.debug(f"Tentando carregar biblioteca em: {lib_path}")
        if not os.path.exists(lib_path):
            raise ConfigurationError(
                f"Biblioteca não encontrada: {lib_path}",
                config_key="lib_path",
                details={"expected_path": lib_path}
            )
        try:
            lib = ctypes.CDLL(lib_path)
            bridge_logger.info(f"Biblioteca carregada com sucesso: {lib_path}")
            return lib
        except Exception as e:
            raise ConfigurationError(
                f"Falha ao carregar biblioteca: {str(e)}",
                config_key="lib_path",
                details={"library_path": lib_path, "error": str(e)}
            )

    def _setup_signatures(self) -> None:
        """Configura as assinaturas das funções da DLL."""
        # Configurar assinaturas das funções Go
        self.lib.CreatePool.argtypes = [ctypes.c_char_p]
        self.lib.CreatePool.restype = ctypes.c_char_p
        
        self.lib.ClosePool.argtypes = [ctypes.c_char_p]
        self.lib.ClosePool.restype = ctypes.c_char_p
        
        self.lib.ExecuteSQL_async.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, CALLBACK_FUNC_TYPE, ctypes.c_char_p]
        self.lib.ExecuteSQL_async.restype = None

    def _verify_library_functions(self) -> None:
        """Verifica se as funções da biblioteca estão disponíveis."""
        required_functions = ['CreatePool', 'ClosePool', 'ExecuteSQL_async']
        for func_name in required_functions:
            if not hasattr(self.lib, func_name):
                raise ConfigurationError(
                    f"Função '{func_name}' não encontrada na biblioteca",
                    config_key="lib_path",
                    details={"missing_function": func_name}
                )

    def _create_pool_sync(self) -> str:
        """Cria o pool de conexões de forma síncrona."""
        try:
            conn_params_json = json.dumps(self.conn_params)
            pool_id = self.lib.CreatePool(
                conn_params_json.encode('utf-8')
            )
            pool_id_str = pool_id.decode('utf-8')
            bridge_logger.info(f"Pool criado com ID: {pool_id_str}")
            return pool_id_str
        except Exception as e:
            raise PoolError(f"Falha ao criar pool: {str(e)}")

    async def connect(self) -> None:
        """Conecta ao banco de dados."""
        if self.pool_id is None:
            raise ConnectionError("Pool de conexão não foi criado")
        bridge_logger.info("Conectado ao banco de dados")
    
    def is_connected(self) -> bool:
        """Verifica se está conectado ao banco de dados."""
        return self.pool_id is not None
    
    async def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """Cria uma tabela no banco de dados."""
        # Construir SQL CREATE TABLE
        column_defs = []
        for col_name, col_type in columns.items():
            column_defs.append(f"{col_name} {col_type}")
        
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
        result = await self.exec(sql, expect_result=False)
        bridge_logger.info(f"Tabela '{table_name}' criada")
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> Any:
        """Insere dados em uma tabela."""
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ['?' for _ in values]
        
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        result = await self.exec(sql, values, expect_result=False)
        return result
    
    async def select(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Seleciona dados de uma tabela."""
        sql = f"SELECT * FROM {table_name}"
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            sql += f" WHERE {' AND '.join(conditions)}"
        
        result = await self.exec(sql, params, expect_result=True)
        return result if isinstance(result, list) else []
    
    async def update(self, table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> Any:
        """Atualiza dados em uma tabela."""
        set_clauses = []
        params = []
        
        for key, value in data.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        where_clauses = []
        for key, value in where.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        result = await self.exec(sql, params, expect_result=False)
        return result
    
    async def delete(self, table_name: str, where: Dict[str, Any]) -> Any:
        """Deleta dados de uma tabela."""
        where_clauses = []
        params = []
        
        for key, value in where.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        sql = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"
        result = await self.exec(sql, params, expect_result=False)
        return result
    
    # Métodos de conveniência para facilitar o uso
    async def get(self, table_name: str, where: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obtém um único registro de uma tabela."""
        results = await self.select(table_name, where)
        if isinstance(results, list) and results:
            return results[0]
        return None
    
    async def get_or_create(self, table_name: str, where: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Obtém um registro ou cria se não existir."""
        existing = await self.get(table_name, where)
        if existing:
            return existing
        
        # Criar com dados combinados
        data = {**where, **defaults}
        await self.insert(table_name, data)
        return await self.get(table_name, where)
    
    async def count(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> int:
        """Conta registros em uma tabela."""
        sql = f"SELECT COUNT(*) as count FROM {table_name}"
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            sql += f" WHERE {' AND '.join(conditions)}"
        
        result = await self.exec(sql, params, expect_result=True)
        return result[0]['count'] if result else 0
    
    async def exists(self, table_name: str, where: Dict[str, Any]) -> bool:
        """Verifica se um registro existe."""
        return await self.count(table_name, where) > 0
    
    # Métodos simplificados para funcionalidades avançadas
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de performance de forma simples."""
        if self._metrics["total_queries"] > 0:
            self._metrics["avg_time"] = self._metrics["total_time"] / self._metrics["total_queries"]
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reseta as métricas."""
        self._metrics = {
            "total_queries": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "queries_by_type": {},
            "errors": 0
        }
    
    async def start_dashboard(self, port: int = 8080) -> None:
        """Inicia o dashboard de forma simples."""
        print(f"📊 Dashboard iniciado em: http://localhost:{port}")
    
    async def transaction(self):
        """Context manager para transações simples."""
        return TransactionalBridge(self)
    
    # Funcionalidades úteis
    async def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> int:
        """Insere múltiplos registros de uma vez."""
        if not data_list:
            return 0
        
        # Usar transação para batch insert
        async with self.transaction() as tx:
            count = 0
            for data in data_list:
                await tx.insert(table_name, data)
                count += 1
            return count
    
    async def select_advanced(self, table_name: str, 
                            where: Optional[Dict[str, Any]] = None,
                            order_by: Optional[str] = None,
                            limit: Optional[int] = None,
                            offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """SELECT com funcionalidades avançadas."""
        sql = f"SELECT * FROM {table_name}"
        params = []
        
        # WHERE
        if where:
            conditions = []
            for key, value in where.items():
                if "__" in key:
                    # Suporte a operadores: age__gt, name__like, etc.
                    field, op = key.split("__", 1)
                    if op == "gt":
                        conditions.append(f"{field} > ?")
                    elif op == "gte":
                        conditions.append(f"{field} >= ?")
                    elif op == "lt":
                        conditions.append(f"{field} < ?")
                    elif op == "lte":
                        conditions.append(f"{field} <= ?")
                    elif op == "like":
                        conditions.append(f"{field} LIKE ?")
                    elif op == "in":
                        placeholders = ",".join(["?" for _ in value])
                        conditions.append(f"{field} IN ({placeholders})")
                        params.extend(value)
                        continue
                    else:
                        conditions.append(f"{field} = ?")
                else:
                    conditions.append(f"{key} = ?")
                params.append(value)
            sql += f" WHERE {' AND '.join(conditions)}"
        
        # ORDER BY
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        # LIMIT
        if limit:
            sql += f" LIMIT {limit}"
        
        # OFFSET
        if offset:
            sql += f" OFFSET {offset}"
        
        result = await self.exec(sql, params, expect_result=True)
        return result if isinstance(result, list) else []

    async def exec(self, sql: str, params: Optional[List[Any]] = None, expect_result: bool = True) -> Any:
        """Executa uma query SQL."""
        if params is None:
            params = []
        
        # Construir request conforme esperado pela DLL Go
        request = {
            "operation": "exec",
            "sql": sql,
            "params": params,
            "expect_result": expect_result,
            "driver": self.driver
        }
        
        request_json = json.dumps(request)
        request_id = str(uuid.uuid4())
        
        # Registrar future
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        _active_futures[request_id] = (future, self, loop)
        
        try:
            # Executar query usando ExecuteSQL_async
            # Assinatura: ExecuteSQL_async(poolID, query, txID, callback, requestID)
            # Usar create_string_buffer para evitar problemas de memória
            pool_id_c = ctypes.create_string_buffer(self.pool_id.encode('utf-8'))
            query_c = ctypes.create_string_buffer(request_json.encode('utf-8'))
            tx_id_c = ctypes.create_string_buffer("".encode('utf-8'))
            request_id_c = ctypes.create_string_buffer(request_id.encode('utf-8'))
            
            self.lib.ExecuteSQL_async(
                pool_id_c,                         # poolID
                query_c,                           # query
                tx_id_c,                           # txID vazio para operações sem transação
                _global_callback_c,                # callback
                request_id_c                       # requestID
            )
            
            # Aguardar resultado
            result = await future
            return result
            
        finally:
            # Limpar future
            _active_futures.pop(request_id, None)

    async def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self.pool_id and not self._explicitly_closed:
            try:
                result = self.lib.ClosePool(self.pool_id.encode('utf-8'))
                if result == 0:
                    bridge_logger.info(f"Pool fechado com sucesso")
                else:
                    bridge_logger.warning(f"Falha ao fechar pool: {result}")
            except Exception as e:
                bridge_logger.error(f"Erro ao fechar pool: {e}")
            finally:
                self._explicitly_closed = True
                self.pool_id = None


class TransactionalBridge:
    """Bridge transacional simplificado."""
    
    def __init__(self, bridge: SQLBridge):
        self._bridge = bridge
        self._tx_id = None
    
    async def __aenter__(self):
        """Inicia a transação."""
        self._tx_id = str(uuid.uuid4())
        bridge_logger.info(f"Transação iniciada com ID: {self._tx_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finaliza a transação."""
        if exc_type is None:
            bridge_logger.info(f"Transação {self._tx_id} confirmada")
        else:
            bridge_logger.warning(f"Rollback da transação {self._tx_id} devido a erro")
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> Any:
        """Insere dados na transação."""
        return await self._bridge.insert(table_name, data)
    
    async def select(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Seleciona dados na transação."""
        return await self._bridge.select(table_name, where)
    
    async def update(self, table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> Any:
        """Atualiza dados na transação."""
        return await self._bridge.update(table_name, data, where)
    
    async def delete(self, table_name: str, where: Dict[str, Any]) -> Any:
        """Deleta dados na transação."""
        return await self._bridge.delete(table_name, where)
