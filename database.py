import asyncpg
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

# Supabase connection details

#"user=postgres.aifjbnzzxdwhzlpvzzes password=ZOSMFJVMKSDVS43J5N43 host=aws-0-ap-southeast-1.pooler.supabase.com port=6543 database=postgres"

SUPABASE_URL = "postgres://postgres.aifjbnzzxdwhzlpvzzes:ZOSMFJVMKSDVS43J5N43@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres" # Replace with your Supabase URL
SUPABASE_KEY = os.getenv('SUPABASE')  # Replace with your Supabase Key


# Connection pool
_connection_pool = None

async def init():
    await _initialize()


async def _initialize():
    global _connection_pool
    _connection_pool = await asyncpg.create_pool(SUPABASE_URL)
    async with _connection_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS discord_logs (
                id SERIAL PRIMARY KEY,
                server_id TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print ("Database connection established")

async def add_log(server_id, message):
    global _connection_pool
    if _connection_pool is None:
        raise Exception("Database connection not established")

    async with _connection_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO discord_logs (server_id, message) VALUES ($1, $2)
        ''', str(server_id), message)

async def get_logs(server_id):
    global _connection_pool
    if _connection_pool is None:
        raise Exception("Database connection not established")

    async with _connection_pool.acquire() as conn:
            return await conn.fetch('''
                SELECT message FROM discord_logs WHERE server_id = $1 ORDER BY timestamp ASC
            ''', str(server_id))

async def get_server_ids():
    global _connection_pool
    if _connection_pool is None:
        raise Exception("Database connection not established")

    async with _connection_pool.acquire() as conn:
        server_ids = await conn.fetch('''
            SELECT DISTINCT server_id FROM discord_logs
        ''')

    return [server_id['server_id'] for server_id in server_ids]


async def _close():
    global _connection_pool
    if _connection_pool is not None:
        await _connection_pool.close()
        _connection_pool = None
