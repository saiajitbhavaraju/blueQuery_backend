# File: database/connection.py
# --- FINAL ENHANCED VERSION: Now includes column comments for better AI context ---
print("--- database/connection.py: File imported ---") # ADD THIS LINE

import oracledb
import os
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

class Database:
    # ... (class variables __init__ and close methods remain the same) ...
    connection = None
    db_owner = None

    def __init__(self):
        if Database.connection is None:
            try:
                # --- THIS IS THE CORRECTED LOGIC ---
                # It looks for ORACLE_SCHEMA_OWNER first, and falls back to ORACLE_USER
                owner_from_env = os.getenv("ORACLE_SCHEMA_OWNER") or os.getenv("ORACLE_USER")
                if not owner_from_env:
                    raise ValueError("CRITICAL: ORACLE_USER or ORACLE_SCHEMA_OWNER environment variable not set.")
                
                self.db_owner = owner_from_env.upper()
                
                dsn = f'{os.getenv("ORACLE_HOST")}:{os.getenv("ORACLE_PORT")}/{os.getenv("ORACLE_SERVICE")}'
                
                print("Attempting to connect to Oracle Database...")
                Database.connection = oracledb.connect(
                    user=os.getenv("ORACLE_USER"),
                    password=os.getenv("ORACLE_PASSWORD"),
                    dsn=dsn
                )
                print("Successfully connected to Oracle Database!")
            except (oracledb.Error, ValueError) as e:
                print(f"FATAL: Error during database initialization: {e}")
                Database.connection = None
                raise e

    def execute_sql_query(self, query: str, params: Optional[dict] = None):
        if self.connection is None: return [], None
        try:
            with self.connection.cursor() as cursor:
                print(f"Executing Query:\n---\n{query}\n---")
                cursor.execute(query, params or {})
                if cursor.description:
                    columns = [col[0].lower() for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()], None
                else:
                    return [], None
        except oracledb.Error as e:
            print(f"Error executing query: {e}")
            return None, str(e)

    def get_schema_string_for_tables(self, table_names: List[str]) -> str:
        if self.connection is None: return "-- Database connection not available."
        
        all_schemas = []
        with self.connection.cursor() as cursor:
            # --- QUERY NOW JOINS WITH ALL_COL_COMMENTS ---
            query = """
            SELECT 
                c.COLUMN_NAME, c.DATA_TYPE, c.DATA_LENGTH, c.DATA_PRECISION, c.DATA_SCALE, c.NULLABLE,
                cm.COMMENTS
            FROM ALL_TAB_COLUMNS c
            LEFT JOIN ALL_COL_COMMENTS cm ON c.OWNER = cm.OWNER AND c.TABLE_NAME = cm.TABLE_NAME AND c.COLUMN_NAME = cm.COLUMN_NAME
            WHERE c.TABLE_NAME = :table_name AND c.OWNER = :owner
            ORDER BY c.COLUMN_ID
            """
            for table_name in table_names:
                try:
                    cursor.execute(query, table_name=table_name.upper(), owner=self.db_owner)
                    rows = cursor.fetchall()
                    if not rows: continue
                    
                    columns_str = []
                    for row in rows:
                        col_name, data_type, length, precision, scale, nullable, comments = row
                        
                        if data_type in ("VARCHAR2", "CHAR"): type_str = f"{data_type}({int(length)})"
                        elif data_type == "NUMBER":
                            if precision is not None and scale is not None and scale != 0: type_str = f"NUMBER({int(precision)}, {int(scale)})"
                            elif precision is not None: type_str = f"NUMBER({int(precision)})"
                            else: type_str = "NUMBER"
                        else: type_str = data_type
                        
                        null_str = " NOT NULL" if nullable == 'N' else ""
                        comment_str = f" -- {comments}" if comments else ""
                        columns_str.append(f"    {col_name} {type_str}{null_str},{comment_str}")
                    
                    # Remove comma from last line
                    if columns_str: columns_str[-1] = columns_str[-1].rstrip(',')

                    schema_str = f"CREATE TABLE {table_name.upper()} (\n" + "\n".join(columns_str) + "\n);"
                    all_schemas.append(schema_str)
                except oracledb.Error as e:
                    print(f"Could not fetch schema for table {table_name}: {e}")

        return "\n\n".join(all_schemas)
    
    # ... (Keep the fetch_all_for_rag and close methods) ...
    def fetch_all_for_rag(self, table_name: str, columns: List[str]):
        if self.connection is None: return [], None
        column_str = ", ".join(columns)
        query = f"SELECT {column_str} FROM {table_name}"
        print(f"Fetching data for RAG pipeline with query: {query}")
        results, error = self.execute_sql_query(query)
        if error:
            print(f"Failed to fetch data for RAG: {error}")
            return []
        return results

    def close(self):
        if self.connection:
            self.connection.close()
            Database.connection = None
            print("Oracle database connection closed.")