import os
import json
import asyncio
import ctypes
import time
import uuid
import traceback
from typing import Optional, Dict, Any
from .query import Q

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CALLBACK_FUNC_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

_active_futures: Dict[str, Any] = {}
_debug_logs = []
_MAX_DEBUG_LOGS = 1000  # Limite de logs para evitar consumo excessivo de memória


class DebugLogger:
    _enabled = False

    @classmethod
    def set_enabled(cls, enabled: bool):
        cls._enabled = enabled

    @staticmethod
    def log(message: str, level: str = "INFO"):
        # CORREÇÃO: Esta é a única alteração. A função agora sai imediatamente
        # se o debug não estiver ativado, impedindo que qualquer log seja impresso.
        if not DebugLogger._enabled:
            return
            
        timestamp = f"[{time.time():.4f}]"
        log_entry = f"{timestamp} {level}: {message}"
        _debug_logs.append(log_entry)
        if len(_debug_logs) > _MAX_DEBUG_LOGS:
            _debug_logs.pop(0)
        print(log_entry)


def _on_query_complete_global(result_ptr, request_id_ptr):
    try:
        DebugLogger.log("Callback global iniciada", "DEBUG")
        request_id = ctypes.cast(request_id_ptr, ctypes.c_char_p).value.decode('utf-8')
        DebugLogger.log(f"Request ID recebido: {request_id}", "DEBUG")
        
        future_tuple = _active_futures.get(request_id)
        if not future_tuple:
            DebugLogger.log(f"Future não encontrado para request_id: {request_id}", "ERROR")
            return
            
        future, bridge_instance, loop = future_tuple
        
        if future.done():
            DebugLogger.log(f"Future já concluído para request_id: {request_id}", "WARNING")
            return

        result_str = ctypes.cast(result_ptr, ctypes.c_char_p).value.decode('utf-8')
        DebugLogger.log(f"Resultado bruto recebido (truncado): {result_str[:200]}", "DEBUG")
        
        try:
            result = json.loads(result_str)
            DebugLogger.log("JSON parseado com sucesso", "DEBUG")
            if not loop.is_closed():
                loop.call_soon_threadsafe(future.set_result, result)
                DebugLogger.log(f"Future resolvido para request_id: {request_id}", "DEBUG")
            else:
                DebugLogger.log("Loop de evento fechado, não é possível resolver o future", "ERROR")
        except json.JSONDecodeError as e:
            error_msg = f"Falha ao decodificar JSON: {str(e)}"
            DebugLogger.log(error_msg, "ERROR")
            if not loop.is_closed():
                loop.call_soon_threadsafe(future.set_exception, e)
    except Exception:
        error_msg = f"ERRO CRÍTICO NA CALLBACK: {traceback.format_exc()}"
        DebugLogger.log(error_msg, "CRITICAL")

_global_callback_c = CALLBACK_FUNC_TYPE(_on_query_complete_global)

class SQLBridge:
    def __init__(self, driver: str, server: str, db_name: str, user: str, password: str, 
                 lib_path: Optional[str] = None, debug: bool = False):
        self.driver = driver
        self.conn_params = {"driver": driver, "server": server, "name": db_name, "user": user, "password": password}
        self.debug = debug
        DebugLogger.set_enabled(debug)
        self.pool_id: Optional[str] = None
        self.lib = self._load_library(lib_path)
        self._setup_signatures()
        self._verify_library_functions()
        self.pool_id = self._create_pool_sync()
        DebugLogger.log(f"SQLBridge inicializada. Pool ID: {self.pool_id}", "INFO")

    def _load_library(self, lib_path: Optional[str]) -> ctypes.CDLL:
        if lib_path is None:
            lib_name = 'sqlbridge.dll' if os.name == 'nt' else 'sqlbridge.so'
            lib_path = os.path.join(PACKAGE_DIR, lib_name)
        DebugLogger.log(f"Tentando carregar biblioteca em: {lib_path}", "DEBUG")
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"Biblioteca não encontrada: {lib_path}")
        try:
            lib = ctypes.cdll.LoadLibrary(lib_path)
            DebugLogger.log(f"Biblioteca carregada com sucesso: {lib._name}", "INFO")
            return lib
        except Exception as e:
            raise RuntimeError(f"Falha ao carregar biblioteca: {str(e)}") from e

    def _setup_signatures(self):
        self.lib.CreatePool.argtypes = [ctypes.c_char_p]; self.lib.CreatePool.restype = ctypes.c_char_p
        self.lib.ClosePool.argtypes = [ctypes.c_char_p]
        self.lib.ExecuteSQL_async.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, CALLBACK_FUNC_TYPE, ctypes.c_char_p]
        if hasattr(self.lib, 'BeginTransaction'):
            self.lib.BeginTransaction.argtypes = [ctypes.c_char_p]; self.lib.BeginTransaction.restype = ctypes.c_char_p
        if hasattr(self.lib, 'CommitTransaction'):
            self.lib.CommitTransaction.argtypes = [ctypes.c_char_p]
        if hasattr(self.lib, 'RollbackTransaction'):
            self.lib.RollbackTransaction.argtypes = [ctypes.c_char_p]
        if hasattr(self.lib, 'FreeCString'):
            self.lib.FreeCString.argtypes = [ctypes.c_char_p]

    def _verify_library_functions(self):
        required_functions = ['CreatePool', 'ClosePool', 'ExecuteSQL_async']
        missing = [func for func in required_functions if not hasattr(self.lib, func)]
        if missing:
            raise RuntimeError(f"Funções essenciais faltando na DLL: {', '.join(missing)}")

    def _create_pool_sync(self) -> str:
        params_json = json.dumps(self.conn_params).encode('utf-8')
        pool_id_raw = self.lib.CreatePool(params_json)
        pool_id_str = pool_id_raw.decode('utf-8')
        if pool_id_str.startswith('{'):
            raise ConnectionError(f"Falha ao criar pool: {pool_id_str}")
        return pool_id_str

    async def close(self):
        """Fecha o pool de conexões de forma assíncrona."""
        if self.pool_id:
            try:
                DebugLogger.log(f"Fechando pool {self.pool_id}", "INFO")
                # Se a operação de fechamento for síncrona, remova o await abaixo
                self.lib.ClosePool(self.pool_id.encode('utf-8'))
                self.pool_id = None
                DebugLogger.log("Pool fechado com sucesso", "INFO")
            except Exception as e:
                error_msg = f"Erro ao fechar pool: {str(e)}"
                DebugLogger.log(error_msg, "ERROR")
                raise

    def __del__(self):
        self.close()

    async def _execute_async(self, req: Dict[str, Any], tx_id: str = "") -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        request_id = str(uuid.uuid4())
        
        _active_futures[request_id] = (future, self, loop)
        DebugLogger.log(f"Future criado para request_id: {request_id}", "DEBUG")
        
        try:
            req['driver'] = self.driver
            req_json = json.dumps(req).encode('utf-8')
            pool_id_enc = self.pool_id.encode('utf-8')
            tx_id_enc = tx_id.encode('utf-8') if tx_id else b""
            request_id_enc = request_id.encode('utf-8')
            
            DebugLogger.log(f"Enviando requisição para DLL (req_id: {request_id}, op: {req.get('operation')})", "DEBUG")
            self.lib.ExecuteSQL_async(pool_id_enc, req_json, tx_id_enc, _global_callback_c, request_id_enc)
            
            try:
                result = await asyncio.wait_for(future, timeout=30.0)
                DebugLogger.log(f"Requisição concluída (req_id: {request_id})", "DEBUG")
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout na requisição {request_id}") from None
        finally:
            _active_futures.pop(request_id, None)
            DebugLogger.log(f"Future removido para request_id: {request_id}", "DEBUG")

    def _process_where(self, where):
        if where is None: return {}
        if isinstance(where, Q): return where.to_dict()
        if isinstance(where, dict): return {'connector': 'AND', 'children': [where]}
        raise TypeError(f"Argumento 'where' deve ser um dict ou objeto Q.")

    async def select(self, table: str, fields=None, where=None, joins=None):
        req = {"operation": "select", "table": table, "fields": fields or ['*'], "where_q": self._process_where(where), "joins": joins or []}
        return await self._execute_async(req)
        
    async def insert(self, table: str, data: Dict[str, Any]):
        req = {"operation": "insert", "table": table, "data": data}
        return await self._execute_async(req)
        
    async def update(self, table: str, data: Dict[str, Any], where=None):
        req = {"operation": "update", "table": table, "data": data, "where_q": self._process_where(where)}
        return await self._execute_async(req)

    async def delete(self, table: str, where=None):
        req = {"operation": "delete", "table": table, "where_q": self._process_where(where)}
        return await self._execute_async(req)
        
    async def exec(self, sql: str, params=None, expect_result: bool = False):
        req = {"operation": "exec", "sql": sql, "params": params or [], "expect_result": expect_result}
        return await self._execute_async(req)

    def transaction(self):
        return Transaction(self)

    def get_debug_logs(self) -> list:
        return _debug_logs.copy()

class Transaction:
    def __init__(self, bridge: SQLBridge):
        self._bridge = bridge
        self.tx_id: Optional[str] = None
        self.tx_bridge: Optional['TransactionalBridge'] = None

    async def __aenter__(self) -> 'TransactionalBridge':
        if not hasattr(self._bridge.lib, 'BeginTransaction'):
            raise RuntimeError("DLL não suporta transações")
        response_raw = self._bridge.lib.BeginTransaction(self._bridge.pool_id.encode('utf-8'))
        self.tx_id = response_raw.decode('utf-8')
        if self.tx_id.startswith('{'):
            raise ConnectionError(f"Falha ao iniciar transação: {self.tx_id}")
        DebugLogger.log(f"Transação iniciada com ID: {self.tx_id}", "INFO")
        self.tx_bridge = TransactionalBridge(self._bridge, self.tx_id)
        return self.tx_bridge

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.tx_id: return
        try:
            if exc_type is not None:
                DebugLogger.log(f"Rollback da transação {self.tx_id} devido a erro", "WARNING")
                if hasattr(self._bridge.lib, 'RollbackTransaction'):
                    self._bridge.lib.RollbackTransaction(self.tx_id.encode('utf-8'))
            else:
                DebugLogger.log(f"Commit da transação {self.tx_id}", "INFO")
                if hasattr(self._bridge.lib, 'CommitTransaction'):
                    self._bridge.lib.CommitTransaction(self.tx_id.encode('utf-8'))
        finally:
            self.tx_id = None

class TransactionalBridge:
    def __init__(self, original_bridge: SQLBridge, tx_id: str):
        self._bridge = original_bridge
        self._tx_id = tx_id
        DebugLogger.log(f"Bridge transacional criada para tx_id: {tx_id}", "DEBUG")

    async def select(self, table: str, fields=None, where=None, joins=None):
        return await self._bridge._execute_async({"operation": "select", "table": table, "fields": fields or ['*'], "where_q": self._bridge._process_where(where), "joins": joins or []}, self._tx_id)
    async def update(self, table: str, data: Dict[str, Any], where=None):
        return await self._bridge._execute_async({"operation": "update", "table": table, "data": data, "where_q": self._bridge._process_where(where)}, self._tx_id)
    async def delete(self, table: str, where=None):
        return await self._bridge._execute_async({"operation": "delete", "table": table, "where_q": self._bridge._process_where(where)}, self._tx_id)
    async def exec(self, sql: str, params=None, expect_result=False):
        return await self._bridge._execute_async({"operation": "exec", "sql": sql, "params": params or [], "expect_result": expect_result}, self._tx_id)
