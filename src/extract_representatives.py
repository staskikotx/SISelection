from config import *
from sql_execution import execute_sql_with_timeout, normalize_sql, is_valid_execution_result, measure_sql_execution_time
import pickle
from collections import defaultdict

import warnings
warnings.filterwarnings("error")

def has_subquery_in_where(sql):
    """Check if SQL query contains a subquery in the WHERE clause."""
    if not isinstance(sql, str) or not sql.strip():
        return False
    
    # Normalize SQL (lowercase, clean whitespace, remove comments)
    sql = re.sub(r'/\*.*?\*/|--.*?$|\s+', ' ', sql, flags=re.DOTALL).lower().strip()
    
    # Extract WHERE clause content
    where_match = re.search(r'\bwhere\b\s*(.*?)(?=\s+(?:group|order|having|limit|$)|$)', sql)
    if not where_match:
        return False
    
    # Check for SELECT inside parentheses within WHERE
    depth = 0
    for i, char in enumerate(where_match.group(1)):
        if char == '(': depth += 1
        elif char == ')': depth = max(0, depth - 1)
        elif i+6 <= len(where_match.group(1)) and where_match.group(1)[i:i+6] == 'select':
            # Verify it's a standalone keyword inside parentheses
            if depth > 0 and (i == 0 or not where_match.group(1)[i-1].isalnum()) \
                and (i+6 == len(where_match.group(1)) or not where_match.group(1)[i+6].isalnum()):
                return True
    return False


def normal_form(sql):
    return normalize_sql(sql).replace('"', '`')

def extract_representatives(all_candidates, db_path):
    
    grouped_by_result = defaultdict(list)
    
    # there are many equal pairs of candidates, we group them by their pretty form
    grouped_by_pretty_form = {}
    for candidate in all_candidates:
        sql_query = normalize_sql(candidate).replace('"', '`')
        if 'from' not in sql_query.lower():
            continue
        if sql_query in grouped_by_pretty_form:
            grouped_by_pretty_form[sql_query] += 1
        else:
            grouped_by_pretty_form[sql_query] = 1
    for sql_query, occurences in grouped_by_pretty_form.items():
        execution_result = execute_sql_with_timeout(db_path, sql_query)
        if is_valid_execution_result(execution_result):
            execution_time = measure_sql_execution_time(db_path, sql_query)
            grouped_by_result[result_to_normal_form(execution_result.result)]+= [(sql_query, execution_time) for i in range(occurences)]
    
    

    if len(grouped_by_result) == 0:
        # AlphaSQL yielded no working sql queries. Kaput. There is nothing we can do
        return []

    if len(grouped_by_result) == 1:
        # all given queries are equivalent. Choose the random one (or fastest!) for the answer.
        candidates_list = next(iter(grouped_by_result.values()))
        # Select fastest query in the group
        fastest_query = min(candidates_list, key=lambda x: x[1])[0]
        return [fastest_query]

    representatives = []
    for group in sorted(list(grouped_by_result.values()), key = lambda x: len(x), reverse = True):
        # Split group into queries with and without subqueries in WHERE
        without_subquery = [item for item in group if not has_subquery_in_where(item[0])]
        
        # Prefer queries without subqueries in WHERE (if available)
        if without_subquery:
            representative_sql = min(without_subquery, key=lambda x: x[1])[0]
        else:
            representative_sql = min(group, key=lambda x: x[1])[0]
        
        representatives.append(representative_sql)
    
    
    return representatives 


            