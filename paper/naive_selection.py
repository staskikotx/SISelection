from config import *
import pandas as pd
import os
from batch_sender_2 import make_batch_query
from collections import defaultdict

def extract_json_from_response(text) :
    if '</think>' in text:
        text = text.split('</think>')[-1]
    
    if '```json' in text:
        text = text.split('```json')[-1]
        text = text.split('```')[0]
    
    return text


################################################################################################


original_data = read_bird_json()
database_to_schema_text = read_database_to_schema_text()
candidates = read_initial_representatives()

with open(PATH_TO_SELECTION_PROMPT_TEMPLATE, 'r', encoding='utf-8') as file:
    prompt_template = file.read()

tasks_to_process = []
with open(f'{PATH_TO_DATA}/good_sr_tasks.json', 'r') as f:
    tasks_to_process = json.load(f)

###########################
# tasks_to_process = [1061]
#############################

selection_results = {task:[] for task in tasks_to_process}

cases_with_no_response_json = []

# Start processing
for attempt in range(NUMBER_OF_ATTEMPTS_FOR_LLM):

    data = {'question_id': [], 'prompt': [] }

    number_of_prompts = 0
    affected_tasks = set()

    for question_id in tqdm(tasks_to_process):
        print(f'Reading task {question_id}')
        
        number_of_candidates = len(candidates[question_id])

        
        DB_SCHEMA = database_to_schema_text[original_data[question_id]['db_id']]
        QUESTION = original_data[question_id]['question']
        KNOWLEDGE_EVIDENCE = original_data[question_id]['evidence']
        SQL_QUERIES = candidates[question_id]

        prompt = prompt_template.format(**locals())

        # print(prompt)

        data['question_id'].append(question_id)
        data['prompt'].append(prompt)

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
            prompt = batch_df['prompt'].iloc[local_index]
            
            # Extract response_json from output_text
            response_json = ""
            try:
                response_json = extract_json_from_response(output_text)
                response_dict = json.loads(response_json)
                selection_results[question_id].append(response_dict['sql'])
                print("\n\nGood response_json for question_id ", question_id)
            except:
                print("\n\nNo response_json for question_id ", question_id)
                cases_with_no_response_json.append(question_id)
                

            with open(f"{PATH_TO_BASE}/{question_id}/bl_response_{attempt}.json", "w", encoding="utf-8") as f:
                f.write(response_json)

# Postprocessing: majority voting with tie breaking

import statistics

selection_result = {}
for task in tasks_to_process:
    try:
        selection_result[str(task)] = statistics.mode(selection_results[task])
    except:
        selection_result[str(task)] = candidates[task][0]    


print(f"\n These are {len(cases_with_no_response_json)} cases with no response json:{cases_with_no_response_json}\n")

with open(f"baseline.json", "w", encoding="utf-8") as f:
    json.dump(selection_result, f, indent=2, ensure_ascii=False)




    


