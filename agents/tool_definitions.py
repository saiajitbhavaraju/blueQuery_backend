# File: agents/tool_definitions.py
# --- FINAL DEFINITIVE VERSION ---

import re
import json
from datetime import date
from typing import List, Dict, Any

from database.connection import Database
from llm.model import LanguageModel
from rag.pipeline import RagPipeline

def _clean_sql_query(raw_sql: str) -> str:
    cleaned_sql = re.sub(r'```(sql)?', '', raw_sql, flags=re.IGNORECASE).strip()
    if cleaned_sql.lower().startswith('sql:'): cleaned_sql = cleaned_sql[4:].strip()
    n = len(cleaned_sql)
    if n > 0 and n % 2 == 0:
        midpoint = n // 2
        first_half = cleaned_sql[:midpoint].strip()
        second_half = cleaned_sql[midpoint:].strip()
        if first_half == second_half:
            print("CLEANER: Detected and removed duplicated SQL query.")
            cleaned_sql = first_half
    if cleaned_sql.endswith(';'): cleaned_sql = cleaned_sql[:-1]
    return cleaned_sql

# In agents/tool_definitions.py

async def sql_search_tool(user_question: str, db_schema: str, db: Database, llm: LanguageModel) -> Dict[str, Any]:
    print("TOOL: Using 'sql_search_tool' (Context-Aware Flow)")
    current_date_str = date.today().strftime("%Y-%m-%d")

    # --- FINAL PROMPT WITH BUSINESS CONTEXT AND PERFECTED FEW-SHOT EXAMPLE ---
    prompt = f"""
    You are an expert-level Oracle SQL developer and police data analyst. Your task is to write a single, valid, read-only Oracle SQL query to answer the user's question based on the provided schema and business context.

    **CRITICAL INSTRUCTIONS:**
    1.  First, understand the user's question and the business context.
    2.  Then, use the database schema to find the exact table and column names.
    3.  You MUST use the table and column names EXACTLY as defined in the schema. Do NOT hallucinate.
    4.  If the question cannot be answered, you MUST return a single word: UNSUPPORTED.

    **DATABASE SCHEMA:**
    ---
    {db_schema}
    ---

    **BUSINESS CONTEXT & RULES:**
    - A "registered case" corresponds to one row in the T_FIR_REGISTRATION table. To count registered cases, use COUNT(fir.FIR_REG_NUM).
    - A "convicted case" is determined by the ACCUSED_STATUS_CD in the T_ACCUSED_INFO table. A value of '1' often indicates a conviction. To count these, use COUNT(CASE WHEN accused.ACCUSED_STATUS_CD = 1 THEN 1 END).
    - To get district names, you must JOIN T_FIR_REGISTRATION on DISTRICT_CD with M_DISTRICT on DISTRICT_CD.

    -- START OF A HIGH-QUALITY EXAMPLE --
    [USER QUESTION]:
    list me all convicted cases out of registered cases for the year - 2023 by district

    [SQL QUERY]:
    SELECT d.DISTRICT, COUNT(f.FIR_REG_NUM) as "total_registered_cases", COUNT(CASE WHEN a.ACCUSED_STATUS_CD = 1 THEN 1 END) as "convicted_cases" FROM T_FIR_REGISTRATION f JOIN T_ACCUSED_INFO a ON f.FIR_REG_NUM = a.FIR_REG_NUM JOIN M_DISTRICT d ON f.DISTRICT_CD = d.DISTRICT_CD WHERE f.REG_YEAR = 2023 GROUP BY d.DISTRICT
    -- END OF EXAMPLE --

    **NEW USER'S QUESTION (as of {current_date_str}):** "{user_question}"

    Your output is ONLY the single, valid Oracle SQL query, or the word UNSUPPORTED.
    SQL QUERY:
    """
    
    raw_sql = await llm.generate_response(prompt)
    if "UNSUPPORTED" in raw_sql:
        return {"error": "The question could not be answered with the available database schema.", "sql_query": "UNSUPPORTED"}
    
    generated_sql = _clean_sql_query(raw_sql)
    
    if not generated_sql.upper().startswith('SELECT'):
        return {"error": "Generated query was not a valid SELECT statement."}

    try:
        results, error = db.execute_sql_query(generated_sql)
        if error:
             return {"error": f"SQL execution failed: {error}", "sql_query": generated_sql}
        return {"sql_query": generated_sql, "results": results}
    except Exception as e:
        return {"error": f"A critical error occurred during SQL execution: {e}", "sql_query": generated_sql}

async def vector_search_tool(user_question: str, db: Database, llm: LanguageModel) -> Dict[str, Any]:
    print("TOOL: Using 'vector_search_tool'")
    rag_pipeline = RagPipeline(db=db)
    context, sources = rag_pipeline.get_context(
        user_question, 
        table_name="T_FIR_REGISTRATION",
        content_column="FIR_CONTENTS",
        id_column="FIR_REG_NUM"
    )
    return {"context": context, "sources": sources}

async def graphing_tool(user_question: str, data: List[Dict[str, Any]], llm: LanguageModel) -> Dict[str, Any]:
    print("TOOL: Using 'graphing_tool'")
    if not data or len(data) < 2: return {"chart_definition": {"chart_type": "none"}}
    data_sample = data[:3]
    prompt = f"""
    You are a data visualization expert. Based on the data and user question, provide a JSON object with "chart_type", "label_column", and "value_column".
    User Question: "{user_question}"
    Data Sample: {json.dumps(data_sample, indent=2, default=str)}
    Your response MUST be ONLY the JSON object.
    """
    try:
        response_str = await llm.generate_response(prompt)
        cleaned_response = re.sub(r'```(json)?', '', response_str, flags=re.IGNORECASE).strip()
        chart_definition = json.loads(cleaned_response)
        if all(k in chart_definition for k in ["chart_type", "label_column", "value_column"]):
            return {"chart_definition": chart_definition}
        else:
            return {"chart_definition": {"chart_type": "none"}}
    except Exception as e:
        print(f"TOOL 'graphing_tool' failed: {e}")
        return {"chart_definition": {"chart_type": "none"}}