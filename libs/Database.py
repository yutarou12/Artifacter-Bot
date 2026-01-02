import os
import hashlib
import logging
from functools import wraps

import asyncpg

import libs.env as env


class ProductionDatabase:

    def __init__(self):
        self.pool = None

    async def setup(self):
        self.pool = await asyncpg.create_pool(f"postgresql://{env.POSTGRESQL_USER}:{env.POSTGRESQL_PASSWORD}@{env.POSTGRESQL_HOST_NAME}:{env.POSTGRESQL_PORT}/{env.POSTGRESQL_DATABASE_NAME}")

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
                "CREATE TABLE IF NOT EXISTS cmd_log (user_id bigint, cmd_name text, ch_id bigint, cmd_date timestamp)")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS ephemeral_mode_guild (guild_id bigint NOT NULL, PRIMARY KEY (guild_id))")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS rasen_character (user_id bigint NOT NULL PRIMARY KEY, character_data TEXT[] NOT NULL)")

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
    async def add_cmd_log(self, user_id: int, cmd_name: str, ch_id: int):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO cmd_log (user_id, cmd_name, ch_id, cmd_date)  VALUES ($1,$2,$3,now())", user_id, cmd_name, ch_id)

    @check_connection
    async def get_cmd_log(self):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM cmd_log")
            return data

    @check_connection
    async def get_ephemeral_mode_guild_list(self):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT guild_id FROM ephemeral_mode_guild")
            result = [value['guild_id'] for value in data]
            return result

    @check_connection
    async def add_ephemeral_mode_guild(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO ephemeral_mode_guild (guild_id)  VALUES ($1)", guild_id)

    @check_connection
    async def remove_ephemeral_mode_guild(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM ephemeral_mode_guild WHERE guild_id=$1", guild_id)

    @check_connection
    async def is_ephemeral_mode_guild(self, guild_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM ephemeral_mode_guild WHERE guild_id=$1", guild_id)
            return bool(data)

    @check_connection
    async def get_rasen_character(self, user_id: int) -> list[str]:
        async with self.pool.acquire() as con:
            # data = await con.fetch("SELECT ARRAY_TO_STRING(ARRAY_AGG(unnested_value ORDER BY ordinality), ',') FROM rasen_character, UNNEST(character_data)  WITH ORDINALITY AS u(unnested_value, ordinality) WHERE user_id = $1;", user_id)
            data = await con.fetchval("SELECT array_to_string(character_data, ',') FROM rasen_character WHERE user_id = $1", user_id)
            if data:
                # dataの例：10000021,10000016,10000023
                return data.split(',')
            else:
                return []

    @check_connection
    async def add_rasen_character(self, user_id: int, character_data: list[str]):
        db_data = await self.get_rasen_character(user_id)
        if not db_data:
            async with self.pool.acquire() as con:
                await con.execute("INSERT INTO rasen_character (user_id, character_data)  VALUES ($1, $2)", user_id, character_data)
        else:
            async with self.pool.acquire() as con:
                await con.execute("UPDATE rasen_character SET character_data=$1 WHERE user_id=$2", character_data, user_id)

    @check_connection
    async def remove_rasen_character(self, user_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM rasen_character WHERE user_id=$1", user_id)


class DebugDatabase(ProductionDatabase):
    def __init__(self):
        super().__init__()
        self.pool = None

    async def setup(self):
        pass

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

    async def get_premium_guild_list(self):
        return []

    async def add_premium_guild(self, guild_id: int):
        pass

    async def remove_premium_guild(self, guild_id: int):
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

    async def add_cmd_log(self, user_id: int, cmd_name: str, ch_id: int):
        pass

    async def get_cmd_log(self):
        return []

    async def get_ephemeral_mode_guild_list(self):
        return []

    async def add_ephemeral_mode_guild(self, guild_id: int):
        pass

    async def remove_ephemeral_mode_guild(self, guild_id: int):
        pass

    async def is_ephemeral_mode_guild(self, guild_id: int):
        return False

    async def get_rasen_character(self, user_id: int):
        return []

    async def add_rasen_character(self, user_id: int, character_data):
        pass

    async def remove_rasen_character(self, user_id: int):
        pass


if env.DEBUG == 1:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
