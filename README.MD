
# KaironDB
The Async Python ORM that doesn't sacrifice performance.

KaironDB is a modern database access library built on a unique hybrid architecture: an elegant and declarative Python API that communicates with a high-performance DLL written in Go.

Stop choosing between the ease of use of an ORM and the speed of a low-level driver. With KaironDB, you get both.

## ✨ Key Advantages

**Truly Asynchronous**  
Built from the ground up for async/await. Run hundreds of queries in parallel with asyncio.gather and watch your application fly, ideal for frameworks like FastAPI.

**Extreme Performance**  
Thanks to the Go backend and automatic Connection Pooling, KaironDB minimizes Python's overhead to deliver performance that surpasses traditional solutions in high-concurrency scenarios.

**Declarative & Safe API**  
Define your tables as intuitive Python classes. KaironDB provides automatic data validation, ensuring the integrity of your data before it even hits the database.

**Powerful Querying**  
Forget long SQL strings. Build complex queries with AND (&) and OR (|) programmatically using Q Objects and dynamic filters like `__gt`, `__like`, and `__in`.

**Multi-DB Support**  
Write your code once and run it on PostgreSQL, SQL Server, MySQL, and SQLite without changes.

## 🚀 Installation

Available directly on PyPI. Install with a simple pip command:

```bash
pip install kairondb
```

## ⚡ Quickstart Guide

### 1. Define Your Model

Describe your table using Python classes.

```python
from kairondb import Model, IntegerField, StringField

class User(Model):
    _table_name = "users"
    id = IntegerField(primary_key=True)
    name = StringField(required=True, max_length=100)
    status = StringField(default='active')
```

### 2. Connect and Run an Async Query

All database interaction is done asynchronously.

```python
import asyncio
from kairondb import SQLBridge, Model

async def main():
    bridge = SQLBridge(
        driver="postgres",
        server="localhost",
        db_name="mydb",
        user="myuser",
        password="mypassword"
    )
    Model.set_bridge(bridge)

    active_users = await User.select(where={'status': 'active'})
    print(active_users)

    await bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📖 Advanced Usage

### Complex Queries with Q Objects

```python
from kairondb import Q

query = Q(status='active') & (Q(age__lt=25) | Q(name__like='A%'))
results = await User.select(where=query)
```

### Concurrent Execution

```python
tasks = [User.select(where={'id': i}) for i in range(1, 101)]
results = await asyncio.gather(*tasks)
```

### Atomic Transactions

```python
try:
    async with bridge.transaction() as tx:
        accounts_model = Model(tx, "Accounts")
        await accounts_model.exec("UPDATE Accounts SET balance = balance - 100 WHERE id = 1")
        await accounts_model.exec("UPDATE Accounts SET balance = balance + 100 WHERE id = 2")
    print("Transfer successful!")
except Exception as e:
    print(f"Transaction failed and was rolled back: {e}")
```

## ❤️ Contributing

KaironDB is an open-source project, and all help is welcome! If you find a bug, have a suggestion, or want to contribute code, please open an "Issue" or a "Pull Request" on our GitHub repository.

## 📄 License

Distributed under the MIT License.
