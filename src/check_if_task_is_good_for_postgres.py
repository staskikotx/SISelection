from config import *
import pickle
import pandas as pd
import re
import sqlglot
import psycopg2
from psycopg2 import sql
import time

def check_if_task_is_good_for_postgres(postgres_candidates, db_name):
    """
    Check if all PostgreSQL candidates execute successfully.
    Retries 'recovery mode' errors up to 3 times with 1s delay.
    Returns False if any candidate fails after retries.
    """
    task_ok = True 
    
    for idx, candidate in enumerate(postgres_candidates):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with psycopg2.connect(
                    host=HOST,
                    dbname="pure_" + db_name,
                    user=USER
                ) as conn:
                    with conn.cursor() as cur:
                        try:
                            # Set timeout (LOCAL works in autocommit too)
                            cur.execute("SET LOCAL statement_timeout = 30000")
                            
                            # Execute query
                            cur.execute(sql.SQL(candidate))
                            
                            print(f"✓ Candidate {idx}: Execution OK")
                            break  # Success - exit retry loop
                            
                        except psycopg2.Error as query_error:
                            task_ok = False
                            
                            # Handle timeout errors
                            if query_error.pgcode == '57014':  # QueryCanceled
                                print(f"\n✗ Candidate {idx}: Query timed out after 30 seconds")
                            else:
                                print(f"\n✗ Candidate {idx}: {query_error.pgerror}")
                                print(f"   Candidate: {candidate}")
                            
                            break  # Don't retry query errors, only connection errors
                        
            except psycopg2.OperationalError as conn_error:
                error_msg = str(conn_error).lower()
                
                # Check for recovery mode error
                if "recovery mode" in error_msg or "the database system is in recovery" in error_msg:
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        print(f"⚠️  Candidate {idx}: Database in recovery mode (attempt {retry_count}/{max_retries})")
                        print(f"   Sleeping 1 second before retry...")
                        time.sleep(1)
                        continue  # Retry the connection
                    else:
                        # Max retries reached - return False
                        print(f"✗ Candidate {idx}: Database still in recovery mode after {max_retries} attempts")
                        print(f"   Aborting task check")
                        return False  # ← Return False immediately on persistent recovery error
                else:
                    # Different OperationalError - don't retry
                    print(f"✗ Candidate {idx}: Connection error: {conn_error}")
                    task_ok = False
                    break  # Move to next candidate
                    
            except Exception as unexpected_error:
                # Catch any other unexpected errors
                print(f"✗ Candidate {idx}: Unexpected error: {unexpected_error}")
                task_ok = False
                break  # Move to next candidate
        
    return task_ok