from rewrite_candidates import rewrite_representatives
from check_if_task_is_good_for_postgres import check_if_task_is_good_for_postgres
from create_postgres_tables import create_postgres_tables
from extract_provenance_from_postgres_tables import extract_provenance_from_postgres_tables
from tournament import run_tournament_concurrent
from calculate_score_table import calculate_score_table
from config import *

def select(representatives, task_data): 
    # return a pair (status, query_or_message)
    # status is True if the selection using separating instances worked successfully
    #        is False if the selection using separating instances is inapplicable
    #        is None if the selection does not make sense, that is, there is <= 1 candidates after rewriting       
    
    if len(representatives) <= 1:
        return None, "There are not sufficiently many candidates to run selection"

    try:
        with open(task_data['path_to_schema'], 'rt') as f:
            db_schema = f.read()
    except Exception as e:
        print(str(e))
        return False, "Invalid path to database schema"

    postgres_representatives, initial_indices = rewrite_representatives(representatives, task_data['path_to_schema'])
    
    task_is_good_for_postgres = check_if_task_is_good_for_postgres(postgres_representatives, task_data['db_name']) # evaluate_everything_with_select
    
    if not task_is_good_for_postgres:
        return False, "Method unapplicable because some candidates are not Postgres-valid"
    
    try:
        create_postgres_tables(postgres_representatives, task_data['db_name'], TABLE_PREFIX) #evaluate_everything_with_create_table
        task_is_good_for_provsql = True
    except Exception as e:
        print(str(e))
        task_is_good_for_provsql = False
    
    if not task_is_good_for_provsql:
        return False, "Method unapplicable because the candidates are not ProvSQL-valid"
    
    try:
        provenance = [extract_provenance_from_postgres_tables(task_data['db_name'], TABLE_PREFIX, index) 
            for index in range(len(postgres_representatives))] #evaluate_good_with_sr_formula
        task_is_good_for_getting_provenance = True
    except Exception as e:
        print(str(e))
        task_is_good_for_getting_provenance = False
    
    if not task_is_good_for_getting_provenance:
        return False, "Method unapplicable because there is a problem with getting and parsing provenance"
    
    print(provenance)

    try:
        with open(PATH_TO_PROMPT_TEMPLATE, 'rt') as f:
            prompt_template = f.read()
    except Exception as e:
        print(str(e))
        return False, "Invalid path to prompt template"


    tournament_table = run_tournament_concurrent(
        postgres_representatives=postgres_representatives,
        representatives=representatives,
        initial_indices=initial_indices,
        db_schema=db_schema,
        db_name=task_data['db_name'],
        question=task_data['question'],
        hint=task_data['hint'],
        prompt_template=prompt_template,
        prov=provenance,
        max_workers=10  # Adjust based on your LLM server capacity
    )

    score_table = calculate_score_table(tournament_table, initial_indices, len(representatives))

    print('Score table:', score_table)

    worthy = sorted([idx for idx in range(len(score_table)) if score_table[idx] > -1], key = lambda x: score_table[x],reverse = True)

    if len(worthy) == 0:
        return False, "Method unapplicable because tournament table contains only -1 (how can that be?)"
    else:
        best_nle = [idx for idx in worthy if score_table[idx] == score_table[worthy[0]]]

    if len(best_nle) > 1:
        return False, "Method unapplicable because there are multiple winners in the tournament table"
    else :
        return True, representatives[best_nle[0]]
    




    