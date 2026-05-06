from selection import select
from config import *
from sql_execution import execute_sql_with_timeout, is_valid_execution_result

def build_task_data(question, hint, db_name) :
    return {
        "path_to_schema" : f"{PATH_TO_SCHEMAS}{db_name}.sql",
        "path_to_db" : f"{PATH_TO_DBS}{db_name}/{db_name}.sqlite",
        "db_name" : db_name,
        "question" : question,
        "hint" : hint
    }
 
def chosen_sql_is_equal_to_gold_sql(sql, gold_sql, db_path):
    our_answer = execute_sql_with_timeout(db_path, sql)
    gold_answer = execute_sql_with_timeout(db_path, gold_sql)

    if not is_valid_execution_result(gold_answer):
        raise Exception("\nGold_sql execution result is not valid\n")
    if not is_valid_execution_result(our_answer):
        raise Exception("\nChosen_sql execution result is not valid\n")
    return are_equal(our_answer.result, gold_answer.result)

############# Test 1 ############

candidates = [
    "SELECT COUNT(*) FROM district INNER JOIN account ON district.district_id = account.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'",
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'east Bohemia'"
]

task_data = build_task_data(
    question = "How many accounts who choose issuance after transaction are staying in East Bohemia region?",
    hint = "A3 contains the data of region; 'POPLATEK PO OBRATU' represents for 'issuance after transaction'.",
    db_name = "financial"
)

status, query_or_message = select(candidates, task_data)


print(status, query_or_message)

assert(status == True)

assert chosen_sql_is_equal_to_gold_sql(query_or_message, candidates[1], task_data["path_to_db"]),  f"Expected \n{query_or_message}\n to be equal to gold_sql: \n{candidates[1]}"

############# Test 2 ############

candidates = [
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'",
    "SELECT DISTINCT `cards`.`layout` FROM `cards` WHERE `cards`.`keywords` = 'Flying'"
]

task_data = build_task_data(
    question = "What can be the card layout of cards with keyword of flying?",
    hint = "",
    db_name = "card_games"
)

status, query_or_message = select(candidates, task_data)


print(status, query_or_message)

assert(status == True)

assert chosen_sql_is_equal_to_gold_sql(query_or_message, candidates[0], task_data["path_to_db"]),  f"Expected \n{query_or_message}\n to be equal to gold_sql: \n{candidates[0]}"

############# Test 3 ############

candidates = [
    "SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60",
    "SELECT t1.loan_id, t3.a2, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60",
    "SELECT loan.loan_id, account.district_id, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60"
]

task_data = build_task_data(
    question = "List the loan ID, district and average salary for loan with duration of 60 months.",
    hint = "A3 refers to regions; A11 refers to average salary",
    db_name = "financial"
)

status, query_or_message = select(candidates, task_data)


print(status, query_or_message)

assert(status == True)

assert chosen_sql_is_equal_to_gold_sql(query_or_message, candidates[1], task_data["path_to_db"]),  f"Expected \n{query_or_message}\n to be equal to gold_sql: \n{candidates[1]}"


print('\033[92mSuccess\033[0m')