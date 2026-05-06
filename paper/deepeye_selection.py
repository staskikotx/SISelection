from config import *
import pandas as pd
import os
from batch_sender_2 import make_batch_query
from alphasql.database.sql_execution import execute_sql_with_timeout, format_execution_result
from collections import defaultdict

def extract_json_from_response(text) :
    if '</think>' in text:
        text = text.split('</think>')[-1]
    
    if '```json' in text:
        text = text.split('```json')[-1]
        text = text.split('```')[0]
    
    return text

def build_result_string(database, sql) :
    db_path = f"{PATH_TO_DB}/{database}/{database}.sqlite"
    result = execute_sql_with_timeout(db_path, sql)
    return format_execution_result(result)
        

################################################################################################

original_data = read_bird_json()
database_to_schema_text = read_database_to_schema_text()
candidates = read_rewritten_representatives()

with open(PATH_TO_DEEPEYE_PROMPT_TEMPLATE, 'r', encoding='utf-8') as file:
    prompt_template = file.read()

tasks_to_process = []
with open(f'{PATH_TO_DATA}/good_sr_tasks.json', 'r') as f:
    tasks_to_process = json.load(f)

###########################
# tasks_to_process = [1]
#############################

# Start processing
for attempt in tqdm(range(NUMBER_OF_ATTEMPTS_FOR_LLM)):
    data = {'question_id': [], 'i': [], 'j': [], 'prompt': [], 'status': []}

    scheduled_for_deletion = []

    number_of_prompts = 0
    affected_tasks = set()

    cases_with_no_response_json = []

    is_first = True

    for question_id in tqdm(tasks_to_process):
        print(f'Reading task {question_id}')
        
        number_of_candidates = len(candidates[question_id]["queries"])

        for i in range(number_of_candidates):
            for j in range(i + 1, number_of_candidates):
                with open(f'{PATH_TO_BASE}/{question_id}/{i}_{j}.json', 'r') as file:
                    pair_data = json.load(file)
                    
                    DATABASE_SCHEMA = database_to_schema_text[pair_data['database']]
                    QUESTION = original_data[question_id]['question']
                    HINT = original_data[question_id]['evidence']
                    QUERY_A = pair_data['sql1']
                    RESULT_A = build_result_string(pair_data['database'], QUERY_A)
                    QUERY_B = pair_data['sql2']
                    RESULT_B = build_result_string(pair_data['database'], QUERY_B)
                    
                    prompt = prompt_template.format(**locals())

                    if is_first:
                        print(prompt)
                        is_first = False

                    data['question_id'].append(question_id)
                    data['i'].append(i)
                    data['j'].append(j)
                    data['prompt'].append(prompt)
                    data['status'].append(pair_data['status'])
                    number_of_prompts += 1
                    affected_tasks.add(question_id)
                        
    print(f'There will be {number_of_prompts} prompts to the LLM for tasks {affected_tasks}')

    df = pd.DataFrame(data)

    batch_size = 20
    for batch_num, batch_df in tqdm(df.groupby(df.index // batch_size)):

        print(f"Processing batch {batch_num} ({len(batch_df)} rows)")
        
        # Generate formatted prompts
        prompts = batch_df['prompt']
        
        # Get LLM responses
        output_texts = make_batch_query(prompts)

        # Update files
        for local_index, output_text in enumerate(output_texts):
            question_id = batch_df['question_id'].iloc[local_index]
            i = batch_df['i'].iloc[local_index]
            j = batch_df['j'].iloc[local_index]
            prompt = batch_df['prompt'].iloc[local_index]
            
            # Extract response_json from output_text
            response_json = ""
            try:
                response_json = extract_json_from_response(output_text)
            except:
                print("\n\n\n\nNo response_json for Theorem \n\n\n\n", global_index)
                cases_with_no_response_json.append((question_id, i, j))


            with open(f"{PATH_TO_BASE}/{question_id}/de_response_{i}_{j}_att_{attempt}.json", "w", encoding="utf-8") as f:
                f.write(response_json)

            with open(f"{PATH_TO_BASE}/{question_id}/de_output_{i}_{j}_att_{attempt}.txt", "w", encoding="utf-8") as f:
                f.write(output_text)

            with open(f"{PATH_TO_BASE}/{question_id}/de_prompt_{i}_{j}_att_{attempt}.txt", "w", encoding="utf-8") as f:
                f.write(prompt)
        


print(f"\n These are {len(cases_with_no_response_json)} cases with no response json:{cases_with_no_response_json}\n")

def remove_if_exists(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

for (task, i, j) in scheduled_for_deletion:
    for attempt in range(NUMBER_OF_ATTEMPTS_FOR_LLM):
        remove_if_exists("{PATH_TO_BASE}/{question_id}/de_response_{i}_{j}_att_{attempt}.json")
        remove_if_exists("{PATH_TO_BASE}/{question_id}/de_output_{i}_{j}_att_{attempt}.json") 
        remove_if_exists("{PATH_TO_BASE}/{question_id}/de_prompt_{i}_{j}_att_{attempt}.json") 



    


