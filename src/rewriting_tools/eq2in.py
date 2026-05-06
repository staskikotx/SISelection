from pglast import parse_sql
from pglast.ast import A_Expr, SubLink, String
from pglast.enums import SubLinkType
from pglast.stream import RawStream
from copy import deepcopy

def transform_eq_sublinks_to_in(ast_node, visited=None):
    """
    Work with AST objects directly with cycle detection
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
        return type(ast_node)(transform_eq_sublinks_to_in(item, visited) for item in ast_node)
    
    # Check for cycles - if we've seen this exact object before, return it as-is
    if id(ast_node) in visited:
        return ast_node
    
    # Add current node to visited set
    visited.add(id(ast_node))
    
    try:
        # Check if it's an A_Expr with '=' operator and SubLink RHS
        if isinstance(ast_node, A_Expr):
            if (len(ast_node.name) == 1 and 
                isinstance(ast_node.name[0], String) and 
                ast_node.name[0].sval == '='):
                
                if (hasattr(ast_node, 'rexpr') and 
                    isinstance(ast_node.rexpr, SubLink)):
        
                    # Transform the original parts recursively
                    transformed_lexpr = transform_eq_sublinks_to_in(ast_node.lexpr, visited)
                    transformed_subselect = transform_eq_sublinks_to_in(ast_node.rexpr.subselect, visited)

                    new_sublink = SubLink(
                        subLinkType=SubLinkType.ANY_SUBLINK,
                        subLinkId=getattr(ast_node.rexpr, 'subLinkId', 0),
                        testexpr=transformed_lexpr,
                        subselect=transformed_subselect,
                        location=getattr(ast_node.rexpr, 'location', -1)
                    )
                    # Don't add the new node to visited since it's a new object
                    return new_sublink
        
        # Create a copy of the node
        new_node = deepcopy(ast_node)
        
        # Get all attributes that might contain AST nodes
        # We'll try common attribute names that typically contain nested nodes
        attrs_to_check = []
        
        # Try to get attributes dynamically
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
                new_attr_value = transform_eq_sublinks_to_in(attr_value, visited)
                setattr(new_node, attr_name, new_attr_value)
            except (AttributeError, TypeError):
                continue
        
        return new_node
        
    finally:
        # Remove from visited set when done (important for correct traversal)
        visited.discard(id(ast_node))

def convert_eq_sublinks_to_in(sql_query):
    parsed = parse_sql(sql_query)
    transformed = transform_eq_sublinks_to_in(parsed)
    return RawStream()(transformed)

# Example usage
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE amount > 100)",
        "SELECT * FROM products WHERE category = (SELECT name FROM categories WHERE id = 1)",
        "SELECT * FROM table1 WHERE col1 = (SELECT col2 FROM table2 WHERE x = (SELECT y FROM table3))",
        "SELECT * FROM users WHERE name = 'John' AND id = (SELECT user_id FROM admin)",
    ]
    
    for query in test_queries:
        print("Original:")
        print(query)
        try:
            result = convert_eq_sublinks_to_in(query)
            print(result)
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 80)