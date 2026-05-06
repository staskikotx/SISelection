from config import *
import pandas as pd
import os
from collections import defaultdict

def extract_json_from_response(text) :
    if '</think>' in text:
        text = text.split('</think>')[-1]
    
    if '```json' in text:
        text = text.split('```json')[-1]
        text = text.split('```')[0]
    
    return text

################################################################################################

def build_filter_info(sql1, sql2, instance_as_dict):
    info = defaultdict(set)

    for row_name, row_dict in instance_as_dict.items():
        table_name = ('_').join(row_name.split('_')[3:-1])

        for column_name in row_dict.keys():
            if column_name.lower() in sql1.lower() or column_name.lower() in sql2.lower():
                info[table_name].add(column_name)

    return info


def filter_schema_file(unfiltered_schema, filter_info) : 
    if filter_info == None:
        return unfiltered_schema

    lines = unfiltered_schema.split('\n')
    filtered_lines = []
    current_table = None
    for line in lines:
        match = re.search(r'CREATE TABLE (`\w+`)', line.strip(), re.IGNORECASE)
        if match:
            table_name = match.group(1)
            current_table = table_name.strip('`').lower()
            if current_table in filter_info:
                filtered_lines.append(line) 
        elif ');' in line:
            if current_table in filter_info:
                filtered_lines.append(line)
                current_table = None
        else:
            if current_table in filter_info: # FOREIGN KEY (`CDSCode`) REFERENCES `schools`(`CDSCode`)
                fk_match = re.search(r'^FOREIGN KEY \(`(\w+)`\) REFERENCES `(\w+)`\(`(\w+)`\)', line.strip())                
                if fk_match:
                    col_name = fk_match.group(1).lower()
                    reference_table_name = fk_match.group(2).lower()
                    if col_name in filter_info[current_table] and reference_table_name in filter_info :
                        filtered_lines.append(line)
                    continue

                col_match = re.search(r'`([^`]+)`\s+(\w+),', line.strip())
                if col_match:
                    col_name = col_match.group(1)
                    if ' ' not in col_name and '-' not in col_name:
                        col_name = col_name.lower()
                    if col_name in filter_info[current_table] :
                        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def get_table_name_from_key(row_description) :
    row_description_match = re.search(r'^row_(\d+)_of_(\w+)_table', row_description)
    if row_description_match:
        table_name = row_description_match.group(2).lower()   
        return table_name
    else :
        return None   

def remove_table_suffix(descr):
    return descr[:-6]

def filter_instance_as_dict(instance_as_dict, filter_info) :
    if filter_info == None:
        return instance_as_dict

    filtered_instance = {}
    for (row_description, row_values) in instance_as_dict.items():
        table_name = get_table_name_from_key(row_description)
        filtered_row_values = {}
        for (column, value) in row_values.items():
            if column in filter_info[table_name]:
                filtered_row_values[column] = value
        filtered_instance[remove_table_suffix(row_description)] = filtered_row_values
    return filtered_instance




################################################################################################

def get_prompt(pair_data, i, j, db_schema, question, hint, prompt_template):
           
    schema = db_schema
    filter_info = build_filter_info(pair_data['sql1'], pair_data['sql2'], pair_data["instance_as_dict"])
    schema = filter_schema_file(schema, filter_info)    
    question = question
    hint = hint
    modified_instance = filter_instance_as_dict(pair_data['instance_as_dict'], filter_info)
    #print(filter_info, "\n")
    print('Instance:', modified_instance)
    #print("schema:", schema)
    tuple_length = pair_data['first_cols']
    prompt = prompt_template.format(**locals())

    return prompt

    


