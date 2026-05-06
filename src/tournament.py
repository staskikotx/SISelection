import concurrent.futures
import asyncio
import aiohttp
from functools import partial
from batch_sender import send_prompt
from create_instances import create_instance
from check_instances import check_instance
from build_prompt import get_prompt, extract_json_from_response
from duel_result import get_duel_result
import json
import traceback
from config import *


# Thread-safe async runner (required because asyncio.run() can't be called from multiple threads)
def run_async_in_thread(coro_func, *args, **kwargs):
    """Run an async coroutine in a new event loop within a thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro_func(*args, **kwargs))
    finally:
        loop.close()

# Modified version of your LLM query function to work in threads
def get_llm_answers_threadsafe(pair_data, i, j, db_schema, question, hint, prompt_template):
    """Thread-safe wrapper for LLM queries."""
    
    print('Status:', pair_data['status'])

    if pair_data['status'] == 'INS-C' or pair_data['status'] == 'INS-E':
        return None
    
    # Here we assume that two candidates are separated by pair_data['instance'] 

    prompts = [get_prompt(pair_data, i, j, db_schema, question, hint, prompt_template)] * NUMBER_OF_ATTEMPTS_FOR_LLM 
    
    async def _run_batch():
        async with aiohttp.ClientSession() as session:
            tasks = [send_prompt(session, prompt) for prompt in prompts]
            results = await asyncio.gather(*tasks)
            return results
    
    raw_results = run_async_in_thread(_run_batch)
    
    # Process results (same as your original make_batch_query logic)
    output_texts = []
    for result in raw_results:
        if result and "choices" in result and len(result["choices"]) > 0:
            output_texts.append(extract_json_from_response(result["choices"][0]["message"]["content"]))
        else:
            output_texts.append("")


    llm_answers = []
    for k in range(NUMBER_OF_ATTEMPTS_FOR_LLM):
        try:
            print('Parsing LLM answer\n', output_texts[k])
            llm_answers.append(json.loads(output_texts[k])['tuples_that_answer_question'])
        except Exception as e:
            print('Cannot parse llm answer (is it empty?)')
            print(str(e))

    return llm_answers

# Worker function for concurrent processing
def process_pair(args):
    i, j, representatives, initial_indices, db_schema, db_name, question, hint, prompt_template, postgres_representatives, prov = args
    
    try:
        first_sqlite_rep = representatives[initial_indices[i]]
        second_sqlite_rep = representatives[initial_indices[j]]
        
        pair_info = create_instance(i, j, first_sqlite_rep, second_sqlite_rep, db_schema, db_name, prov)
        pair_info['status'] = check_instance(pair_info, db_schema)
        
        # Thread-safe LLM query
        llm_answers = get_llm_answers_threadsafe(pair_info, i, j, db_schema, question, hint, prompt_template)
        print('LLM answers:', llm_answers)

        if llm_answers is not None and len(llm_answers) > 0 :
            result = get_duel_result(pair_info, llm_answers, db_schema)
            return (i, j, result)
        else :
            return (i, j, None)
    
    except Exception as e:
        print(f"Error processing pair ({i},{j}): {e}")
        print(f"\n=== Exception in pair ({i},{j}) ===")
        traceback.print_exc()  # Prints full traceback to stderr
        print(f"=== End traceback for pair ({i},{j}) ===\n")
        return (i, j, None)  # Return None or fallback value on error

# Main execution with ThreadPoolExecutor
def run_tournament_concurrent(postgres_representatives, representatives, initial_indices, db_schema, db_name, question, hint, prompt_template, prov, max_workers=10):
    n = len(postgres_representatives)
    tournament_table = [[None for _ in range(n)] for _ in range(n)]
    
    # Prepare all tasks
    tasks = [
        (i, j, representatives, initial_indices, db_schema, db_name, question, hint, prompt_template, postgres_representatives, prov)
        for i in range(n)
        for j in range(i+1, n)
    ]
    
    # Process concurrently with thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(process_pair, task) for task in tasks]
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            i, j, result = future.result()
            tournament_table[i][j] = result
    
    return tournament_table
