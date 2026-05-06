from config import *
import ast
import pandas as pd
from sql_execution import execute_sql_on_string_with_timeout
from custom_tools import convert_postgres_database_to_sqlite
from collections import defaultdict

def to_lower(original_data):
        return [[s.lower() if isinstance(s, str) else s for s in inner_list] for inner_list in original_data]

'''def fix_json_file(file_path):
    """Converts single-quoted JSON-like files to valid JSON"""
    with open(file_path, 'r') as f:
        try:
            # Parse as Python literal (handles single quotes properly)
            data = ast.literal_eval(f.read())
            
            # Write back as valid JSON
            with open(file_path + "f", 'w') as out_f:
                json.dump(data, out_f, indent=2)
            return True
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False'''

'''def fix_json_file(file_path):
    """Converts single-quoted JSON-like files to valid JSON"""
    with open(file_path, 'r') as f:
        try:
            response_dict = json.load(f)
            bad_string = 'Ancestor\'s Chosen'
            good_string = 
            response_dict["chain_of_thought_reasoning"]
            # Parse as Python literal (handles single quotes properly)
            return True
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False'''

def count_unique_unhashable(seq):
    unique = []
    for item in seq:
        if not any(item == x for x in unique):
            unique.append(item)
    return len(unique)

################################################################################################

def get_duel_result(pair_data, llm_answers, db_schema):

    database = db_schema + pair_data['instance']
    #print('Old Database:')
    #print(database)
    #print()

    sqlite_database = convert_postgres_database_to_sqlite(database)
    #print('Modified Database:')
    #print(sqlite_database)
    #print()
    #print('Queries:')
    #for index, query in enumerate(rewritten_candidates[question_id]):
    #    print(f"SQLite Candidate {index}:", get_sqlite_candidate_by_index(index))
    
    responses = llm_answers
    
    try:
        #print("First candidate:", get_sqlite_candidate_by_index(i))
        answer1 = execute_sql_on_string_with_timeout(sqlite_database, pair_data['sql1'])
        answer1set = result_to_normal_form(answer1.result) # unused by design, but causes exception if answer.result is None
    except:
        answer1 = None

    try:
        #print("Second candidate:", get_sqlite_candidate_by_index(j))
        answer2 = execute_sql_on_string_with_timeout(sqlite_database, pair_data['sql2'])
        answer2set = result_to_normal_form(answer2.result) # unused by design, but causes exception if answer.result is None
    except:
        answer2 = None
    
    answers = [answer1, answer2]

    if answer1 is None or answer2 is None:
        if answer1 is None and answer2 is None:
            winner = 'NONE'
        elif answer1 is None and answer2 is not None:
            winner = 'B'
        else:
            winner = 'A'
    else: # Main case: both answers are correctly evaluated
        
        if len(responses) == 0 :
            winner = 'NONE'
        else :
            print(len(responses), 'responses with correct json. Here they are:', responses)
            
            score = [0,0]
            
            for candidate_index in [0,1]:
                pred_answer = answers[candidate_index]
                for llm_answer in responses:
                    this_query_is_correct = pred_answer.result_type.value == "success" and are_equal(pred_answer.result, llm_answer)
                    if this_query_is_correct:
                        score[candidate_index] += 1
                    print('Pred:',  result_to_normal_form(pred_answer.result))
                    print('LLM:',  result_to_normal_form(llm_answer))
                    print("This query is correct:", this_query_is_correct) 

                
            if score[0] > score[1] :
                winner = 'A'
            elif score[0] < score[1]:
                winner = 'B'
            elif score[0] > 0 : # here assume that score[0] == score[1]
                winner = 'AB'
            else:
                winner = 'NONE'
            
    answer1 = answers[0].result if answers[0] is not None else None
    answer2 = answers[1].result if answers[1] is not None else None
    result1 = answers[0].result_type.value if answers[0] is not None else None
    result2 = answers[1].result_type.value if answers[1] is not None else None

    dict_to_publish = {}
    dict_to_publish['sql1'] = pair_data['sql1']
    dict_to_publish['sql2'] = pair_data['sql2']
    dict_to_publish['status'] = pair_data['status']
    dict_to_publish['winner'] = winner
    dict_to_publish['answer1'] = answer1
    dict_to_publish['answer2'] = answer2
    dict_to_publish['result1'] = result1
    dict_to_publish['result2'] = result2
    dict_to_publish['expected_answer'] = responses
    
    return dict_to_publish