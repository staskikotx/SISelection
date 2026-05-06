from config import *
import pickle
import pandas as pd
import sqlglot
import psycopg2
from psycopg2 import sql


def create_postgres_tables(postgres_representatives, database_name, table_name_prefix):
    task_ok = True 
    for idx, candidate in enumerate(postgres_representatives):
        original_candidate = candidate
        database = "prov_" + database_name 

        print(f'Evaluating {candidate} on ProvSQL')
        with psycopg2.connect(
            host=HOST,
            dbname=database,
            user=USER,
        ) as conn:
            with conn.cursor() as cur:
                table_name = f"{table_name_prefix}_{idx}"
                try:
                    
                    # COMMENT IF YOU DON'T WANT TO RE-CREATE THE ANSWER_TABLES
                    cur.execute(sql.SQL(f"drop table if exists {table_name};"))
                    
                    # Check if table exists (case-insensitive, handles reserved keywords)

                    cur.execute("BEGIN")
                    cur.execute("SET LOCAL statement_timeout = 30000")  # 30 seconds in milliseconds

                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 
                            FROM pg_catalog.pg_tables
                            WHERE schemaname = 'public'
                            AND tablename = %s
                        )
                    """, (table_name,))

                    if not cur.fetchone()[0]:
                        # Table doesn't exist - create it safely
                        cur.execute(
                            sql.SQL("SET LOCAL max_parallel_workers_per_gather = 0; CREATE TABLE {} AS {}").format(
                                sql.Identifier(table_name),  # Safe quoting for table name
                                sql.SQL(candidate)           # Preserves your existing query
                            )
                        )
                    error = "OK"
                    cur.execute("COMMIT")
                    print("Execution: OK")
                except psycopg2.Error as query_error:
                    task_ok = False

                    cur.execute("ROLLBACK")
                    
                    # Special handling for timeout errors
                    if query_error.pgcode == '57014':  # QueryCanceled error code
                        error = "TIMEOUT (30s)"
                        print("\n✗ Query timed out after 30 seconds")
                        print("\n✗ Query execution failed:")
                        raise Exception("Query timed out on ProvSQL")
                    else:
                        print(f"Error: {query_error.pgerror}")
                        #print(f"SQLSTATE: {query_error.pgcode}")
                        #print(f"Details: {query_error}")
                        print(f"Problem table: {table_name}")
                        error = query_error.pgerror.split('\n')[0]
                        raise Exception(error)

                    
                    




