from config import *
import psycopg2
import psycopg2.sql as sql
from psycopg2 import extensions, sql as psql
import random
from sql_execution import execute_sql_on_string_with_timeout
from custom_tools import convert_postgres_database_to_sqlite

def count_sql_columns(sql_query):
    """
    Given an SQL query string, returns the number of columns in the SELECT clause.
    Handles cases like COUNT(*), DISTINCT, functions, and subqueries.
    """
    # Normalize spaces and remove newlines for consistent parsing
    sql_query = ' '.join(sql_query.strip().split())

    # Extract the SELECT clause between SELECT and FROM (case-insensitive)
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE)
    if not select_match:
        return 0  # No valid SELECT...FROM found

    select_clause = select_match.group(1).strip()

    # Handle COUNT(*), which is a single column
    if select_clause == '*':
        return 1

    # Track depth of parentheses to avoid splitting inside functions
    columns = []
    current = ''
    paren_depth = 0

    for char in select_clause:
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        elif char == ',' and paren_depth == 0:
            # Only split at top-level commas
            if current.strip():
                columns.append(current.strip())
                current = ''
            continue
        current += char

    # Add the last column
    if current.strip():
        columns.append(current.strip())

    return len(columns)

def tuplify(provenance_item):
    key, value = provenance_item
    return key, tuple(sorted(value))
 
def dict_list_to_set(lst):
    return {tuple(sorted(map(tuplify, d.items()))) for d in lst}
 
def pairs_to_dict_with_unique_values(pairs):
    result = {}
    for key, value in pairs:
        # Initialize empty list if key doesn't exist
        if key not in result:
            result[key] = []
        # Only add value if it's not already in the list
        for subvalue in value:
            if subvalue not in result[key]:
                result[key].append(subvalue)
    return result

def get_where_clause(row_numbers) :
    return ' or '.join([f'tuple_id = {number}' for number in row_numbers])

def table_exists(table_name, conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        return cur.fetchone()[0]

def process_table(table_name, conn, original_name):
    insert_statements = []
    rows_as_dictionary = {}

    with conn.cursor() as cur:
        # Step 1: Get all rows from the table
        cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
        
        # Step 2: Get column names
        col_names = [desc[0] for desc in cur.description][0:-2]

        columns_sql = sql.SQL(', ').join(map(sql.Identifier, col_names))
            
        cur.execute(sql.SQL("SELECT {} FROM {}").format(columns_sql, sql.Identifier(table_name)))


        # Step 3: Build INSERT statements
        for row_index, row in enumerate(cur):
            #print(row_index, ' ', row)
            # Escape values and format them correctly
            #values = []
            #for val in row:
            #    if isinstance(val, (str, bytes)):
            #        adapted = extensions.adapt(val).getquoted()
            #        if isinstance(adapted, bytes):
            #            adapted = adapted.decode('utf-8')
            #        values.append(adapted)
            #    elif val is None:
            #        values.append("NULL")
            #    else:
            #        values.append(str(val))
            
            
            actual_row = row[0:-1] # remove provenance uuid

            # Create INSERT statements
            values_sql = sql.SQL(', ').join(sql.Literal(v) for v in actual_row)
            insert_stmt = sql.SQL("INSERT INTO {} VALUES ({});").format(
                sql.Identifier(original_name),
                values_sql
            )
            insert_statements.append(insert_stmt.as_string(conn))

            # Create JSON dictionary

            assert(len(col_names) == len(actual_row))
            this_row_as_dict = {}
            for index in range (len(col_names)):
                this_row_as_dict[col_names[index]] = actual_row[index]

            row_identifier = f"row_{row_index}_of_{original_name}_table"    
            rows_as_dictionary[row_identifier] = this_row_as_dict

            

    return insert_statements, rows_as_dictionary

def contains_sum_case_when(query):
    """
    Check if an SQL query contains the words 'SUM', 'CASE', and 'WHEN' 
    (case-insensitive) as whole words.
    
    Args:
        query (str): SQL query string
        
    Returns:
        bool: True if all three words are present as whole words, False otherwise
    """
    if not isinstance(query, str):
        return False
        
    # Normalize whitespace to handle multi-line queries and extra spaces
    normalized = re.sub(r'\s+', ' ', query.strip())
    
    # Check for whole words using word boundaries (\b)
    has_sum = bool(re.search(r'\bsum\b', normalized, re.IGNORECASE))
    has_case = bool(re.search(r'\bcase\b', normalized, re.IGNORECASE))
    has_when = bool(re.search(r'\bwhen\b', normalized, re.IGNORECASE))
    
    return has_sum and has_case and has_when    

def contains_select_count(query):
    """
    Check if an SQL query contains the words 'SELECT' and 'COUNT' 
    (case-insensitive) as whole words.
    
    Args:
        query (str): SQL query string
        
    Returns:
        bool: True if both words are present as whole words, False otherwise
    """
    if not isinstance(query, str):
        return False
        
    # Normalize whitespace to handle multi-line queries and extra spaces
    normalized = re.sub(r'\s+', ' ', query.strip())
    
    # Check for whole words using word boundaries (\b)
    has_select_count = bool(re.search(r'select\s+count', normalized, re.IGNORECASE))
    
    return has_select_count

def grub_to_inserts(grub, database, suffix) :
    with psycopg2.connect(
            host=HOST,
            dbname = database,
            user=USER
        ) as conn:
        with conn.cursor() as cur:
            insert_statements = []
            rows_as_dictionary = {}

            pupa = pairs_to_dict_with_unique_values(grub)
            for table_name in pupa.keys() :   
                try:
                    temp_table_name = f"{table_name}_temp_{suffix}" 
                    if table_exists(temp_table_name, conn) :
                        cur.execute(
                            sql.SQL(f"drop table {temp_table_name};")
                        )

                    wclause = get_where_clause(pupa[table_name])
                    
                    if wclause != "":
            
                        cur.execute(
                            sql.SQL(f"create table {temp_table_name} as select * from \"{table_name}\" where {wclause};")
                        )
                        
                        new_insert_statements, new_rows_as_dictionary = process_table(temp_table_name, conn, table_name)
                        insert_statements = insert_statements + new_insert_statements
                        rows_as_dictionary.update(new_rows_as_dictionary)

                except psycopg2.Error as query_error:
                    print("\n✗ Query execution failed:")
                    print(f"Error: {query_error.pgerror}")
                    #print(f"SQLSTATE: {query_error.pgcode}")
                    #print(f"Details: {query_error}")
                    #exit()
    return insert_statements, rows_as_dictionary

def create_instance(i,j, first_candidate, second_candidate, db_schema, db_name, prov):
    suffix = f"_{i}_{j}"
    
    set1 = dict_list_to_set(prov[i])
    set2 = dict_list_to_set(prov[j])

    if (set1 == set2) :
        
        list1 = list(set1)

        # Number 42 was taken as an optimal balance between speed and performance
        for attempt in range(NUMBER_OF_ATTEMPTS_FOR_SIC):
            grub = []
            if set1:
                # we pick <= 2 random dicts and hope that they will be separating
                for d in random.sample(list1, min(2, len(list1))):
                    for item in d:
                        grub.append(item)
            else:
                # extremely rare case, occuring due to difference in SQLite and PostgreSQL functions
                # both candidates give empty answers, normally, it should be eradicated in extract_candidates.py
                # we will not construct separating instances for this case
                # сюда же попадает случай 0 vs None, для провенанса они одинаково пусты. Но ответы формально разные, это хорошо!
                pass
                

            # создаём инстанс и вычисляем на нём оба запроса
            database = "prov_" + db_name 
            insert_statements, rows_as_dictionary = grub_to_inserts(grub, database, suffix)

            schema = db_schema
            database = schema + "\n".join(insert_statements)
            sqlite_database = convert_postgres_database_to_sqlite(database)
            answer1 = execute_sql_on_string_with_timeout(sqlite_database, first_candidate)
            answer2 = execute_sql_on_string_with_timeout(sqlite_database, second_candidate)
        
            if not are_equal(answer1.result, answer2.result):
                break
    else :
        # that's the outcome we expect the most
        
        diff_one = set1.difference(set2)
        diff_two = set2.difference(set1)
        common = set1.intersection(set2)
        
        list_diff_one = list(diff_one)
        list_diff_two = list(diff_two)
        list_common = list(common)

        if contains_sum_case_when(first_candidate) or contains_sum_case_when(second_candidate) :
            q1 = 3
            q2 = 4
        elif contains_select_count(first_candidate) and contains_select_count(second_candidate):
            q1 = 1
            q2 = 2
        else:
            q1 = 1
            q2 = 1
        
        if q1 < q2 and len(diff_one) > len(diff_two):
            q1, q2 = q2, q1

        for attempt in range(NUMBER_OF_ATTEMPTS_FOR_SIC):
            
            grub = []
            
            if len(diff_one) > 0 and len(diff_two) > 0:
                for d in random.sample(list_diff_one, min(q1, len(list_diff_one))):
                    for item in d:
                        grub.append(item)
                for d in random.sample(list_diff_two, min(q2, len(list_diff_two))):
                    for item in d:
                        grub.append(item)
            elif len(diff_one) > 0 :
                if len(common) > 0 :
                    for d in random.sample(list_diff_one, 1):
                        for item in d:
                            grub.append(item)
                    for d in random.sample(list_common, 1):
                        for item in d:
                            grub.append(item)
                else:
                    for d in random.sample(list_diff_one, min(2, len(list_diff_one))):
                        for item in d:
                            grub.append(item)
            elif len(diff_two) > 0 :
                if len(common) > 0 :
                    for d in random.sample(list_diff_two, 1):
                        for item in d:
                            grub.append(item)
                    for d in random.sample(list_common, 1):
                        for item in d:
                            grub.append(item) 
                else:
                    for d in random.sample(list_diff_two, min(2, len(list_diff_two))):
                        for item in d:
                            grub.append(item)
        
            # создаём инстанс и вычисляем на нём оба запроса
            database = "prov_" + db_name

        
            insert_statements, rows_as_dictionary = grub_to_inserts(grub, database, suffix)
            #print(insert_statements)
            schema = db_schema
            database = schema + "\n".join(insert_statements)
            sqlite_database = convert_postgres_database_to_sqlite(database)
            answer1 = execute_sql_on_string_with_timeout(sqlite_database, first_candidate)
            answer2 = execute_sql_on_string_with_timeout(sqlite_database, second_candidate)
            
            if not are_equal(answer1.result, answer2.result):
                break
        
    dict_to_publish = {}
    dict_to_publish['database'] = db_name 
    dict_to_publish['sql1'] = first_candidate
    dict_to_publish['sql2'] = second_candidate
    dict_to_publish['first_cols'] = count_sql_columns(first_candidate)
    dict_to_publish['second_cols'] = count_sql_columns(second_candidate)
    dict_to_publish['instance'] = "\n".join(insert_statements)
    dict_to_publish['instance_as_dict'] = rows_as_dictionary
                
    return dict_to_publish
            

        
                
                
                
                






