# File: db_health_check.py
# A standalone script to diagnose the Oracle DB connection and schema visibility.

import os
import oracledb
from dotenv import load_dotenv

# --- Helper function to print nicely ---
def print_test_header(n, text):
    print("\n" + "="*50)
    print(f"  Test {n}: {text}")
    print("="*50)

def print_result(result):
    if result:
        for i, row in enumerate(result):
            print(f"  Row {i+1}: {row}")
    else:
        print("  --> No results returned.")
    print("-" * 50)


# --- MAIN SCRIPT ---
if __name__ == "__main__":
    print("Starting Oracle Database Health Check...")
    load_dotenv()

    connection = None
    try:
        # --- Test 1: Basic Connection ---
        print_test_header(1, "Attempting Basic Database Connection")
        user = os.getenv("ORACLE_USER")
        owner = os.getenv("ORACLE_SCHEMA_OWNER") or user
        dsn = f'{os.getenv("ORACLE_HOST")}:{os.getenv("ORACLE_PORT")}/{os.getenv("ORACLE_SERVICE")}'
        
        if not user:
            raise ValueError("ORACLE_USER not found in .env file.")
        
        connection = oracledb.connect(user=user, password=os.getenv("ORACLE_PASSWORD"), dsn=dsn)
        print("  --> SUCCESS: Connection to Oracle established.")
        print("-" * 50)

        cursor = connection.cursor()

        # --- Test 2: Check Current User ---
        print_test_header(2, "Checking Current Logged-In User")
        cursor.execute("SELECT USER FROM DUAL")
        print_result(cursor.fetchall())
        
        # --- Test 3: List All Visible Schemas/Owners ---
        # This is CRUCIAL. It tells us what schemas your user can see.
        print_test_header(3, "Listing All Schemas/Owners Visible to This User")
        cursor.execute("SELECT DISTINCT OWNER FROM ALL_TABLES ORDER BY OWNER")
        print_result(cursor.fetchall())

        # --- Test 4: Count Rows in a Specific Table ---
        # This tests if you have SELECT permission on an actual table.
        print_test_header(4, f"Attempting to Count Rows in {owner.upper()}.T_FIR_REGISTRATION")
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {owner.upper()}.T_FIR_REGISTRATION")
            print_result(cursor.fetchall())
        except oracledb.Error as e:
            print(f"  --> FAILED: Could not query table. Error: {e}")
        print("-" * 50)
            
        # --- Test 5: Test the Exact Schema Query from our App ---
        # This tests if you have permission to view the data dictionary.
        print_test_header(5, f"Testing Data Dictionary Access for Owner '{owner.upper()}'")
        query = "SELECT COUNT(*) FROM ALL_TAB_COLUMNS WHERE OWNER = :owner"
        try:
            cursor.execute(query, owner=owner.upper())
            count = cursor.fetchone()[0]
            print(f"  --> SUCCESS: Found {count} total columns across all visible tables for this owner.")
            print("  --> This means the dynamic schema loader SHOULD work.")
        except oracledb.Error as e:
            print(f"  --> FAILED: Could not query ALL_TAB_COLUMNS. This is the root cause.")
            print(f"  --> Error: {e}")
            print(f"  --> ACTION: You must ask your DBA to grant 'SELECT ON ALL_TAB_COLUMNS' or 'SELECT ANY DICTIONARY' to the user '{user}'.")
        print("-" * 50)

    except Exception as e:
        print(f"\nAN UNEXPECTED ERROR OCCURRED: {e}")
    finally:
        if connection:
            connection.close()
            print("\nConnection closed. Health check finished.")