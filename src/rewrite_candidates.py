import re
from src.rewriting_tools.contains_sublinks import contains_sublink
from src.rewriting_tools.final_rewriter import rewrite
from src.rewriting_tools.remove_backticks import remove_backticks_without_spaces
import sqlglot

def has_select_star(sql: str) -> bool:
    # Pattern explanation:
    # - (?i)        : case-insensitive flag
    # - \b          : word boundary to avoid matching "SELECTOR" etc.
    # - SELECT      : literal "SELECT"
    # - \s+         : one or more whitespace characters
    # - \*          : literal asterisk (escaped)
    # - (?!\w)      : negative lookahead to ensure * is not part of a longer identifier (e.g., "*abc")
    pattern = r'(?i)\bSELECT\s+\*(?!\w)'
    return bool(re.search(pattern, sql))

#####################################################################################
    
def rewrite_representatives(candidates, db_path) :
    rewritten_candidates = []
    initial_indices = []
    

    for idx, candidate in enumerate(candidates):
        #print('Original candidate:', candidate)
        if has_select_star(candidate):
            #print('Ignoring candidate because it contains \'select *\'')
            continue
        candidate = remove_backticks_without_spaces(candidate)
        #print('Modified candidate:', candidate)
        candidate = sqlglot.transpile(candidate, read = "sqlite", write = "postgres")[0]
        #print('Transpiled candidate:', candidate)
        
        try:
            rewritten_candidate = rewrite(candidate, db_path)
            #print('Rewritten candidate:', rewritten_candidate)
            initial_indices.append(idx) 
            rewritten_candidates.append(rewritten_candidate)
        except Exception as e:
            print('Did not succeed to rewrite:', candidate)
            print(str(e))
            
    return rewritten_candidates, initial_indices
                    




