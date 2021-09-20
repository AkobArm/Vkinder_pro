import psycopg2
from SQL_bd_template import comand_list_sql_bd
from psycopg2 import OperationalError
import re


class SqlDataBase:
    def __init__(self, sql_db_name):
        self.line = sql_db_name
        new_data_list = self._format_name_todata()
        self.db_name = new_data_list[4]
        self.db_user = new_data_list[1]
        self.db_password = new_data_list[2]
        self.db_port = new_data_list[3]
        self.connection = self.create_connection()

    def _format_name_todata(self):
        ref = r"([a-zA-Z_]*)://([a-zA-Z_]*):([a-zA-Z_]*)@localhost:([0-9]*)/([a-zA-Z_]*)"
        return re.findall(ref, self.line)[0]

    def create_connection(self):
        self.connection = None
        try:
            self.connection = psycopg2.connect(
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port,
            )
            print("Connection to PostgreSQL DB successful")
        except OperationalError as e:
            print(f"The error '{e}' occurred")
        return self.connection

    def execute_query(self, query):
        self.connection.autocommit = True
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            print(f"{query} executed successfully")
        except OperationalError as e:
            print(f"The error '{e}' occurred")

    def create_tables(self, command_list):
        for query in command_list:
            self.execute_query(query=query)


def create_db(adress):
    sq1 = SqlDataBase(adress)
    sq1.create_tables(comand_list_sql_bd)
