"""
Sistema de Migrations para KaironDB
"""

import os
import json
import time
import hashlib
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from .typing import Migration, Schema, Index, Constraint
from .exceptions import ConfigurationError, QueryError, ConnectionError


class MigrationStatus(Enum):
    """Status de uma migração."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationRecord:
    """Registro de uma migração no banco."""
    version: str
    name: str
    status: MigrationStatus
    applied_at: Optional[float] = None
    rolled_back_at: Optional[float] = None
    error_message: Optional[str] = None
    checksum: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


class MigrationManager:
    """Gerenciador de migrations do banco de dados."""
    
    def __init__(
        self,
        migrations_dir: str = "migrations",
        table_name: str = "kairondb_migrations",
        logger: Optional[logging.Logger] = None
    ):
        self.migrations_dir = Path(migrations_dir)
        self.table_name = table_name
        self.logger = logger or logging.getLogger('kairondb.migrations')
        
        # Estado
        self._migrations: Dict[str, Migration] = {}
        self._applied_migrations: Dict[str, MigrationRecord] = {}
        self._bridge = None
        
        # Callbacks
        self._on_migration_start: Optional[Callable[[str], None]] = None
        self._on_migration_complete: Optional[Callable[[str], None]] = None
        self._on_migration_fail: Optional[Callable[[str, str], None]] = None
        self._on_migration_rollback: Optional[Callable[[str], None]] = None
    
    def set_bridge(self, bridge) -> None:
        """Define a bridge para execução das migrations."""
        self._bridge = bridge
    
    def set_callbacks(
        self,
        on_migration_start: Optional[Callable[[str], None]] = None,
        on_migration_complete: Optional[Callable[[str], None]] = None,
        on_migration_fail: Optional[Callable[[str, str], None]] = None,
        on_migration_rollback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Define callbacks para eventos de migration."""
        self._on_migration_start = on_migration_start
        self._on_migration_complete = on_migration_complete
        self._on_migration_fail = on_migration_fail
        self._on_migration_rollback = on_migration_rollback
    
    async def initialize(self) -> None:
        """Inicializa o sistema de migrations."""
        if not self._bridge:
            raise ConfigurationError("Bridge não definida")
        
        # Criar diretório de migrations se não existir
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Criar tabela de migrations se não existir
        await self._create_migrations_table()
        
        # Carregar migrations aplicadas
        await self._load_applied_migrations()
        
        # Carregar migrations do diretório
        await self._load_migrations_from_dir()
        
        self.logger.info(f"Sistema de migrations inicializado com {len(self._migrations)} migrations")
    
    async def _create_migrations_table(self) -> None:
        """Cria a tabela de migrations se não existir."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            version VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL,
            applied_at TIMESTAMP NULL,
            rolled_back_at TIMESTAMP NULL,
            error_message TEXT NULL,
            checksum VARCHAR(64) NULL,
            dependencies TEXT NULL
        )
        """
        
        try:
            await self._bridge.exec(create_table_sql)
            self.logger.debug("Tabela de migrations criada/verificada")
        except Exception as e:
            raise ConfigurationError(f"Falha ao criar tabela de migrations: {e}")
    
    async def _load_applied_migrations(self) -> None:
        """Carrega migrations já aplicadas do banco."""
        try:
            result = await self._bridge.select(
                self.table_name,
                fields=["version", "name", "status", "applied_at", "rolled_back_at", "error_message", "checksum", "dependencies"]
            )
            
            for row in result.get('data', []):
                record = MigrationRecord(
                    version=row['version'],
                    name=row['name'],
                    status=MigrationStatus(row['status']),
                    applied_at=row['applied_at'],
                    rolled_back_at=row['rolled_back_at'],
                    error_message=row['error_message'],
                    checksum=row['checksum'],
                    dependencies=json.loads(row['dependencies'] or '[]')
                )
                self._applied_migrations[record.version] = record
            
            self.logger.debug(f"Carregadas {len(self._applied_migrations)} migrations aplicadas")
        except Exception as e:
            self.logger.warning(f"Erro ao carregar migrations aplicadas: {e}")
    
    async def _load_migrations_from_dir(self) -> None:
        """Carrega migrations do diretório."""
        if not self.migrations_dir.exists():
            return
        
        migration_files = sorted(self.migrations_dir.glob("*.json"))
        
        for file_path in migration_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    migration_data = json.load(f)
                
                migration = Migration(
                    version=migration_data['version'],
                    name=migration_data['name'],
                    up_sql=migration_data['up_sql'],
                    down_sql=migration_data['down_sql'],
                    dependencies=migration_data.get('dependencies', [])
                )
                
                self._migrations[migration['version']] = migration
                self.logger.debug(f"Migration carregada: {migration['version']} - {migration['name']}")
            except Exception as e:
                self.logger.error(f"Erro ao carregar migration {file_path}: {e}")
    
    def create_migration(
        self, 
        name: str, 
        up_sql: str, 
        down_sql: str,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Cria uma nova migration."""
        version = f"{int(time.time())}_{name.lower().replace(' ', '_')}"
        dependencies = dependencies or []
        
        migration = {
            'version': version,
            'name': name,
            'up_sql': up_sql,
            'down_sql': down_sql,
            'dependencies': dependencies
        }
        
        # Salvar arquivo
        file_path = self.migrations_dir / f"{version}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(migration, f, indent=2)
        
        # Adicionar à lista em memória
        self._migrations[version] = migration
        
        self.logger.info(f"Migration criada: {version} - {name}")
        return version
    
    async def get_pending_migrations(self) -> List[str]:
        """Retorna migrations pendentes em ordem de dependência."""
        pending = []
        applied_versions = set(self._applied_migrations.keys())
        
        # Ordenar por versão
        sorted_versions = sorted(self._migrations.keys())
        
        for version in sorted_versions:
            if version in applied_versions:
                continue
            
            migration = self._migrations[version]
            
            # Verificar dependências
            if all(dep in applied_versions for dep in migration['dependencies']):
                pending.append(version)
            else:
                missing_deps = [dep for dep in migration['dependencies'] if dep not in applied_versions]
                self.logger.warning(f"Migration {version} tem dependências não aplicadas: {missing_deps}")
        
        return pending
    
    async def migrate(self, target_version: Optional[str] = None) -> List[str]:
        """Executa migrations pendentes."""
        if not self._bridge:
            raise ConfigurationError("Bridge não definida")
        
        pending = await self.get_pending_migrations()
        
        if target_version:
            # Filtrar até a versão alvo
            target_index = None
            for i, version in enumerate(pending):
                if version == target_version:
                    target_index = i + 1
                    break
            
            if target_index is None:
                raise ConfigurationError(f"Versão alvo {target_version} não encontrada")
            
            pending = pending[:target_index]
        
        applied = []
        
        for version in pending:
            try:
                await self._apply_migration(version)
                applied.append(version)
            except Exception as e:
                self.logger.error(f"Falha ao aplicar migration {version}: {e}")
                raise QueryError(f"Falha na migration {version}: {e}")
        
        return applied
    
    async def _apply_migration(self, version: str) -> None:
        """Aplica uma migration específica."""
        migration = self._migrations[version]
        
        if self._on_migration_start:
            self._on_migration_start(version)
        
        self.logger.info(f"Aplicando migration {version}: {migration['name']}")
        
        # Calcular checksum
        checksum = hashlib.sha256(migration['up_sql'].encode()).hexdigest()
        
        # Registrar início da migration
        await self._record_migration_status(
            version, 
            MigrationStatus.RUNNING, 
            checksum=checksum
        )
        
        try:
            # Executar SQL
            await self._bridge.exec(migration['up_sql'])
            
            # Registrar sucesso
            await self._record_migration_status(
                version, 
                MigrationStatus.COMPLETED,
                applied_at=time.time(),
                checksum=checksum
            )
            
            if self._on_migration_complete:
                self._on_migration_complete(version)
            
            self.logger.info(f"Migration {version} aplicada com sucesso")
        
        except Exception as e:
            error_msg = str(e)
            
            # Registrar falha
            await self._record_migration_status(
                version, 
                MigrationStatus.FAILED,
                error_message=error_msg,
                checksum=checksum
            )
            
            if self._on_migration_fail:
                self._on_migration_fail(version, error_msg)
            
            self.logger.error(f"Migration {version} falhou: {error_msg}")
            raise
    
    async def rollback(self, target_version: Optional[str] = None) -> List[str]:
        """Reverte migrations aplicadas."""
        if not self._bridge:
            raise ConfigurationError("Bridge não definida")
        
        # Obter migrations aplicadas em ordem reversa
        applied_versions = [
            version for version, record in self._applied_migrations.items()
            if record.status == MigrationStatus.COMPLETED
        ]
        applied_versions.sort(reverse=True)
        
        if target_version:
            # Encontrar índice da versão alvo
            target_index = None
            for i, version in enumerate(applied_versions):
                if version == target_version:
                    target_index = i
                    break
            
            if target_index is None:
                raise ConfigurationError(f"Versão alvo {target_version} não encontrada")
            
            applied_versions = applied_versions[:target_index]
        
        rolled_back = []
        
        for version in applied_versions:
            try:
                await self._rollback_migration(version)
                rolled_back.append(version)
            except Exception as e:
                self.logger.error(f"Falha ao reverter migration {version}: {e}")
                raise QueryError(f"Falha no rollback da migration {version}: {e}")
        
        return rolled_back
    
    async def _rollback_migration(self, version: str) -> None:
        """Reverte uma migration específica."""
        migration = self._migrations[version]
        
        if self._on_migration_rollback:
            self._on_migration_rollback(version)
        
        self.logger.info(f"Revertendo migration {version}: {migration['name']}")
        
        try:
            # Executar SQL de rollback
            await self._bridge.exec(migration['down_sql'])
            
            # Registrar rollback
            await self._record_migration_status(
                version, 
                MigrationStatus.ROLLED_BACK,
                rolled_back_at=time.time()
            )
            
            self.logger.info(f"Migration {version} revertida com sucesso")
        
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Rollback da migration {version} falhou: {error_msg}")
            raise
    
    async def _record_migration_status(
        self, 
        version: str, 
        status: MigrationStatus,
        applied_at: Optional[float] = None,
        rolled_back_at: Optional[float] = None,
        error_message: Optional[str] = None,
        checksum: Optional[str] = None
    ) -> None:
        """Registra o status de uma migration no banco."""
        migration = self._migrations[version]
        
        # Preparar dados
        data = {
            'version': version,
            'name': migration['name'],
            'status': status.value,
            'applied_at': applied_at,
            'rolled_back_at': rolled_back_at,
            'error_message': error_message,
            'checksum': checksum,
            'dependencies': json.dumps(migration['dependencies'])
        }
        
        # Verificar se já existe
        existing = await self._bridge.select(
            self.table_name,
            where={'version': version}
        )
        
        if existing.get('data'):
            # Atualizar
            await self._bridge.update(
                self.table_name,
                data=data,
                where={'version': version}
            )
        else:
            # Inserir
            await self._bridge.insert(self.table_name, data=data)
        
        # Atualizar cache local
        record = MigrationRecord(
            version=version,
            name=migration['name'],
            status=status,
            applied_at=applied_at,
            rolled_back_at=rolled_back_at,
            error_message=error_message,
            checksum=checksum,
            dependencies=migration['dependencies']
        )
        self._applied_migrations[version] = record
    
    async def get_migration_status(self, version: str) -> Optional[MigrationStatus]:
        """Retorna o status de uma migration."""
        record = self._applied_migrations.get(version)
        return record.status if record else None
    
    async def get_migration_history(self) -> List[MigrationRecord]:
        """Retorna o histórico de migrations."""
        return list(self._applied_migrations.values())
    
    async def get_schema_info(self) -> Schema:
        """Retorna informações sobre o schema atual."""
        # Esta é uma implementação básica - em um sistema real,
        # você consultaria o banco para obter informações reais do schema
        return {
            'tables': [],
            'indexes': [],
            'constraints': [],
            'views': [],
            'functions': []
        }
    
    def list_migrations(self) -> List[str]:
        """Lista todas as migrations disponíveis."""
        return list(self._migrations.keys())
    
    def get_migration_info(self, version: str) -> Optional[Migration]:
        """Retorna informações sobre uma migration específica."""
        return self._migrations.get(version)
    
    async def validate_migrations(self) -> List[str]:
        """Valida todas as migrations disponíveis."""
        errors = []
        
        for version, migration in self._migrations.items():
            # Verificar se tem SQL válido
            if not migration['up_sql'].strip():
                errors.append(f"Migration {version} não tem SQL de aplicação")
            
            if not migration['down_sql'].strip():
                errors.append(f"Migration {version} não tem SQL de rollback")
            
            # Verificar dependências
            for dep in migration['dependencies']:
                if dep not in self._migrations:
                    errors.append(f"Migration {version} depende de {dep} que não existe")
        
        return errors
    
    async def reset_migrations(self) -> None:
        """Reseta o sistema de migrations (CUIDADO!)."""
        if not self._bridge:
            raise ConfigurationError("Bridge não definida")
        
        self.logger.warning("Resetando sistema de migrations")
        
        # Limpar tabela de migrations
        await self._bridge.delete(self.table_name)
        
        # Limpar cache local
        self._applied_migrations.clear()
        
        self.logger.info("Sistema de migrations resetado")
