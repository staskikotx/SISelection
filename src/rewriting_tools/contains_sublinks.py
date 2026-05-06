from pglast import parse_sql
from pglast.ast import SubLink

def contains_sublink_helper(ast_node, visited=None):
    """
    Work with AST objects directly with cycle detection
    """
    if visited is None:
        visited = set()
    
    # Handle None
    if ast_node is None:
        return False
    
    # Handle primitive types
    if isinstance(ast_node, (str, int, float, bool)):
        return False
    
    # Handle containers
    if isinstance(ast_node, (list, tuple)):
        return any(contains_sublink_helper(item, visited) for item in ast_node)
    
    # Check for cycles
    if id(ast_node) in visited:
        return False
    
    visited.add(id(ast_node))
    
    try:
        # Check if current node is a SubLink (this catches ALL subqueries)
        if isinstance(ast_node, SubLink):
            return True
        
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
                    attrs_to_check.append(attr_value)
            except (AttributeError, TypeError):
                continue
        
        # Check all attributes for sublinks
        for attr_value in attrs_to_check:
            if contains_sublink_helper(attr_value, visited):
                return True
        
        return False
        
    finally:
        visited.discard(id(ast_node))

def contains_sublink(sql_query):
    parsed = parse_sql(sql_query)
    return contains_sublink_helper(parsed[0].stmt)
    

# Example usage
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "SELECT * FROM users WHERE id = 5",
        "SELECT * FROM products WHERE category = (SELECT name FROM categories WHERE id = 1)",
        "SELECT * FROM table1 WHERE col1 = (SELECT col2 FROM table2 WHERE x = (SELECT y FROM table3))",
        "SELECT * FROM users WHERE name = 'John' AND id = (SELECT user_id FROM admin)",
    ]
    
    for query in test_queries:
        print("Original:")
        print(query)
        try:
            result = contains_sublink(query)
            print(result)
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 80)