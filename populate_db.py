# # ----------------------------------------------------------------------
# # File: populate_db.py
# # Description: --- UPDATED with more robust error handling and detailed debugging prints. ---
# # ----------------------------------------------------------------------
# import os
# import time
# import psycopg2
# from dotenv import load_dotenv

# load_dotenv()

# def populate():
#     conn = None
#     retries = 10 # Increased retries to account for DB startup time
#     initial_delay = 3 # Initial delay before first connection attempt
#     retry_delay = 5 # Delay between retries

#     print(f"PopulateDB: Attempting to connect to PostgreSQL (host: {os.getenv('POSTGRES_HOST', 'db')}, port: {os.getenv('POSTGRES_PORT', '5432')})...")
#     time.sleep(initial_delay) # Give DB a moment to  start initially

#     while retries > 0:
#         try:
#             conn = psycopg2.connect(
#                 dbname=os.getenv("POSTGRES_DB"),
#                 user=os.getenv("POSTGRES_USER"),
#                 password=os.getenv("POSTGRES_PASSWORD"),
#                 host=os.getenv("POSTGRES_HOST", "db"), # Default to 'db' for Docker
#                 port=os.getenv("POSTGRES_PORT", "5432") # Default to '5432'
#             )
#             conn.autocommit = True # Ensure DDL statements are committed immediately
#             print("PopulateDB: Database connection successful!")
#             break
#         except psycopg2.OperationalError as e:
#             retries -= 1
#             print(f"PopulateDB: Database not ready or connection failed. Retries left: {retries}. Error: {e}")
#             if retries > 0:
#                 time.sleep(retry_delay)
#             else:
#                 print("PopulateDB: Could not connect to database after several retries. Aborting.")
#                 return
#         except Exception as e:
#             print(f"PopulateDB: An unexpected error occurred during connection: {e}")
#             return
    
#     if not conn:
#         print("PopulateDB: Failed to establish database connection. Exiting.")
#         return

#     try:
#         cur = conn.cursor()
#         print("PopulateDB: Cursor created.")

#         # Drop tables in reverse order of dependency to avoid foreign key conflicts
#         tables_to_drop = ["arrest", "fir", "officer_master", "station_master", "district_master", "crime_type_master", "case_reports"]
#         print("PopulateDB: Dropping existing tables if they exist...")
#         for table in tables_to_drop:
#             try:
#                 cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
#                 print(f"PopulateDB: Dropped table '{table}'.")
#             except psycopg2.Error as e:
#                 print(f"PopulateDB: Error dropping table '{table}': {e}")
#                 # Don't re-raise, try to continue with other drops
#         conn.commit() # Commit drops
#         print("PopulateDB: Old tables drop attempts completed.")

#         print("PopulateDB: Creating new CCTNS schema...")

#         # Master Tables
#         schema_statements = [
#             """
#             CREATE TABLE district_master (
#                 district_id SERIAL PRIMARY KEY,
#                 district_name VARCHAR(100) UNIQUE NOT NULL
#             );
#             """,
#             """
#             CREATE TABLE station_master (
#                 station_id SERIAL PRIMARY KEY,
#                 station_name VARCHAR(100) NOT NULL,
#                 district_id INT REFERENCES district_master(district_id)
#             );
#             """,
#             """
#             CREATE TABLE officer_master (
#                 officer_id SERIAL PRIMARY KEY,
#                 officer_name VARCHAR(100) NOT NULL,
#                 rank VARCHAR(50),
#                 station_id INT REFERENCES station_master(station_id)
#             );
#             """,
#             """
#             CREATE TABLE crime_type_master (
#                 crime_type_id SERIAL PRIMARY KEY,
#                 crime_name VARCHAR(100) NOT NULL
#             );
#             """,
#             # Transaction Tables
#             """
#             CREATE TABLE fir (
#                 fir_id SERIAL PRIMARY KEY,
#                 incident_date DATE NOT NULL,
#                 summary TEXT,
#                 district_id INT REFERENCES district_master(district_id),
#                 station_id INT REFERENCES station_master(station_id),
#                 crime_type_id INT REFERENCES crime_type_master(crime_type_id)
#             );
#             """,
#             """
#             CREATE TABLE arrest (
#                 arrest_id SERIAL PRIMARY KEY,
#                 arrest_date DATE NOT NULL,
#                 fir_id INT REFERENCES fir(fir_id),
#                 officer_id INT REFERENCES officer_master(officer_id)
#             );
#             """
#         ]

#         for i, stmt in enumerate(schema_statements):
#             try:
#                 cur.execute(stmt)
#                 print(f"PopulateDB: Successfully executed schema statement {i+1}.")
#                 conn.commit() # Commit after each table creation
#             except psycopg2.Error as e:
#                 print(f"PopulateDB: ERROR creating schema (Statement {i+1}): {e}")
#                 conn.rollback() # Rollback on error
#                 raise # Re-raise to stop if schema creation fails critically

#         print("PopulateDB: Schema created successfully.")

#         print("PopulateDB: Inserting mock data...")
#         data_statements = [
#             "INSERT INTO district_master (district_name) VALUES ('Guntur'), ('Visakhapatnam'), ('Hyderabad');",
#             "INSERT INTO station_master (station_name, district_id) VALUES ('Guntur Sadar', 1), ('Panjagutta', 3), ('MVP Colony', 2);",
#             "INSERT INTO officer_master (officer_name, rank, station_id) VALUES ('Ravi Kumar', 'Inspector', 2), ('Priya Singh', 'Sub-Inspector', 1), ('Anil Reddy', 'Constable', 3);",
#             "INSERT INTO crime_type_master (crime_name) VALUES ('Theft'), ('Assault'), ('Fraud'), ('Cybercrime');",
#             """
#             INSERT INTO fir (incident_date, summary, district_id, station_id, crime_type_id) VALUES
#             ('2025-05-10', 'Theft of electronic goods from a warehouse.', 1, 1, 1),
#             ('2025-05-12', 'A phishing scam targeting bank customers was reported.', 3, 2, 4),
#             ('2025-06-01', 'Assault reported in a public park during the evening.', 2, 3, 2),
#             ('2025-06-03', 'Another case of theft, this time a vehicle was stolen.', 1, 1, 1),
#             ('2025-06-15', 'Financial fraud case involving credit card cloning.', 3, 2, 3);
#             """,
#             """
#             INSERT INTO arrest (arrest_date, fir_id, officer_id) VALUES
#             ('2025-05-15', 1, 2),
#             ('2025-06-05', 3, 1),
#             ('2025-06-20', 5, 1);
#             """
#         ]

#         for i, stmt in enumerate(data_statements):
#             try:
#                 cur.execute(stmt)
#                 print(f"PopulateDB: Successfully inserted data batch {i+1}.")
#             except psycopg2.Error as e:
#                 print(f"PopulateDB: ERROR inserting data (Batch {i+1}): {e}")
#                 conn.rollback() # Rollback on error
#                 raise # Re-raise to stop if data insertion fails critically
        
#         conn.commit() # Final commit for all inserts
#         print("PopulateDB: Database has been successfully populated with new schema and data!")

#     except Exception as e:
#         print(f"PopulateDB: An unhandled error occurred during database population: {e}")
#         if conn:
#             conn.rollback()
#             print("PopulateDB: Transaction rolled back due to error.")
#     finally:
#         if conn:
#             cur.close()
#             conn.close()
#             print("PopulateDB: Database connection closed.")

# if __name__ == "__main__":
#     populate()