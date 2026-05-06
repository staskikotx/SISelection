from config import *
import psycopg2
from psycopg2 import sql
import sqlglot
from collections import defaultdict

# вызывается с from_index, указывающим на дельту, корректно убирает
# её и все её под-дельты
# возвращает индекс следующего элемента после самой внешней удалённой
# закрывающей скобки
def remove_nested_delta(term, string_as_list, from_index):
    i = from_index
    i+=2
    bracket_sum = 1
    while(bracket_sum > 0):
        if term[i] == 'δ':
            i = remove_nested_delta(term, string_as_list, i)
            continue
        
        if term[i] == '(':
            bracket_sum+=1
        elif term[i] == ')':
            bracket_sum-=1
        string_as_list.append(term[i])
        i+=1
    # вышли из цикла, не забываем удалить закрывающую дельту скобку
    string_as_list.pop()
    return i

def remove_delta(term):

    string_as_list = []

    # полу-костыль, чтобы всё отработало за один вызов
    term = 'δ(' + term.strip() + ')'

    remove_nested_delta(term, string_as_list, 0)
    return ("".join(string_as_list)).strip()


# вызывается с from_index, указывающим на открывающую скобку, корректно убирает
# её, её закрывающую скобку и все под-пары скобок
# возвращает индекс следующего элемента после самой внешней удалённой
# закрывающей скобки
def remove_nested_brackets(term, string_as_list, from_index):
    i = from_index
    i+=1
    while(term[i] != ')'):
        if term[i] == '(':
            i = remove_nested_brackets(term, string_as_list, i)
            continue
        else:
            string_as_list.append(term[i])
            i+=1
    return i+1

def remove_brackets(term):
    string_as_list = []

    # полу-костыль, чтобы всё отработало за один вызов
    term = '(' + term.strip() + ')'

    remove_nested_brackets(term, string_as_list, 0)
    return ("".join(string_as_list)).strip()



def parse_provenance(term):
    
    # Handle optional δ(...) wrapper and brackets
    term = remove_delta(term)
    term = remove_brackets(term)
    #отдельно обрабатываем zero-provenance-term:
    if term == '𝟙':
        return []

    # Split into product terms by ⊕
    product_terms = term.split('⊕')

    result = []
    for pt in product_terms:
        # Split into individual terms by ⊗   
        elements = pt.split('⊗')
        product_dict = defaultdict(list)
        for el in elements:
            # Clean up any internal whitespace
            key, val = el.strip().split('-')
            if int(val) not in product_dict[key]:
                product_dict[key].append(int(val))     
        result.append(product_dict)
    
    return result

####################################################################################################
def extract_provenance_from_postgres_tables(database_name, table_name_prefix, candidate_index):
    
    database = "prov_" + database_name 
    table_name = f"{table_name_prefix}_{candidate_index}"

    prov = []

    print(f"Getting provenance info from ", table_name)
    with psycopg2.connect(
        host=HOST,
        dbname=database,
        user=USER
    ) as conn:
        with conn.cursor() as cur:

            cur.execute(
                sql.SQL(f"set search_path to public, provsql;")
            )

            cur.execute(
                sql.SQL(f"select *, sr_formula(provenance(),'provenance_mapping') from {table_name};")
            )
            
            if cur.rowcount == 1:
                record = cur.fetchone()
                the_only_provenance = parse_provenance(record[-2])
                
                if the_only_provenance:
                    prov = the_only_provenance
                else:
                    # empty provenance, empty answer
                    prov = []
                    
            # other cases, arbitrary family of ancestors will be chosen for each row (random dict from list for each row)
            else :
                for record in cur:
                    prov += parse_provenance(record[-2])
    return prov
                
                

                    
                    




