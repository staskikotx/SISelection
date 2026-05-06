from datetime import date, datetime
import json
import re

def convert_postgres_database_to_sqlite(sql):
    """
    Converts PostgreSQL SQL syntax to SQLite-compatible syntax.

    - Replaces "table_name" with `table_name`
    - Removes simple type casts (e.g., ::int)
    - Converts timestamptz literals to UTC strings in SQLite format
    """
    # Step 1: Handle timestamptz literals like '...T...+ZZ:ZZ'::timestamptz
    def convert_timestamp(match):
        date = match.group(1)
        time = match.group(2)
        return f"'{date} {time}.0'"
        

    sql = re.sub(
        r"'([\d-]*)T([\d:]*)\+08:00'::timestamptz", # +08:00 because Postgres runs on a server situated in Hong Kong
        convert_timestamp,
        sql,
        flags=re.IGNORECASE
    )

    # Step 2: Remove other PostgreSQL casts (e.g., ::date, ::int, ::text)
    sql = re.sub(r'::\s*\w+', '', sql)

    # Step 3: Clean up table description tags
    sql = sql.replace("<Table Description>", "")
    sql = sql.replace("</Table Description>", "")

    return sql

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)
