from config import *
from sql_execution import execute_sql_on_string_with_timeout
from custom_tools import convert_postgres_database_to_sqlite, CustomJSONEncoder


def check_instance(pair_data, database_schema):
    if pair_data["instance"]:
        database = database_schema + pair_data['instance']
        
        sqlite_database = convert_postgres_database_to_sqlite(database)
        
        try:
            #print("First candidate:", get_sqlite_candidate_by_index(i))
            answer1 = execute_sql_on_string_with_timeout(sqlite_database, pair_data['sql1'])
            answer1set = result_to_normal_form(answer1.result) # unused by design, but causes exception if answer.result is None
        except:
            answer1 = None

        try:
            #print("Second candidate:", get_sqlite_candidate_by_index(j))
            answer2 = execute_sql_on_string_with_timeout(sqlite_database, pair_data['sql2'])
            answer2set =result_to_normal_form(answer2.result) # unused by design, but causes exception if answer.result is None
        except:
            answer2 = None
        
        answers = [answer1, answer2]

        print('Answers in check_instance:', answer1set, answer2set)

        if answer1 is None or answer2 is None:
            if answer1 is None and answer2 is None:
                verdict = 'INS-E'
            elif answer1 is None and answer2 is not None:
                verdict = 'SEP-E'
            else:
                verdict = 'SEP-E'
        else: # Main case: both answers are correctly evaluated
            
            queries_give_same_answers = are_equal(answer1.result, answer2.result)

            if queries_give_same_answers :
                verdict = 'INS-C'
            else:
                verdict = 'SEP-C'
    else:
        verdict = 'INS-E'
    
    return verdict


                                    
                                
                            