import sqlite3
from sqlite3 import Error
from pathlib import Path
import argparse
import pandas as pd

database_name = r"sync_tests_results.db"
results_file_name = r"sync_results.log"


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(f"Error connecting to the database:\n {e}")

    return conn


def add_test_values_into_db(table_name, col_names_list, col_values_list):
    print(f"Write values into {table_name} table")
    current_directory = Path.cwd()
    print(f"current_directory: {current_directory}")
    database_path = Path(current_directory) / database_name
    print(f"database_path: {database_path}")

    col_names = ','.join(col_names_list)
    col_spaces = ','.join(['?'] * len(col_names_list))
    conn = create_connection(database_path)
    try:
        sql_query = f"INSERT INTO {table_name} (%s) values(%s)" % (col_names, col_spaces)
        print(f"sql: {sql_query}")

        cur = conn.cursor()
        cur.execute(sql_query, col_values_list)
        conn.commit()
        cur.close()
    except sqlite3.Error as error:
        print(f"!!! ERROR: Failed to insert data into {table_name} table:\n", error)
        return False
    finally:
        if conn:
            conn.close()
    return True


# def add_test_values_into_db(table_name, test_values):
#     print(f"Write values into {table_name} table")
#     current_directory = Path.cwd()
#     database_path = Path(current_directory) / "sync_tests" / database_name
#     print(f"database_path: {database_path}")
#
#     conn = create_connection(database_path)
#     try:
#         sql_query = f' INSERT INTO {table_name} ' \
#               f'(env, tag_no1, tag_no2, cardano_cli_version1, cardano_cli_version2, ' \
#               f'cardano_cli_git_rev1, cardano_cli_git_rev2, start_sync_time1, end_sync_time1, start_sync_time2, ' \
#               f'end_sync_time2, byron_sync_time_secs1, shelley_sync_time_secs1, allegra_sync_time_seconds1, mary_sync_time_seconds1, ' \
#               f'sync_time_after_restart_seconds, total_chunks1, total_chunks2, latest_block_no1, latest_block_no2, ' \
#               f'latest_slot_no1, latest_slot_no2, start_node_seconds1, start_node_seconds2, platform_system, ' \
#               f'platform_release, platform_version, chain_size, sync_details1) ' \
#               f'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
#
#         print(f"sql: {sql_query}")
#
#         cur = conn.cursor()
#         cur.execute(sql_query, test_values)
#         conn.commit()
#         cur.close()
#     except sqlite3.Error as error:
#         print(f"!!! ERROR: Failed to insert data into {table_name} table:\n", error)
#         return False
#     finally:
#         if conn:
#             conn.close()
#     return True


def export_db_table_to_csv(table_name):
    print(f"Export {table_name} table into CSV file")
    current_directory = Path.cwd()

    # TODO = make it work for github actions tests
    # database_path = Path(current_directory) / "sync_tests" / database_name
    database_path = Path(current_directory) / database_name
    # csv_files_path = Path(current_directory) / "sync_tests" / "csv_files"
    csv_files_path = Path(current_directory) / "csv_files"

    print(f"database_path : {database_path}")
    print(f"csv_files_path: {csv_files_path}")

    Path(csv_files_path).mkdir(parents=True, exist_ok=True)

    conn = create_connection(database_path)
    try:
        sql_query = f"select * from {table_name}"
        print(f"sql_query: {sql_query}")

        cur = conn.cursor()
        cur.execute(sql_query)

        with open(csv_files_path / f"{table_name}.csv", "w") as csv_file:
            df = pd.read_sql(f"select * from {table_name}", conn)
            df.to_csv(csv_file, escapechar="\n", index=False)

        conn.commit()
        cur.close()

        print(f"Data exported Successfully into {csv_files_path / f'{table_name}.csv'}")
    except sqlite3.Error as error:
        print(f"!!! ERROR: Failed to insert data into {table_name} table:\n", error)
        return False
    finally:
        if conn:
            conn.close()
    return True


def get_column_names_from_table(table_name):
    print(f"Getting the column names from {table_name} table")
    current_directory = Path.cwd()

    # TODO aaa
    # database_path = Path(current_directory) / "sync_tests" / database_name
    database_path = Path(current_directory) / database_name

    print(f"database_path: {database_path}")
    conn = create_connection(database_path)
    try:
        sql_query = f"select * from {table_name}"
        print(f"sql_query: {sql_query}")

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


def add_column_to_table(table_name, column_name, column_type):
    print(f"Adding column {column_name} with type {column_type} to {table_name} table")
    current_directory = Path.cwd()

    # TODO aaa
    # database_path = Path(current_directory) / "sync_tests" / database_name
    database_path = Path(current_directory) / database_name

    print(f"database_path: {database_path}")
    conn = create_connection(database_path)

    try:
        sql_query = f"alter table {table_name} add column {column_name} {column_type}"
        print(f"sql_query: {sql_query}")

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


def main():
    env = vars(args)["environment"]

    current_directory = Path.cwd()
    print(f"current_directory: {current_directory}")

    # sync_test_clean_state.py is creating the "sync_results.log" file that has the test values
    # to be added into the db
    with open(current_directory / "sync_tests" / results_file_name, "r+") as file:
        file_values = file.read()
        print(f"file_values: {file_values}")

        test_values = file_values.replace("(", "").replace(")", "").replace("'", "").split(", ", 28)

    print(f"env: {env}")
    print(f"test_values: {test_values}")

    # Add the test values into the local copy of the database (to be pushed into master)
    add_test_values_into_db(env, test_values)

    # Export data into CSV file
    export_db_table_to_csv(env)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add sync test values into database\n\n")

    parser.add_argument("-e", "--environment",
                        help="The environment on which to run the tests - shelley_qa, testnet, staging or mainnet.")

    args = parser.parse_args()

    main()
