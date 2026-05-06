import os
import sys
import re
import glob
import json
from pathlib import Path
from tqdm import tqdm

USE_CACHED_REPRESENTATIVES = True

PATH_TO_BIRD_JSON = "/home/ashulgin/SQLVerification/data/bird/dev.json"
PATH_TO_CANDIDATES = "/home/ashulgin/SQLVerification/data/candidates/"
PATH_TO_DBS = "/home/ashulgin/SQLVerification/data/bird/dev_databases/"
PATH_TO_PROMPT_TEMPLATE = "/home/ashulgin/SQLVerification/data/prompt_template_for_nl_query_evaluation.txt"
PATH_TO_SCHEMAS = "/home/ashulgin/SQLVerification/data/bird/schemas/"
TABLE_PREFIX = "test_table_temp"
NUMBER_OF_ATTEMPTS_FOR_LLM = 3
NUMBER_OF_ATTEMPTS_FOR_SIC = 42 # SIC is separating instance construction
PATH_TO_CACHED_REPRESENTATIVES = "/home/ashulgin/SQLVerification/data/representatives"
# two parameters of connection to PostgreSQL
HOST = "/var/run/postgresql"
USER = "ashulgin"

# delete Null-rows, make order of columns and rows insignificant
def result_to_normal_form(result):
    result = [t for t in result if t!= tuple([None]*len(t))]
    return frozenset(map(frozenset, result))

def are_equal(result1, result2):
    return result_to_normal_form(result1) == result_to_normal_form(result2)