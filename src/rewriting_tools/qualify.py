import sqlglot
from sqlglot.optimizer.qualify import qualify
import re
from typing import Dict, Any, Optional


class SQLQualifier:
    """
    A class to qualify SQL column names using a schema loaded from a SQL file.
    
    Usage:
        qualifier = SQLQualifier("student_club.sql")
        qualified_sql = qualifier.qualify_columns(
            "SELECT event_name, first_name FROM event JOIN attendance ON event_id = link_to_event JOIN member ON link_to_member = member_id"
        )
    """
    
    def __init__(self, schema_file_path: str, dialect: str = 'postgres'):
        """
        Initialize the SQLQualifier with a schema file.
        
        Args:
            schema_file_path: Path to the SQL file containing CREATE TABLE statements
            dialect: SQL dialect to use for parsing 
        """
        self.schema_file_path = schema_file_path
        self.dialect = dialect
        self.schema = self._load_schema_from_sql_file(schema_file_path)
    
    def _load_schema_from_sql_file(self, sql_file_path: str) -> Dict[str, Dict[str, str]]:
        """Load schema from SQL file by parsing CREATE TABLE statements."""
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        schema = {}
        
        # Find all CREATE TABLE statements
        create_table_pattern = r'CREATE TABLE\s+`?(\w+)`?\s*\((.*?)\)\s*;'
        matches = re.findall(create_table_pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        for table_name, columns_section in matches:
            # print('Table:', table_name)
            schema[table_name] = {}
            
            # Remove comments first
            columns_without_comments = re.sub(r'--.*$', '', columns_section, flags=re.MULTILINE)
            
            # Split by commas, but be careful with commas inside parentheses (like in data types)
            # For simplicity, we'll split by lines and handle multi-line definitions
            lines = columns_without_comments.split('\n')
            current_def = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip constraints
                if (line.upper().startswith('PRIMARY KEY') or 
                    line.upper().startswith('FOREIGN KEY') or
                    line.upper().startswith('CONSTRAINT')):
                    continue
                
                # Handle column definitions that might span multiple lines
                if line.endswith(','):
                    current_def += line[:-1].strip() + " "
                else:
                    current_def += line + " "
                    
                # If we have a complete column definition (contains data type)
                if current_def.strip() and not current_def.strip().endswith(','):
                    # Extract column name - handle backticks
                    # Match: `column name with spaces` or just column_name
                    col_name_match = re.match(r'^`([^`]+)`\s+(\w+)', current_def.strip())
                    if col_name_match:
                        # print("ColNameMatch: name is ", col_name_match.group(1).strip())
                        col_name = col_name_match.group(1).strip()
                        data_type = col_name_match.group(2).upper()
                        # Remove any remaining backticks from column name
                        col_name = col_name.strip('`"')
                        schema[table_name][col_name] = data_type
                    
                    current_def = ""
        
        print('Schema:')
        for table, columns in schema.items():
            print(f"  {table}: {list(columns.keys())}")
        return schema
    
    def qualify_columns(self, sql_query: str, output_dialect: Optional[str] = None) -> str:
        """
        Qualify column names in the given SQL query using the loaded schema.
        
        Args:
            sql_query: The SQL query to qualify
            output_dialect: SQL dialect for output (default: same as input dialect)
        
        Returns:
            Qualified SQL query as a string
        """
        if output_dialect is None:
            output_dialect = self.dialect
            
        expression = sqlglot.parse_one(sql_query, read=self.dialect)
        qualified_expression = qualify(expression, schema=self.schema, dialect=self.dialect)
        return qualified_expression.sql(dialect=output_dialect)
    
    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the loaded schema.
        
        Returns:
            Dictionary mapping table names to column definitions
        """
        return self.schema.copy()


# Usage example (kept for testing purposes)
if __name__ == "__main__":
    # Load schema from your file
    qualifier = SQLQualifier("student_club.sql")
    
    print('Schema:')
    for table, columns in qualifier.get_schema().items():
        print(f"  {table}: {list(columns.keys())}")
    
    # Qualify a SQL query
    sql_query = "SELECT event_name, first_name FROM event JOIN attendance ON event_id = link_to_event JOIN member ON link_to_member = member_id"
    qualified_sql = qualifier.qualify_columns(sql_query, output_dialect='postgres')
    
    print("\nQualified SQL:")
    print(qualified_sql)

    qualifier = SQLQualifier("/mnt/compression/alpha-sql/tempA/formula_1.sql")
    sql_query = "SELECT results.raceid, TO_CHAR(CAST(races.date AS TIMESTAMP), 'YYYY') AS race_year FROM results INNER JOIN drivers ON results.driverid = drivers.driverid INNER JOIN races ON results.raceid = races.raceid WHERE drivers.forename = 'Michael' AND drivers.surname = 'Schumacher' ORDER BY results.milliseconds ASC NULLS FIRST LIMIT 1"
    qualified_sql = qualifier.qualify_columns(sql_query, output_dialect='postgres')
    
    print("\nQualified SQL:")
    print(qualified_sql)