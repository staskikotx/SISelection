from .qualify import SQLQualifier
from .rewrite_query import rewrite_sql
from .eq2in import convert_eq_sublinks_to_in
from .minmax2limit import convert_minmax_subqueries_to_orderby

def rewrite(query, path_to_database):
    qualifier = SQLQualifier(path_to_database, dialect='postgres')
    temp_query_1 = qualifier.qualify_columns(query, output_dialect='postgres')
    temp_query_2 = convert_minmax_subqueries_to_orderby(temp_query_1)
    temp_query_3 = convert_eq_sublinks_to_in(temp_query_2)
    temp_query_4 = rewrite_sql(temp_query_3)
    return temp_query_4

