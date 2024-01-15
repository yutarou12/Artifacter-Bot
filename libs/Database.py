import os
import hashlib
import logging
from functools import wraps

import asyncpg


class ProductionDatabase:

    def __init__(self):
        self.pool = None

    async def setup(self):
        self.pool = await asyncpg.create_pool(f"postgresql://{os.getenv('POSTGRESQL_USER')}:{os.getenv('POSTGRESQL_PASSWORD')}@{os.getenv('POSTGRESQL_HOST_NAME')}:{os.getenv('POSTGRESQL_PORT')}/{os.getenv('POSTGRESQL_DATABASE_NAME')}")

        async with self.pool.acquire() as conn:
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS user_uid (user_id bigint NOT NULL PRIMARY KEY, uid char(10) NOT NULL)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS premium_guild (guild_id bigint NOT NULL, PRIMARY KEY (guild_id))")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS premium_user (user_id bigint NOT NULL, PRIMARY KEY (user_id))")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS user_data_cache (user_id bigint NOT NULL, user_cache text, PRIMARY KEY (user_id))")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS uid_lock (uid bigint NOT NULL, user_id bigint, PRIMARY KEY (uid),)"
            )
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS uid_lock_raw (user_id bigint, uid bigint NOT NULL,  hash char(8), PRIMARY KEY (user_id),)"
            )

        return self.pool

    def check_connection(func):
        @wraps(func)
        async def inner(self, *args, **kwargs):
            self.pool = self.pool or await self.setup()
            return await func(self, *args, **kwargs)

        return inner

    @check_connection
    async def execute(self, sql):
        async with self.pool.acquire() as con:
            await con.execute(sql)

    @check_connection
    async def fetch(self, sql):
        async with self.pool.acquire() as con:
            data = await con.fetch(sql)
        return data

    @check_connection
    async def get_uid_from_user(self, user_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT uid FROM user_uid WHERE user_id=$1', user_id)
            if data:
                return data[0].get('uid')
            else:
                return None

    @check_connection
    async def get_user_from_uid(self, uid: str):
        async with self.pool.acquire() as con:
            data = await con.fetch('SELECT user_id FROM user_uid WHERE uid=$1', uid)
            if data:
                return data[0].get('user_id')
            else:
                return None

    @check_connection
    async def add_user_uid(self, user_id: int, uid: str):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO user_uid (user_id, uid) VALUES ($1, $2)", user_id, str(uid))

    @check_connection
    async def remove_user_uid(self, user_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM user_uid WHERE user_id=$1", user_id)

    @check_connection
    async def get_premium_guild_list(self):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM premium_guild")
            result = [value['guild_id'] for value in data]
            return result

    @check_connection
    async def add_premium_guild(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO premium_guild (guild_id)  VALUES ($1)", guild_id)

    @check_connection
    async def remove_premium_guild(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM premium_guild WHERE guild_id=$1", guild_id)

    @check_connection
    async def get_user_cache(self, user_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM user_data_cache WHERE user_id=$1", user_id)
            if data:
                return data[0].get('user_cache')
            else:
                return None

    @check_connection
    async def add_user_cache_data(self, user_id: int):
        user_cache = hashlib.sha256(str(user_id).encode()).hexdigest()
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO user_data_cache (user_id, user_cache)  VALUES ($1, $2)", user_id, user_cache)

    @check_connection
    async def remove_user_cache_data(self, user_id: int):
        async with self.pool.acquire() as con:
            user_cache = await self.get_user_cache(user_id)
            await con.execute("DELETE FROM user_data_cache WHERE user_id=$1", user_id)
            if os.path.isfile(f'./data/cache/{user_cache}.json'):
                os.remove(f'./data/cache/{user_cache}.json')

    @check_connection
    async def get_premium_user_list(self):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM premium_user")
            result = [value['user_id'] for value in data]
            return result

    @check_connection
    async def get_premium_user_bool(self, user_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM premium_user WHERE user_id=$1", user_id)
            return bool(data)

    @check_connection
    async def add_premium_user(self, user_id: int):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO premium_user (user_id)  VALUES ($1)", user_id)

    @check_connection
    async def remove_premium_user(self, user_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM premium_user WHERE user_id=$1", user_id)

    @check_connection
    async def set_lock_uid_user(self, user_id: int, uid: int):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO uid_lock (uid, user_id)  VALUES ($1, $2)", uid, user_id)

    @check_connection
    async def get_lock_uid_user(self, uid: int, user_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM uid_lock WHERE (uid=$1, user_id=$2)", uid, user_id)
            return bool(data)

    @check_connection
    async def remove_lock_uid_user(self, user_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM uid_lock WHERE user_id=$1", user_id)

    @check_connection
    async def add_raw_lock_uid_user(self, uid: int, user_id: int, hash_: str):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO uid_lock_raw (uid, user_id, hash)  VALUES ($1, $2, $3)", uid, user_id, hash_)

    @check_connection
    async def get_raw_lock_uid_user(self, user_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM uid_lock_raw WHERE user_id=$1", user_id)
            return data

    @check_connection
    async def get_list_raw_hash(self):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT hash FROM uid_lock_raw")
            return data

    @check_connection
    async def remove_raw_lock_uid_user(self, user_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM uid_lock_raw WHERE user_id=$1", user_id)


class DebugDatabase(ProductionDatabase):

    async def execute(self, sql):
        logging.info(f"executing sql: {sql}")

    async def fetch(self, sql):
        logging.info(f"fetching by sql: {sql}")

    async def get_uid_from_user(self, user_id: int):
        return '859015814'

    async def get_user_from_uid(self, uid: str):
        return 534994298827964416

    async def add_user_uid(self, user_id: int, uid: str):
        pass

    async def remove_user_uid(self, user_id: int):
        pass

    async def get_premium_guid_list(self):
        return []

    async def add_premium_guid(self, guild_id: int):
        pass

    async def remove_premium_guid(self, guild_id: int):
        pass

    async def get_user_cache(self, user_id: int):
        pass

    async def add_user_cache_data(self, user_id: int):
        pass

    async def remove_user_cache_data(self, user_id: int):
        pass

    async def get_premium_user_list(self):
        return []

    async def get_premium_user_bool(self, user_id: int):
        return True

    async def add_premium_user(self, user_id: int):
        pass

    async def remove_premium_user(self, user_id: int):
        pass

    async def set_lock_uid_user(self, user_id: int, uid: int):
        pass

    async def get_lock_uid_user(self, uid: int, user_id: int):
        return True

    async def remove_lock_uid_user(self, user_id: int):
        pass

if int(os.getenv('DEBUG')) == 1:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
