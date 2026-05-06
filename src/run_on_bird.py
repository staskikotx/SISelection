import pickle
from selection import select
from sql_execution import normalize_sql, execute_sql_with_timeout, is_valid_execution_result
from extract_representatives import extract_representatives


from config import *

############# Tools ############


def build_task_data(question, hint, db_name) :
    return {
        "path_to_schema" : f"{PATH_TO_SCHEMAS}{db_name}.sql",
        "path_to_db" : f"{PATH_TO_DBS}{db_name}/{db_name}.sqlite",
        "db_name" : db_name,
        "question" : question,
        "hint" : hint
    }

def from_bird(item):
    return build_task_data(item['question'], item['evidence'], item['db_id']) 


class ResultCounter:
    def __init__(self, name: str = "counter") -> None:
        self.name = name
        self._true_count = 0
        self._false_count = 0
        self._total_count = 0
        self._not_none_count = 0
    
    def count(self, status, query_or_message) -> None:
        """Increment counter for the given boolean value."""
        self._total_count += 1
        if status is not None:
            self._not_none_count += 1
            if status == True:
                self._true_count += 1
            elif status == False:
                self._false_count += 1
        
    def __repr__(self):
        lines = [
            f"{self._total_count} tasks processed, selection makes sense on {self._not_none_count}, "
            f"worked on {self._true_count}, did not work on {self._false_count}"
        ]
        if self._not_none_count > 0:
            coverage = self._true_count * 100 / self._not_none_count
            lines.append(f"Coverage is {coverage:.2f} percent")
        else:
            lines.append("Coverage is undefined (no valid selections)")
        return "\n".join(lines)        

def chosen_sql_is_equal_to_gold_sql(sql, gold_sql, db_path):
    our_answer = execute_sql_with_timeout(db_path, sql)
    gold_answer = execute_sql_with_timeout(db_path, gold_sql)

    if not is_valid_execution_result(gold_answer):
        raise Exception("\nGold_sql execution result is not valid\n")
    if not is_valid_execution_result(our_answer):
        raise Exception("\nChosen_sql execution result is not valid\n")
    return are_equal(our_answer.result, gold_answer.result)


# only for tasks where method worked
class EvalCounter:
    def __init__(self) -> None:
        
        self._true_right_count = 0
        self._true_wrong_count = 0
        self._true_count = 0

        # only for tasks with True
        self._cons_true_count = 0
        self._cons_false_count = 0
        
    
    def count(self, status, query_or_message, gold_sql, db_path, question_id) -> None:
        """Increment counter for the given boolean value."""
        if status:
            self._true_count += 1
            if chosen_sql_is_equal_to_gold_sql(query_or_message, gold_sql, db_path):
                self._true_right_count += 1
            else:
                self._true_wrong_count += 1

            with open(f"{PATH_TO_CACHED_REPRESENTATIVES}/{question_id}.txt", 'r') as f:
                cons_sql = f.readlines()[0]
            if chosen_sql_is_equal_to_gold_sql(cons_sql, gold_sql, db_path):
                self._cons_true_count += 1
            else:
                self._cons_false_count += 1
            
        
    def __repr__(self):
        lines = [
            f"Selection made sense on {self._true_count} tasks."
        ]
        if self._true_count > 0:
            our_accuracy = self._true_right_count * 100 / self._true_count
            lines.append(f"Our accuracy on them is {our_accuracy:.2f} percent")

            cons_accuracy = self._cons_true_count * 100 / self._true_count
            lines.append(f"Consistency accuracy on them is {cons_accuracy:.2f} percent")
        else:
            lines.append("Accuracy is undefined (no valid selections)")
        return "\n".join(lines)        

############# Main section ############

def run(tasks_to_process):

    with open(PATH_TO_BIRD_JSON, 'r', encoding='utf-8') as file:
        bird_tasks = json.load(file)
    

    try:
        with open(f"{PATH_TO_CACHED_REPRESENTATIVES}/None_tasks.txt", 'r') as f:
            None_tasks = list(map(int, f.readlines()))
    except:
        None_tasks = []
    try:
        with open(f"{PATH_TO_CACHED_REPRESENTATIVES}/False_tasks.txt", 'r') as f:
            False_tasks = list(map(int, f.readlines()))
    except:
        False_tasks = []

    counter = ResultCounter()
    eval_counter = EvalCounter()
    try:
        for task in bird_tasks:
            question_id = task['question_id']
            if question_id not in tasks_to_process:
                continue
            print('Processing task', question_id)
            task_data = from_bird(task)
            
            candidates = []
            
            if USE_CACHED_REPRESENTATIVES:
                with open(f"{PATH_TO_CACHED_REPRESENTATIVES}/{question_id}.txt", 'r', encoding="utf-8") as f:
                    representatives = f.readlines()
            else:
                path_to_candidates = f"{PATH_TO_CANDIDATES}{str(question_id)}.pkl"
                with open(path_to_candidates, "rb") as f:
                    candidate_paths = pickle.load(f)
                for path in candidate_paths:
                    candidates.append(path[-1].final_sql_query)
    
                representatives = extract_representatives(candidates, task_data["path_to_db"])

                with open(f"{PATH_TO_CACHED_REPRESENTATIVES}/{question_id}.txt", 'w', encoding="utf-8") as f:
                    for sql_query in representatives:
                        f.write(sql_query + '\n')
            
            
            print('Candidates:', candidates)

            if question_id in None_tasks:
                status, query_or_message = None, ""
            if question_id in False_tasks:
                status, query_or_message = False, ""
            else:
                status, query_or_message = select(representatives, task_data)

                if status == None:
                    with open(f"{PATH_TO_CACHED_REPRESENTATIVES}/None_tasks.txt", 'a') as f:
                        f.write(str(question_id) + '\n')
                if status == False and ("tournament table" not in query_or_message):
                    with open(f"{PATH_TO_CACHED_REPRESENTATIVES}/False_tasks.txt", 'a') as f:
                        f.write(str(question_id) + '\n')
            counter.count(status, query_or_message)
            eval_counter.count(status, query_or_message, task["SQL"], task_data["path_to_db"], question_id)


    finally: 
        print(counter)
        print(eval_counter)


if __name__ == '__main__':
    tasks_to_process = list(range(20))
    run(tasks_to_process)



