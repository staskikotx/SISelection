from selection import select
from config import *
from sql_execution import execute_sql_with_timeout, is_valid_execution_result
from extract_representatives import extract_representatives


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
#question_id = 89
candidates = ["SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'",
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'east Bohemia'", 
    "SELECT COUNT(DISTINCT account.account_id) AS account_count FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'east Bohemia'", "SELECT COUNT(*) FROM district INNER JOIN account ON district.district_id = account.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM district INNER JOIN account ON district.district_id = account.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) AS account_count FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) AS account_count FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 LIKE '%East Bohemia%'", 
    "SELECT COUNT(DISTINCT account_id) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 LIKE '%east bohemia%'",
    "SELECT COUNT(DISTINCT account_id) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 LIKE '%east bohemia%'", 
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'",
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'", 
    "SELECT COUNT(t1.account_id) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account AS t1 JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'",
    "SELECT COUNT(DISTINCT account_id) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'",
    "SELECT COUNT(DISTINCT account_id) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'",
    "SELECT COUNT(DISTINCT t1.account_id) AS num_accounts FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t2.a3 = 'East Bohemia' AND t1.frequency = 'POPLATEK PO OBRATU'",
    "SELECT COUNT(t1.account_id) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t2.a3 = 'East Bohemia' AND t1.frequency = 'POPLATEK PO OBRATU'", 
    "SELECT COUNT(t1.account_id) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t2.a3 = 'East Bohemia' AND t1.frequency = 'POPLATEK PO OBRATU'",
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE district.a3 = 'East Bohemia' AND account.frequency = 'POPLATEK PO OBRATU'", 
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE district.a3 = 'East Bohemia' AND account.frequency = 'POPLATEK PO OBRATU'", 
    "SELECT COUNT(*) FROM account AS t1 INNER JOIN district AS t2 ON t1.district_id = t2.district_id WHERE t1.frequency = 'POPLATEK PO OBRATU' AND t2.a3 = 'East Bohemia'",
    "SELECT COUNT(account.account_id) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'",
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'", 
    "SELECT COUNT(*) FROM account INNER JOIN district ON account.district_id = district.district_id WHERE account.frequency = 'POPLATEK PO OBRATU' AND district.a3 = 'East Bohemia'"]

task_data = build_task_data(
    question = "How many accounts who choose issuance after transaction are staying in East Bohemia region?",
    hint = "A3 contains the data of region; 'POPLATEK PO OBRATU' represents for 'issuance after transaction'.",
    db_name = "financial"
)

representatives = extract_representatives(candidates, task_data["path_to_db"])
status, query_or_message = select(representatives, task_data)

print(status, query_or_message)

assert(status == True)
gold_sql = "SELECT COUNT(T2.account_id) FROM district AS T1 INNER JOIN account AS T2 ON T1.district_id = T2.district_id WHERE T1.A3 = 'east Bohemia' AND T2.frequency = 'POPLATEK PO OBRATU'"
assert chosen_sql_is_equal_to_gold_sql(query_or_message, gold_sql, task_data["path_to_db"]),  f"Expected \n{query_or_message}\n to be equal to gold_sql: \n{gold_sql}"






############# Test 2 ############
#question_id = 376
candidates = ["SELECT layout FROM cards WHERE keywords LIKE '%flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'",
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT DISTINCT cards.layout FROM cards WHERE cards.keywords LIKE '%Flying%'", 
    "SELECT DISTINCT cards.layout FROM cards WHERE cards.keywords LIKE '%Flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT layout FROM cards WHERE keywords = 'Flying'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%' OR keywords LIKE '%flying%'",
    'SELECT DISTINCT "cards"."layout" FROM "cards" WHERE "cards"."keywords" LIKE \'%Flying%\'', 
    'SELECT DISTINCT "cards"."layout" FROM "cards" WHERE "cards"."keywords" = \'Flying\'',
    "SELECT layout FROM cards WHERE keywords LIKE '%Flying%'",
    "SELECT layout FROM cards WHERE INSTR(',' || keywords || ',', ',Flying,') > 0",
    "SELECT layout FROM cards WHERE keywords LIKE '%flying%' OR keywords LIKE '%Flying%' OR keywords LIKE '%FLYING%' OR keywords LIKE '%flying,%' OR keywords LIKE '%,flying%' OR keywords LIKE '%,flying,%' OR keywords LIKE '%Flying,%' OR keywords LIKE '%,Flying%' OR keywords LIKE '%,Flying,%' OR keywords LIKE '%FLYING,%' OR keywords LIKE '%,FLYING%' OR keywords LIKE '%,FLYING,%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%flying%'", 
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'",
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'", 
    "SELECT layout FROM cards WHERE keywords LIKE '%Flying%'",
    "SELECT layout FROM cards WHERE LOWER(keywords) LIKE '%flying%'",
    "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'"]

task_data = build_task_data(
    question = "What are the card layout of cards with keyword of flying?",
    hint = "",
    db_name = "card_games"
)

representatives = extract_representatives(candidates, task_data["path_to_db"])
status, query_or_message = select(representatives, task_data)

print(status, query_or_message)

assert(status == True)
gold_sql = "SELECT DISTINCT layout FROM cards WHERE keywords LIKE '%Flying%'"
assert chosen_sql_is_equal_to_gold_sql(query_or_message, gold_sql, task_data["path_to_db"]),  f"Expected \n{query_or_message}\n to be equal to gold_sql: \n{gold_sql}"







############# Test 3 ############
#question_id = 124
candidates = ['SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT t1.loan_id, t3.a2, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan_id, a3, a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan_id, a3, a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN disp ON loan.account_id = disp.account_id INNER JOIN account ON disp.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN disp ON loan.account_id = disp.account_id INNER JOIN account ON disp.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT DISTINCT t1.loan_id, t3.a3, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60', 
    'SELECT DISTINCT t1.loan_id, t3.a3, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60',
    'SELECT t1.loan_id, t3.a3, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60',
    'SELECT t1.loan_id, t3.a3, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60', 
    'SELECT l.loan_id, d.a3, d.a11 FROM loan AS l INNER JOIN account AS a ON l.account_id = a.account_id INNER JOIN district AS d ON a.district_id = d.district_id WHERE l.duration = 60',
    'SELECT loan.loan_id, district.a3 AS district, district.a11 AS average_salary FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN district ON loan.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan.loan_id, district.a3 AS district, district.a11 AS average_salary FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, district.a3 AS district, district.a11 AS average_salary FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT t1.loan_id, t3.a3, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60', 
    'SELECT t1.loan_id, t3.a3, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60', 
    'SELECT loan.loan_id, district.a3, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60',
    'SELECT loan.loan_id, account.district_id, district.a11 FROM loan INNER JOIN account ON loan.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE loan.duration = 60', 
    'SELECT t1.loan_id, t3.a3, t3.a11 FROM loan AS t1 INNER JOIN account AS t2 ON t1.account_id = t2.account_id INNER JOIN district AS t3 ON t2.district_id = t3.district_id WHERE t1.duration = 60']

task_data = build_task_data(
    question = "List the loan ID, district and average salary for loan with duration of 60 months.",
    hint = "A3 refers to regions; A11 refers to average salary",
    db_name = "financial"
)

representatives = extract_representatives(candidates, task_data["path_to_db"])
status, query_or_message = select(representatives, task_data)

print(status, query_or_message)

assert(status == True)
gold_sql = "SELECT T3.loan_id, T2.A2, T2.A11 FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id INNER JOIN loan AS T3 ON T1.account_id = T3.account_id WHERE T3.duration = 60"
assert chosen_sql_is_equal_to_gold_sql(query_or_message, gold_sql, task_data["path_to_db"]),  f"Expected \n{query_or_message}\n to be equal to gold_sql: \n{gold_sql}"


print('\033[92mSuccess\033[0m')

