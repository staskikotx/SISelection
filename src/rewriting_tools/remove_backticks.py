import re

def remove_backticks_without_spaces(sql_query):
    """
    Removes backticks from SQL identifiers that do not contain spaces.
    
    Args:
        sql_query (str): The SQL query string to process
        
    Returns:
        str: The SQL query with backticks removed from identifiers without spaces
    """
    def replace_backticks(match):
        content = match.group(1)
        # If the content contains spaces, keep the backticks
        if ' ' in content or '-' in content:
            return f'`{content}`'
        # Otherwise, remove the backticks
        else:
            return content
    
    # Pattern to match backtick-quoted identifiers
    # This matches `...` but handles escaped backticks properly
    pattern = r'`([^`\\]*(?:\\.[^`\\]*)*)`'
    
    return re.sub(pattern, replace_backticks, sql_query)

# Test cases
if __name__ == "__main__":
    # Test case 1: identifiers without spaces
    query1 = "SELECT `name` FROM `cards` ORDER BY `faceConvertedManaCost` DESC LIMIT 1"
    result1 = remove_backticks_without_spaces(query1)
    expected1 = "SELECT name FROM cards ORDER BY faceConvertedManaCost DESC LIMIT 1"
    print(f"Test 1: {'PASS' if result1 == expected1 else 'FAIL'}")
    print(f"Input:  {query1}")
    print(f"Output: {result1}")
    print()
    
    # Test case 2: identifiers with spaces should remain unchanged
    query2 = "SELECT `FRPM Count (Ages 5-17)` FROM satscores INNER JOIN frpm ON satscores.sname = frpm.`School Name` ORDER BY satscores.avgscrread DESC LIMIT 1"
    result2 = remove_backticks_without_spaces(query2)
    expected2 = query2  # Should remain unchanged
    print(f"Test 2: {'PASS' if result2 == expected2 else 'FAIL'}")
    print(f"Input:  {query2}")
    print(f"Output: {result2}")
    print()
    
    # Test case 3: mixed case
    query3 = "SELECT `name`, `FRPM Count (Ages 5-17)`, `id` FROM `table` WHERE `School Name` = 'Test'"
    result3 = remove_backticks_without_spaces(query3)
    expected3 = "SELECT name, `FRPM Count (Ages 5-17)`, id FROM table WHERE `School Name` = 'Test'"
    print(f"Test 3: {'PASS' if result3 == expected3 else 'FAIL'}")
    print(f"Input:  {query3}")
    print(f"Output: {result3}")