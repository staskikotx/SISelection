from pglast import parse_sql
from pglast.ast import SelectStmt, FuncCall, String, A_Const, Integer, SortBy, ColumnRef
from pglast.enums.nodes import LimitOption
from pglast.stream import RawStream
from pglast.enums import SortByDir
from copy import deepcopy
from pprint import pprint

def transform_minmax_subqueries_to_orderby(ast_node, visited=None):
    """
    Transform SELECT min(col) or SELECT max(col) in subqueries to SELECT col ORDER BY col [ASC|DESC] LIMIT 1
    """
    if visited is None:
        visited = set()
    
    # Handle None
    if ast_node is None:
        return ast_node
    
    # Handle primitive types
    if isinstance(ast_node, (str, int, float, bool)):
        return ast_node
    
    # Handle containers
    if isinstance(ast_node, (list, tuple)):
        return type(ast_node)(transform_minmax_subqueries_to_orderby(item, visited) for item in ast_node)
    
    # Check for cycles
    if id(ast_node) in visited:
        return ast_node
    
    visited.add(id(ast_node))
    
    try:
        # Check if it's a SelectStmt that we want to transform
        if isinstance(ast_node, SelectStmt):
            # Check if this is a simple SELECT with a single target that's a min/max function
            if (ast_node.targetList and 
                len(ast_node.targetList) == 1 and
                hasattr(ast_node.targetList[0], 'val') and
                isinstance(ast_node.targetList[0].val, FuncCall)):
                
                func_call = ast_node.targetList[0].val
                
                # Check if function name is min or max
                if (len(func_call.funcname) == 1 and 
                    isinstance(func_call.funcname[0], String) and
                    func_call.funcname[0].sval in ('min', 'max')):
                    
                    # Get the argument to min/max (should be a single column reference)
                    if (func_call.args and 
                        len(func_call.args) == 1):
                        
                        arg = func_call.args[0]
                        
                        # Handle ColumnRef arguments
                        if isinstance(arg, ColumnRef):
                            # Determine sort direction: min -> ASC, max -> DESC
                            func_name = func_call.funcname[0].sval
                            sort_dir = SortByDir.SORTBY_ASC if func_name == 'min' else SortByDir.SORTBY_DESC
                            
                            # Create new SelectStmt without the function wrapper
                            new_select = deepcopy(ast_node)
                            
                            # Replace targetList with just the column reference
                            new_select.targetList[0].val = deepcopy(arg)
                            
                            # Set LIMIT 1
                            new_select.limitCount = Integer(ival=1)
                            new_select.limitOption = LimitOption.LIMIT_OPTION_COUNT
                            

                            # Create SortBy node - useOp should be None for simple column sorts
                            sort_by = SortBy(
                                node=deepcopy(arg),
                                sortby_dir=sort_dir,
                                sortby_nulls=0,  # default nulls ordering
                                useOp=None,      # This was the problem - should be None, not 0
                                location=-1
                            )
                            
                            # Handle existing ORDER BY
                            if new_select.sortClause is None:
                                new_select.sortClause = [sort_by]
                            else:
                                # Prepend our sort to existing sorts
                                new_select.sortClause = [sort_by] + new_select.sortClause
                            
                            return new_select
        
        # General recursive traversal for non-matching nodes
        new_node = deepcopy(ast_node)
        
        # Get all attributes that might contain AST nodes
        attrs_to_check = []
        for attr_name in dir(ast_node):
            if attr_name.startswith('_'):
                continue
            if attr_name in ['__class__', '__dict__', '__module__', 'skip_none', 'node_tag']:
                continue
            
            try:
                attr_value = getattr(ast_node, attr_name)
                if attr_value is not None and not isinstance(attr_value, (str, int, float, bool)):
                    attrs_to_check.append((attr_name, attr_value))
            except (AttributeError, TypeError):
                continue
        
        # Process each attribute
        for attr_name, attr_value in attrs_to_check:
            try:
                new_attr_value = transform_minmax_subqueries_to_orderby(attr_value, visited)
                setattr(new_node, attr_name, new_attr_value)
            except (AttributeError, TypeError):
                continue
        
        return new_node
        
    finally:
        visited.discard(id(ast_node))

def convert_minmax_subqueries_to_orderby(sql_query):
    parsed = parse_sql(sql_query)
    #pprint(parsed[0].stmt(skip_none=True))
    transformed = transform_minmax_subqueries_to_orderby(parsed)
    #pprint(transformed[0].stmt(skip_none=True))
    return RawStream()(transformed)

# Example usage
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "SELECT expense.expense_id FROM expense INNER JOIN budget ON expense.link_to_budget = budget.budget_id WHERE budget.remaining IN (SELECT min(remaining) FROM budget)",
        "SELECT * FROM products WHERE price = (SELECT max(price) FROM products)",
        "SELECT name FROM employees WHERE salary IN (SELECT max(salary) FROM employees WHERE department = 'Sales')",
        "SELECT * FROM orders WHERE total = (SELECT min(total) FROM orders WHERE customer_id = 123)",
        "SELECT id FROM table1 WHERE x IN (SELECT max(y) FROM table2 WHERE z > 10 GROUP BY w HAVING count(*) > 1)"
    ]
    
    for query in test_queries:
        print("Original:")
        print(query)
        try:
            result = convert_minmax_subqueries_to_orderby(query)
            print("Transformed:")
            print(result)
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 80)