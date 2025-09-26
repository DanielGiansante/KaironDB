# KaironDB Troubleshooting Guide

## Common Issues and Solutions

### 1. Connection Issues

#### Error: "Library not found"
```
ConfigurationError: Library not found: /path/to/sqlbridge.dll
```

**Cause:** KaironDB DLL was not found in the expected directory.

**Solutions:**
1. Check if `sqlbridge.dll` (Windows) or `sqlbridge.so` (Linux/macOS) file is present
2. Check if the file is in the `src/kairondb/` directory
3. For development, ensure the DLL was compiled correctly
4. For distribution, check if the DLL is included in the package

**Verification:**
```python
import os
from kairondb import SQLBridge

# Check if DLL exists
dll_path = os.path.join(os.path.dirname(__file__), 'src', 'kairondb', 'sqlbridge.dll')
print(f"DLL exists: {os.path.exists(dll_path)}")
```

#### Error: "Driver not supported"
```
ValidationError: Driver 'oracle' is not supported
```

**Cause:** The specified driver is not in the list of supported drivers.

**Solutions:**
1. Use one of the supported drivers: `postgres`, `sqlserver`, `mysql`, `sqlite3`
2. Check the spelling of the driver name
3. For SQLite, use `sqlite3` (not `sqlite`)

**Supported Drivers:**
```python
from kairondb import SQLBridge

# PostgreSQL
bridge = SQLBridge("postgres", "localhost", "mydb", "user", "pass")

# SQL Server
bridge = SQLBridge("sqlserver", "localhost", "mydb", "user", "pass")

# MySQL
bridge = SQLBridge("mysql", "localhost", "mydb", "user", "pass")

# SQLite
bridge = SQLBridge("sqlite3", "/path/to/database.db", "", "", "")
```

#### Error: "Failed to load library"
```
ConfigurationError: Failed to load library: [Errno 193] %1 is not a valid Win32 application
```

**Cause:** Architecture incompatibility (32-bit vs 64-bit) or corrupted DLL.

**Solutions:**
1. Check if DLL was compiled for correct architecture (x64 for Python 64-bit)
2. Recompile the DLL if necessary
3. Check if there are no missing dependencies (Visual C++ Redistributable)

### 2. Validation Issues

#### Error: "Required field empty"
```
ValidationError: Field 'name' is required
```

**Cause:** Attempt to create a model without filling required fields.

**Solutions:**
1. Check if all required fields are filled
2. Use default values if appropriate
3. Check the model definition

**Example:**
```python
from kairondb import Model, StringField

class User(Model):
    name = StringField(required=True)
    email = StringField(required=True)

# ❌ Error - required field empty
user = User()  # ValidationError

# ✅ Correct - fill required fields
user = User(name="John", email="john@example.com")
```

#### Error: "Invalid field value"
```
ValidationError: Value 'invalid-email' is not a valid email
```

**Cause:** Provided value does not meet field validation criteria.

**Solutions:**
1. Check the format of the provided value
2. Use appropriate validators
3. Handle validation errors properly

**Example:**
```python
from kairondb import EmailField

class User(Model):
    email = EmailField()

# ❌ Error - invalid email
user = User(email="invalid-email")  # ValidationError

# ✅ Correct - valid email
user = User(email="user@example.com")
```

### 3. Performance Issues

#### Slow query performance
**Symptoms:** Queries take too long to execute.

**Solutions:**
1. Use profiling system to identify bottlenecks
2. Enable query caching
3. Use database indexes
4. Optimize SQL queries

**Example with Profiling:**
```python
from kairondb import SQLBridge

# Enable profiling
bridge = SQLBridge(
    driver="postgres",
    server="localhost",
    db_name="mydb",
    user="user",
    password="pass",
    enable_profiling=True
)

# Execute queries
result = await bridge.select("users", ["*"])

# Check metrics
metrics = bridge.get_performance_metrics()
print(f"Average time: {metrics['average_duration']:.4f}s")
```

#### High memory usage
**Symptoms:** Application consumes too much memory.

**Solutions:**
1. Close unused bridges
2. Limit cache size
3. Use lazy loading for large data
4. Monitor memory metrics

**Example:**
```python
# Always close bridges
try:
    bridge = SQLBridge(...)
    # use bridge
finally:
    await bridge.close()

# Configure limited cache
bridge = SQLBridge(
    ...,
    cache_config={"max_size": 100}  # Limit cache
)
```

### 4. Transaction Issues

#### Error: "DLL does not support transactions"
```
RuntimeError: DLL does not support transactions
```

**Cause:** DLL was not compiled with transaction support or is outdated.

**Solutions:**
1. Check if DLL has transaction functions
2. Recompile DLL with transaction support
3. Use operations without transactions if necessary

**Verification:**
```python
import ctypes

# Check if DLL has transaction support
dll = ctypes.cdll.LoadLibrary("sqlbridge.dll")
has_transactions = hasattr(dll, 'BeginTransaction')
print(f"Transaction support: {has_transactions}")
```

#### Transaction not committed
**Symptoms:** Changes are not saved to database.

**Solutions:**
1. Use `async with` context manager
2. Check if there are no exceptions during transaction
3. Use try/except for error handling

**Correct Example:**
```python
async with bridge.transaction() as tx:
    await tx.insert("users", {"name": "John"})
    await tx.update("users", {"active": True}, {"name": "John"})
    # Automatic commit when exiting context
```

### 5. Cache Issues

#### Cache not working
**Symptoms:** Queries are not cached.

**Solutions:**
1. Check if cache is enabled
2. Use same parameters for identical queries
3. Check if TTL has not expired

**Example:**
```python
# Enable cache
bridge = SQLBridge(
    ...,
    enable_query_cache=True,
    cache_config={"default_ttl": 300}  # 5 minutes
)

# Query will be cached
result1 = await bridge.select("users", ["*"], {"active": True})

# Same query uses cache
result2 = await bridge.select("users", ["*"], {"active": True})
```

#### Cache invalidation not working
**Symptoms:** Old data is returned from cache.

**Solutions:**
1. Invalidate cache after write operations
2. Use appropriate TTL
3. Invalidate by table or operation

**Example:**
```python
# Insert data
await bridge.insert("users", {"name": "John"})

# Invalidate cache for users table
await bridge.invalidate_cache(table="users")

# Next query will fetch updated data
result = await bridge.select("users", ["*"])
```

### 6. Logging Issues

#### Logs not appearing
**Symptoms:** No logs are displayed.

**Solutions:**
1. Enable debug mode
2. Configure logging level
3. Check if handlers are configured

**Example:**
```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug in bridge
bridge = SQLBridge(..., debug=True)

# Or configure manually
logger = bridge.get_logger()
logger.setLevel(logging.DEBUG)
```

#### Too many logs
**Symptoms:** Excessive logs pollute output.

**Solutions:**
1. Disable debug mode in production
2. Configure appropriate logging level
3. Use logging filters

**Example:**
```python
# Production - no debug
bridge = SQLBridge(..., debug=False)

# Development - with debug
bridge = SQLBridge(..., debug=True)
```

### 7. Migration Issues

#### Migration not executing
**Symptoms:** Migration is not applied.

**Solutions:**
1. Check if migration system is enabled
2. Check if bridge is configured
3. Check if migration file exists

**Example:**
```python
# Enable migrations
bridge = SQLBridge(
    ...,
    enable_migrations=True,
    migrations_dir="migrations"
)

# Run migrations
await bridge.run_migrations()
```

#### Dependency error
**Symptoms:** Migration fails due to unmet dependency.

**Solutions:**
1. Check if dependent migrations were executed
2. Run migrations in order
3. Check migration file

**Example:**
```python
# Check migration status
status = await bridge.get_migration_status("001_create_users")
print(f"Status: {status}")

# Run pending migrations
await bridge.run_migrations()
```

## Debug Tools

### 1. Debug Mode
```python
bridge = SQLBridge(..., debug=True)
```

### 2. Profiling
```python
bridge = SQLBridge(..., enable_profiling=True)
metrics = bridge.get_performance_metrics()
```

### 3. Dashboard
```python
bridge = SQLBridge(..., enable_dashboard=True)
await bridge.start_dashboard()
summary = bridge.get_dashboard_summary()
```

### 4. Detailed Logs
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contact and Support

For issues not covered in this guide:

1. Check detailed logs with `debug=True`
2. Use profiling system to identify bottlenecks
3. Consult DLL API documentation
4. Open an issue in the project repository

## Debug Code Examples

### Check Bridge Status
```python
async def debug_bridge_status(bridge):
    print(f"Driver: {bridge.driver}")
    print(f"Pool ID: {bridge.pool_id}")
    print(f"Debug: {bridge.debug}")
    
    # Performance metrics
    metrics = bridge.get_performance_metrics()
    if metrics:
        print(f"Metrics: {metrics}")
    
    # Dashboard status
    summary = bridge.get_dashboard_summary()
    if summary:
        print(f"Dashboard: {summary}")
```

### Test Connection
```python
async def test_connection(bridge):
    try:
        # Simple test
        result = await bridge.select("information_schema.tables", ["table_name"], limit=1)
        print("✅ Connection working")
        return True
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
```
