import sqlite3
from pathlib import Path
from sqlite3 import Error
import pandas as pd


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(f"!!! Error connecting to the database:\n {e}")

    return conn


def add_test_values_into_db(database_path, table_name, col_names_list, col_values_list):
    print(f"  -- database_path: {database_path}")
    col_names = ','.join(col_names_list)
    col_spaces = ','.join(['?'] * len(col_names_list))
    conn = create_connection(database_path)
    sql_query = f"INSERT INTO {table_name} (%s) values(%s)" % (col_names, col_spaces)
    print(f"  -- sql_query: {sql_query}")
    try:
        cur = conn.cursor()
        cur.execute(sql_query, col_values_list)
        conn.commit()
        cur.close()
    except sqlite3.Error as error:
        print(f"  -- !!! ERROR: Failed to insert data into {table_name} table:\n", error)
        return False
    finally:
        if conn:
            conn.close()
    return True


def export_db_table_to_csv(database_path, table_name):
    print(f"Exporting {table_name} table into CSV file")
    current_directory = Path.cwd()
    csv_files_path = Path(current_directory) / "csv_files"

    print(f"  -- database_path : {database_path}")
    print(f"  -- csv_files_path: {csv_files_path}")

    Path(csv_files_path).mkdir(parents=True, exist_ok=True)

    conn = create_connection(database_path)
    sql_query = f"select * from {table_name}"
    print(f"  -- sql_query: {sql_query}")
    try:
        cur = conn.cursor()
        cur.execute(sql_query)

        with open(csv_files_path / f"{table_name}.csv", "w") as csv_file:
            df = pd.read_sql(f"select * from {table_name}", conn)
            df.to_csv(csv_file, escapechar="\n", index=False)

        conn.commit()
        cur.close()

        print(f"  -- Data exported Successfully into {csv_files_path / f'{table_name}.csv'}")
    except sqlite3.Error as error:
        print(f"!!! ERROR: Failed to export {table_name} table to CSV:\n", error)
        return False
    finally:
        if conn:
            conn.close()
    return True


def get_column_names_from_table(database_path, env):
    table_name = env
    print(f"Getting the column names from {table_name} table")
    current_directory = Path.cwd()
    print(f"current_directory: {current_directory}")
    print(f"  -- database_path: {database_path}")

    conn = create_connection(database_path)
    sql_query = f"select * from {table_name}"
    print(f"  -- sql_query: {sql_query}")
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        col_name_list = [res[0] for res in cur.description]
        return col_name_list
    except sqlite3.Error as error:
        print(f"!!! ERROR: Failed to get column names from {table_name} table:\n", error)
        return False
    finally:
        if conn:
            conn.close()


def get_last_row_no(database_path, table_name):
    print(f"Getting the last row no from {table_name} table")
    current_directory = Path.cwd()
    print(f"  -- current_directory: {current_directory}")
    print(f"  -- database_path: {database_path}")

    conn = create_connection(database_path)
    sql_query = f"SELECT count(*) FROM {table_name};"
    print(f"  -- sql_query: {sql_query}")
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        last_row_no = cur.fetchone()[0]
        return last_row_no
    except sqlite3.Error as error:
        print(f"!!! ERROR: Failed to get the last row no from {table_name} table:\n", error)
        return False
    finally:
        if conn:
            conn.close()


def get_column_values(database_path, table_name, column_name):
    conn = create_connection(database_path)
    sql_query = f"SELECT {column_name} FROM {table_name};"
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        return [el[0] for el in cur.fetchall()]
    except sqlite3.Error as error:
        print(f"!!! ERROR: Failed to get {column_name} values from {table_name} table:\n", error)
        return False
    finally:
        if conn:
            conn.close()


def add_column_to_table(database_path, env, column_name, column_type):
    table_name = env
    print(f"Adding column {column_name} with type {column_type} to {table_name} table")
    print(f"  -- database_path: {database_path}")

    conn = create_connection(database_path)
    sql_query = f"alter table {table_name} add column {column_name} {column_type}"
    print(f"  -- sql_query: {sql_query}")
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        col_name_list = [res[0] for res in cur.description]
        return col_name_list
    except sqlite3.Error as error:
        print(f"!!! ERROR: Failed to add {column_name} column into {table_name} table:\n", error)
        return False
    finally:
        if conn:
            conn.close()