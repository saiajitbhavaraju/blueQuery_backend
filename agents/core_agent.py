# File: agents/core_agent.py
# --- ROBUST ARCHITECTURE: Caching schema on startup ---
print("--- agents/core_agent.py: File imported ---") # ADD THIS LINE

from database.connection import Database
from llm.model import LanguageModel
from agents.tool_definitions import sql_search_tool, vector_search_tool, graphing_tool
from typing import List, Dict, Any, Optional
import json

class CoreInvestigationAgent:
    # In agents/core_agent.py

    def __init__(self):
        """
        Initializes the agent, database connection, LLM, and crucially,
        loads the GUARANTEED CORRECT database schema from local files.
        """
        print("--- CoreInvestigationAgent: __init__ started. ---")
        
        self.db = Database()
        self.llm = LanguageModel()

        print("Agent is initializing: loading database schema from local cache files...")
        
        try:
            # --- THIS IS THE NEW, ROBUST SCHEMA LOADING LOGIC ---
            with open('t_fir_registration_schema.txt', 'r') as f:
                fir_schema = f.read()
            with open('m_district_schema.txt', 'r') as f:
                district_schema = f.read()
            
            # We can add more files here as needed for other tables
            self.db_schema = f"{fir_schema}\n\n{district_schema}"
            
            print("Database schema successfully loaded from files.")
            # You can print self.db_schema here to see the combined string
            
        except FileNotFoundError as e:
            self.db_schema = ""
            print(f"CRITICAL ERROR: Schema file not found: {e}. Please generate it using schema_checker.py.")
        
        if not self.db_schema:
            print("CRITICAL WARNING: Database schema could not be loaded. SQL generation will likely fail.")
        
        print("Planner-Synthesizer 'CoreInvestigationAgent' initialized.")

    def _create_routing_prompt(self, user_question: str) -> str:
        # ... (This function remains unchanged) ...
        prompt = f"""
        You are a routing agent. Your job is to determine if a user's question requires accessing a police database or if it's a general conversational question (like a greeting or a question about your purpose).

        - If the question is about crimes, cases, arrests, officers, districts, or asks for any specific data, respond with 'DATA_QUERY'.
        - If the question is a simple greeting, a thank you, or a general question like "what can you do?", respond with 'GENERAL_CONVERSATION'.

        User Question: "{user_question}"
        
        Response (DATA_QUERY or GENERAL_CONVERSATION):
        """
        return prompt
    
    def _create_synthesis_prompt(self, user_question: str, evidence: Dict[str, Any]) -> str:
        # ... (This function remains unchanged) ...
        evidence_str = json.dumps(evidence, indent=2, default=str)
        prompt = f"""
        You are an AI assistant for a police officer. Your task is to provide a comprehensive, single, cohesive answer to the user's question based on the evidence you have gathered.
        
        The user's original question was: "{user_question}"

        You have gathered the following evidence by using your tools:
        ---
        {evidence_str}
        ---

        Synthesize this evidence into a final, user-friendly answer.
        - If you have a `sql_data` payload, present the key findings from it.
        - If you have a `chart_definition` payload, introduce the chart in your answer (e.g., "Here is a breakdown of...").
        - If you have a `vector_search_context`, use it to provide a summary.
        - If a tool returned an error, state that you were unable to retrieve that specific piece of information and mention the error.
        - Do not mention the tools or the evidence gathering process in your final answer. Just give the answer.

        Final Answer:
        """
        return prompt

    async def process_query(self, user_question: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> dict:
        print(f"PLANNER: Received question: '{user_question}'")
        evidence = {} 

        routing_prompt = self._create_routing_prompt(user_question)
        route = await self.llm.generate_response(routing_prompt)

        if "GENERAL_CONVERSATION" in route:
            print("PLANNER: Routing to general conversation.")
            general_prompt = f"The user said: '{user_question}'. Provide a brief, friendly response."
            response_text = await self.llm.generate_response(general_prompt)
            return {"response_text": response_text, "data_sources": ["General Conversation"], "data_payload": None, "chart_payload": None}

        print("PLANNER: Routing to data query. Starting evidence gathering.")
        
        # --- MODIFIED: The SQL tool call now passes the cached schema ---
        sql_evidence = await sql_search_tool(user_question, self.db_schema, self.db, self.llm)
        
        if sql_evidence and not sql_evidence.get("error"):
            evidence["sql_data"] = sql_evidence.get("results")
            evidence["data_sources"] = [sql_evidence.get("sql_query")]

            data_for_chart = evidence.get("sql_data")
            if data_for_chart:
                graph_evidence = await graphing_tool(user_question, data_for_chart, self.llm)
                if graph_evidence and graph_evidence.get("chart_definition", {}).get("chart_type") != "none":
                    evidence["chart_definition"] = graph_evidence.get("chart_definition")
        else:
            print("PLANNER: SQL tool failed or returned error.")
            # Add the error message from the failed SQL tool to the evidence
            evidence["sql_tool_error"] = sql_evidence.get("error", "Unknown SQL tool error")
            
            # --- RE-ENABLE THE FALLBACK TOOL ---
            vector_evidence = await vector_search_tool(user_question, self.db, self.llm)
            evidence["vector_search_context"] = vector_evidence.get("context")
            evidence["data_sources"] = vector_evidence.get("sources", [])


        print(f"PLANNER: Synthesizing final answer from evidence: {list(evidence.keys())}")
        synthesis_prompt = self._create_synthesis_prompt(user_question, evidence)
        final_answer = await self.llm.generate_response(synthesis_prompt)

        return {
            "response_text": final_answer,
            "data_sources": evidence.get("data_sources", []),
            "data_payload": evidence.get("sql_data"),
            "chart_payload": {
                "definition": evidence.get("chart_definition"),
                "data": evidence.get("sql_data")
            } if evidence.get("chart_definition") else None
        }