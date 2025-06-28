# File: schema_checker.py
# A standalone script to definitively test schema visibility in your Oracle database.

import os
import oracledb
from dotenv import load_dotenv
import sys

# --- MAIN SCRIPT ---
if __name__ == "__main__":
    print("--- Starting Oracle Database Schema Check ---")
    load_dotenv()

    # --- Configuration ---
    USER = os.getenv("ORACLE_USER")
    OWNER = os.getenv("ORACLE_SCHEMA_OWNER") or USER
    DSN = f'{os.getenv("ORACLE_HOST")}:{os.getenv("ORACLE_PORT")}/{os.getenv("ORACLE_SERVICE")}'
    PWD = os.getenv("ORACLE_PASSWORD")
    TABLE_TO_CHECK = 'M_DISTRICT' # Focusing on the table that causes errors

    if not all([USER, OWNER, DSN, PWD]):
        print("FATAL: One or more environment variables are missing.")
        sys.exit(1)

    connection = None
    try:
        print(f"\n[STEP 1] Connecting as user '{USER}' to query schema owned by '{OWNER.upper()}'...")
        connection = oracledb.connect(user=USER, password=PWD, dsn=DSN)
        print("--> SUCCESS: Connection established.")

        cursor = connection.cursor()

        # --- This is the exact logic from your main application's schema loader ---
        print(f"\n[STEP 2] Generating CREATE TABLE statement for '{TABLE_TO_CHECK}'...")
        query = """
        SELECT c.COLUMN_NAME, c.DATA_TYPE, c.DATA_LENGTH, c.DATA_PRECISION, c.DATA_SCALE, c.NULLABLE, cm.COMMENTS
        FROM ALL_TAB_COLUMNS c
        LEFT JOIN ALL_COL_COMMENTS cm ON c.OWNER = cm.OWNER AND c.TABLE_NAME = cm.TABLE_NAME AND c.COLUMN_NAME = cm.COLUMN_NAME
        WHERE c.TABLE_NAME = :table_name AND c.OWNER = :owner
        ORDER BY c.COLUMN_ID
        """
        cursor.execute(query, table_name=TABLE_TO_CHECK.upper(), owner=OWNER.upper())
        rows = cursor.fetchall()

        if not rows:
            print("\n--> RESULT: FAILED. Found ZERO columns for this table. This indicates a permissions or owner name issue.")
        else:
            print(f"\n--> RESULT: SUCCESS. Found {len(rows)} columns. The ground truth schema is:")
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
            
            if columns_str: columns_str[-1] = columns_str[-1].rstrip(',')
            schema_str = f"CREATE TABLE {TABLE_TO_CHECK.upper()} (\n" + "\n".join(columns_str) + "\n);"
            print("\n" + schema_str)

    except Exception as e:
        print(f"\nAN UNEXPECTED ERROR OCCURRED: {e}")
    finally:
        if connection:
            connection.close()
        print("\n--- Schema Check Finished ---")