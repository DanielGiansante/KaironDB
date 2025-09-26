# KaironDB Installation Guide

## PyPI Installation (Recommended)

### Basic Installation
```bash
pip install kairondb
```

### Installation with Development Dependencies
```bash
pip install kairondb[dev]
```

### Specific Version Installation
```bash
pip install kairondb==1.0.0
```

## Source Installation

### 1. Clone Repository
```bash
git clone https://github.com/kairondb/kairondb.git
cd kairondb
```

### 2. Install in Development Mode
```bash
pip install -e .
```

### 3. Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

## System Requirements

### Python
- **Minimum version**: Python 3.8+
- **Tested versions**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

### Operating System
- **Windows**: Windows 10 or higher
- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 9+
- **macOS**: macOS 10.14+ (Mojave)

### System Dependencies

#### Windows
- Visual C++ Redistributable 2015 or higher
- .NET Framework 4.7.2+ (for SQL Server)

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential libpq-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install postgresql-devel
```

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install via Homebrew
brew install postgresql
```

## DLL Installation

KaironDB requires a DLL (Dynamic Link Library) compiled in Go. The DLL must be in the package directory.

### DLL Verification
```python
import os
from kairondb import SQLBridge

# Check if DLL exists
dll_path = os.path.join(os.path.dirname(SQLBridge.__file__), 'sqlbridge.dll')
print(f"DLL exists: {os.path.exists(dll_path)}")
```

### DLL Compilation (Developers)
```bash
# Install Go
# https://golang.org/dl/

# Compile DLL
cd go-backend
go build -buildmode=c-shared -o sqlbridge.dll main.go

# Copy to package directory
cp sqlbridge.dll ../src/kairondb/
```

## Installation Verification

### Basic Test
```python
import kairondb
print(f"KaironDB version: {kairondb.__version__}")
```

### Functionality Test
```python
import asyncio
from kairondb import SQLBridge

async def test_installation():
    try:
        # Test with SQLite (no server required)
        bridge = SQLBridge(
            driver="sqlite3",
            server=":memory:",
            db_name="test",
            user="",
            password=""
        )
        
        # Basic test
        result = await bridge.select("sqlite_master", ["name"], {"type": "table"})
        print("✅ Installation working correctly!")
        
        await bridge.close()
        
    except Exception as e:
        print(f"❌ Installation error: {e}")

# Run test
asyncio.run(test_installation())
```

## Development Setup

### 1. Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Install Pre-commit Hooks
```bash
pre-commit install
```

### 4. Run Tests
```bash
pytest tests/ -v
```

## Troubleshooting

### Error: "DLL not found"
```bash
# Check if DLL exists
ls src/kairondb/sqlbridge.*

# If not exists, compile
cd go-backend
go build -buildmode=c-shared -o sqlbridge.dll main.go
cp sqlbridge.dll ../src/kairondb/
```

### Error: "Driver not supported"
```python
from kairondb import SQLBridge

# Check supported drivers
print("Supported drivers:", SQLBridge.SUPPORTED_DRIVERS)
```

### Error: "Failed to load library"
- Check if DLL was compiled for correct architecture (x64 for Python 64-bit)
- Install Visual C++ Redistributable (Windows)
- Check system dependencies (Linux/macOS)

## Usage Examples

### Basic Example
```python
import asyncio
from kairondb import SQLBridge

async def main():
    # Connect to database
    bridge = SQLBridge(
        driver="postgres",
        server="localhost:5432",
        db_name="mydb",
        user="user",
        password="pass"
    )
    
    # Execute query
    result = await bridge.select("users", ["*"])
    print(result)
    
    # Close connection
    await bridge.close()

asyncio.run(main())
```

### Advanced Features Example
```python
import asyncio
from kairondb import SQLBridge

async def main():
    # Bridge with all features
    bridge = SQLBridge(
        driver="postgres",
        server="localhost:5432",
        db_name="mydb",
        user="user",
        password="pass",
        enable_advanced_pool=True,
        enable_query_cache=True,
        enable_profiling=True,
        enable_dashboard=True
    )
    
    # Execute operations
    result = await bridge.select("users", ["*"], {"active": True})
    
    # View metrics
    metrics = bridge.get_performance_metrics()
    print(f"Metrics: {metrics}")
    
    await bridge.close()

asyncio.run(main())
```

## Support

For installation issues:

1. Check detailed logs
2. Consult troubleshooting documentation
3. Open an issue on GitHub
4. Contact support team

## Useful Links

- [Complete Documentation](README.md)
- [API Reference](DLL_API.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Advanced Examples](examples/)
- [GitHub Repository](https://github.com/kairondb/kairondb)
- [PyPI Package](https://pypi.org/project/kairondb/)
