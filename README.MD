KaironDB
The Async Python ORM that doesn't sacrifice performance.

KaironDB is a modern database access library built on a unique hybrid architecture: an elegant and declarative Python API that communicates with a high-performance DLL written in Go.

Stop choosing between the ease of use of an ORM and the speed of a low-level driver. With KaironDB, you get both.

✨ Key Advantages
Truly Asynchronous: Built from the ground up for async/await. Run hundreds of queries in parallel with asyncio.gather and watch your application fly, ideal for frameworks like FastAPI.

Extreme Performance: Thanks to the Go backend and automatic Connection Pooling, KaironDB minimizes Python's overhead to deliver performance that surpasses traditional solutions in high-concurrency scenarios.

Declarative & Safe API: Define your tables as intuitive Python classes. KaironDB provides automatic data validation, ensuring the integrity of your data before it even hits the database.

Powerful Querying: Forget long SQL strings. Build complex queries with AND (&) and OR (|) programmatically using Q Objects and dynamic filters like __gt, __like, and __in.

Multi-DB Support: Write your code once and run it on PostgreSQL, SQL Server, MySQL, and SQLite without changes.

🚀 Installation
Available directly on PyPI. Install with a simple pip command:

pip install kairondb

⚡ Quickstart Guide
See how easy it is to get started.

1. Define Your Model
Describe your table using Python classes.

from kairondb import Model, IntegerField, StringField

class User(Model):
    # The name of the table in your database
    _table_name = "users"

    # Define your columns with types and rules
    id = IntegerField(primary_key=True)
    name = StringField(required=True, max_length=100)
    status = StringField(default='active')

2. Connect and Run an Async Query
All database interaction is done asynchronously.

import asyncio
from kairondb import SQLBridge, Model

async def main():
    # Create the connection bridge (the pool is managed automatically)
    bridge = SQLBridge(
        driver="postgres",
        server="localhost",
        db_name="mydb",
        user="myuser",
        password="mypassword"
    )
    # Associate the connection with all your models
    Model.set_bridge(bridge)

    # Run your first async query!
    active_users = await User.select(where={'status': 'active'})
    print(active_users)

    # Close the connection pool when you're done
    await bridge.close()

if __name__ == "__main__":
    asyncio.run(main())

📖 Advanced Usage
Complex Queries with Q Objects
Use Q to build any WHERE logic you need.

from kairondb import Q

# Find active users who are under 25 OR whose name starts with 'A'
query = Q(status='active') & (Q(age__lt=25) | Q(name__like='A%'))

results = await User.select(where=query)

Concurrent Execution
Run hundreds of queries in parallel for a massive performance gain.

# Create a list of 100 search tasks
tasks = [User.select(where={'id': i}) for i in range(1, 101)]

# Dispatch all at once and wait for the results
results = await asyncio.gather(*tasks)

Atomic Transactions
Ensure data integrity with the asynchronous context manager.

try:
    async with bridge.transaction() as tx:
        # 'tx' is a transactional bridge
        accounts_model = Model(tx, "Accounts")
        
        # These two operations will either succeed together or fail together.
        await accounts_model.exec("UPDATE Accounts SET balance = balance - 100 WHERE id = 1")
        await accounts_model.exec("UPDATE Accounts SET balance = balance + 100 WHERE id = 2")
        
    print("Transfer successful!")
except Exception as e:
    print(f"Transaction failed and was rolled back: {e}")

❤️ Contributing
KaironDB is an open-source project, and all help is welcome! If you find a bug, have a suggestion, or want to contribute code, please open an "Issue" or a "Pull Request" on our GitHub repository.

If you like the project, consider supporting its development:

📄 License
Distributed under the MIT License.