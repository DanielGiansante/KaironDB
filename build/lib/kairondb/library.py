# kairondb/__init__.py

import os
import json
from ctypes import cdll, c_char_p, c_void_p

# 1. Definimos o caminho do pacote PRIMEIRO.
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Agora definimos as classes.

class SQLBridge:
    def __init__(self, driver: str, server: str, db_name: str, user: str, password: str, lib_path: str = None):
        """
        Inicializa a conexão e carrega a DLL a partir da pasta do pacote.
        """
        self.conn_params = {
            "driver": driver,
            "server": server,
            "name": db_name,
            "user": user,
            "password": password
        }
        self.conn_params_json = json.dumps(self.conn_params).encode('utf-8')

        if lib_path is None:
            lib_name = 'sqlbridge.dll' if os.name == 'nt' else 'sqlbridge.so'
            lib_path = os.path.join(PACKAGE_DIR, lib_name)

        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"A biblioteca da DLL não foi encontrada: {lib_path}")

        self.lib = cdll.LoadLibrary(lib_path)
        self._setup_signatures()

    def _setup_signatures(self):
        """Define as assinaturas das funções exportadas pela DLL."""
        self.lib.ExecuteSQL.argtypes = [c_char_p, c_char_p, c_char_p]
        self.lib.ExecuteSQL.restype = c_char_p
        
        self.lib.BeginTransaction.argtypes = [c_char_p]
        self.lib.BeginTransaction.restype = c_char_p

        self.lib.CommitTransaction.argtypes = [c_char_p]
        self.lib.CommitTransaction.restype = c_char_p

        self.lib.RollbackTransaction.argtypes = [c_char_p]
        self.lib.RollbackTransaction.restype = c_char_p

    def _execute(self, req: dict, tx_id: str = "") -> dict:
        """
        Envia o JSON para a DLL e retorna o resultado decodificado.
        Aceita um tx_id opcional para operações transacionais.
        """
        req_json = json.dumps(req).encode('utf-8')
        tx_id_encoded = tx_id.encode('utf-8')

        raw_result = self.lib.ExecuteSQL(req_json, self.conn_params_json, tx_id_encoded)
        
        result_str = raw_result.decode('utf-8')
        try:
            return json.loads(result_str)
        except json.JSONDecodeError:
            return {"error": "Resposta inválida da DLL", "raw_response": result_str}

    def select(self, table: str, fields=None, where=None, joins=None):
        if not fields:
            fields = ['*']
        req = {
            "operation": "select", "table": table, "fields": fields,
            "where": where or {}, "joins": joins or []
        }
        return self._execute(req)

    def exec(self, sql: str, params=None, expect_result=False):
        req = {
            "operation": "exec", "sql": sql, "params": params or [], "expect_result": expect_result
        }
        return self._execute(req)
        
    def transaction(self):
        """Retorna um gerenciador de contexto para uma nova transação."""
        return Transaction(self)

    # Métodos privados para serem usados pelo gerenciador de transação
    def _begin_transaction(self) -> str:
        response_raw = self.lib.BeginTransaction(self.conn_params_json)
        response_str = response_raw.decode('utf-8')
        # CORREÇÃO: Verifica se a resposta é um erro JSON
        if response_str.strip().startswith('{'):
            error_data = json.loads(response_str)
            raise ConnectionError(f"Falha ao iniciar transação na DLL: {error_data.get('error', response_str)}")
        return response_str

    def _commit_transaction(self, tx_id: str):
        response_raw = self.lib.CommitTransaction(tx_id.encode('utf-8'))
        response_str = response_raw.decode('utf-8')
        data = json.loads(response_str)
        if 'error' in data:
            raise Exception(f"Falha ao commitar transação: {data['error']}")

    def _rollback_transaction(self, tx_id: str):
        response_raw = self.lib.RollbackTransaction(tx_id.encode('utf-8'))
        response_str = response_raw.decode('utf-8')
        data = json.loads(response_str)
        if 'error' in data:
            # Em um rollback (que já está tratando um erro), apenas avisamos.
            print(f"AVISO: Falha adicional ao fazer rollback da transação: {data['error']}")


class Transaction:
    """Gerenciador de contexto para operações transacionais."""
    def __init__(self, bridge: SQLBridge):
        self._bridge = bridge
        self.tx_id = None
        self.tx_bridge = None

    def __enter__(self):
        self.tx_id = self._bridge._begin_transaction()
        self.tx_bridge = TransactionalBridge(self._bridge, self.tx_id)
        return self.tx_bridge

    def __exit__(self, exc_type, exc_value, traceback):
        if self.tx_id:
            if exc_type is not None:
                self._bridge._rollback_transaction(self.tx_id)
            else:
                self._bridge._commit_transaction(self.tx_id)


class TransactionalBridge:
    """Um wrapper em volta do SQLBridge que força o uso de um tx_id."""
    def __init__(self, original_bridge: SQLBridge, tx_id: str):
        self._bridge = original_bridge
        self._tx_id = tx_id
    
    def exec(self, sql: str, params=None, expect_result=False):
        req = {
            "operation": "exec", "sql": sql, "params": params or [], "expect_result": expect_result
        }
        return self._bridge._execute(req, self._tx_id)
        
    # CORREÇÃO: Adicionado o método select para ser usado dentro de transações
    def select(self, table: str, fields=None, where=None, joins=None):
        if not fields:
            fields = ['*']
        req = {
            "operation": "select", "table": table, "fields": fields,
            "where": where or {}, "joins": joins or []
        }
        return self._bridge._execute(req, self._tx_id)

class Model:
    def __init__(self, bridge, table: str):
        self.bridge = bridge
        self.table = table

    def select(self, fields=None, where=None, joins=None):
        # CORREÇÃO: A checagem de erro foi removida, pois agora o select funciona em transações
        return self.bridge.select(self.table, fields, where, joins)

    def exec(self, sql, params=None, expect_result=False):
        return self.bridge.exec(sql, params, expect_result)

    def insert(self, data: dict):
        # NOTA: O placeholder '?' pode precisar ser adaptado para o SQL Server.
        # A melhor forma é usar o método .exec() diretamente com a sintaxe correta (@p1, @p2).
        cols = ', '.join(data.keys())
        values_placeholders = ', '.join([f'@p{i+1}' for i in range(len(data))])
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({values_placeholders})"
        params = list(data.values())
        return self.exec(sql, params)

    def update(self, data: dict, where: dict):
        set_clause_parts = []
        param_index = 1
        params = []
        for key, value in data.items():
            set_clause_parts.append(f"{key} = @p{param_index}")
            params.append(value)
            param_index += 1
            
        where_clause_parts = []
        for key, value in where.items():
            where_clause_parts.append(f"{key} = @p{param_index}")
            params.append(value)
            param_index += 1

        set_clause = ', '.join(set_clause_parts)
        where_clause = ' AND '.join(where_clause_parts)
        sql = f"UPDATE {self.table} SET {set_clause} WHERE {where_clause}"
        return self.exec(sql, params)

    def delete(self, where: dict):
        where_clause_parts = []
        param_index = 1
        params = []
        for key, value in where.items():
            where_clause_parts.append(f"{key} = @p{param_index}")
            params.append(value)
            param_index += 1
        
        where_clause = ' AND '.join(where_clause_parts)
        sql = f"DELETE FROM {self.table} WHERE {where_clause}"
        return self.exec(sql, params)

