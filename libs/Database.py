import os
import logging
from functools import wraps

import pymysql.cursors


class ProductionDatabase:

    def __init__(self):
        self.connection = None

    def setup(self):
        self.connection = pymysql.connect(host=os.getenv('MYSQL_HOST_NAME'),
                                          user=os.getenv('MYSQL_USER'),
                                          password=os.getenv('MYSQL_PASSWORD'),
                                          database=os.getenv('MYSQL_DATABASE_NAME'),
                                          cursorclass=pymysql.cursors.DictCursor)

        with self.connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS `user_uid` (`user_id` bigint NOT NULL, `uid` char(10) NOT NULL, PRIMARY KEY (`user_id`))")
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS `premium_guild` (`guild_id` bigint NOT NULL, PRIMARY KEY (`guild_id`))")
        self.connection.commit()

        return self.connection

    def check_connection(func):
        @wraps(func)
        def inner(self, *args, **kwargs):
            self.connection = self.connection or self.setup()
            return func(self, *args, **kwargs)
        return inner

    @check_connection
    def execute(self, sql):
        with self.connection.cursor() as cursor:
            await cursor.execute(sql)

    @check_connection
    def fetch(self, sql):
        with self.connection.cursor() as cursor:
            data = cursor.fetchone(sql)
        return data

    @check_connection
    def get_uid_from_user(self, user_id: int):
        with self.connection.cursor() as cursor:
            cursor.excute('SELECT `uid` FROM `user_uid` WHERE `user_id`=%s', (user_id,))
            result = cursor.fetchone()
        return result

    @check_connection
    def get_user_from_uid(self, uid: str):
        with self.connection.cursor() as cursor:
            cursor.excute('SELECT `user_id` FROM `user_uid` WHERE `uid`=%s', (uid,))
            result = cursor.fetchone()
        return result

    @check_connection
    def add_user_uid(self, user_id: int, uid: str):
        with self.connection.cursor() as cursor:
            cursor.excute("INSERT INTO `user_uid` (`user_id`, `uid`) VALUES (%s, %s)", (user_id, uid))
        self.connection.commit()

    @check_connection
    def remove_user_uid(self, user_id: int, uid: str):
        with self.connection.cursor() as cursor:
            cursor.excute("DELETE FROM `user_uid` WHERE `user_id`=%s AND `uid`=%s", (user_id, uid))
        self.connection.commit()

    @check_connection
    def get_premium_guid_list(self):
        with self.connection.cursor() as cursor:
            cursor.excute('SELECT guild_id FROM `premium_guild`')
            result = cursor.fetchall()
        return result

    @check_connection
    def add_premium_guid(self, guild_id: int):
        with self.connection.cursor() as cursor:
            cursor.excute("INSERT INTO `premium_guild` (`guild_id`)  VALUES (%s)", (guild_id,))
        self.connection.commit()

    @check_connection
    def remove_premium_guid(self, guild_id: int):
        with self.connection.cursor() as cursor:
            cursor.excute("DELETE FROM `premium_guild` WHERE `guild_id`=%s", (guild_id, ))
        self.connection.commit()


class DebugDatabase(ProductionDatabase):

    def execute(self, sql):
        logging.info(f"executing sql: {sql}")

    def fetch(self, sql):
        logging.info(f"fetching by sql: {sql}")

    def get_uid_from_user(self, user_id: int):
        return '859015814'

    def get_user_from_uid(self, uid: str):
        return 534994298827964416

    def add_user_uid(self, user_id: int, uid: str):
        pass

    def remove_user_uid(self, user_id: int, uid: str):
        pass

    def get_premium_guid_list(self):
        return []

    def add_premium_guid(self, guild_id: int):
        pass

    def remove_premium_guid(self, guild_id: int):
        pass


if int(os.getenv('DEBUG')) == 1:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
