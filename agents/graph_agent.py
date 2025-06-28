# File: agents/graph_agent.py
# --- CORRECTED: Added missing imports for json and re ---

import json
import re
from llm.model import LanguageModel
from typing import List, Dict, Any

class GraphAgent:
    def __init__(self, llm_model: LanguageModel):
        self.llm = llm_model
        print("Specialist Agent 'GraphAgent' initialized.")

    def _create_charting_prompt(self, user_question: str, data: List[Dict[str, Any]]) -> str:
        """ Creates a prompt to ask the LLM to choose a chart type and map the data. """
        
        data_sample = data[:3]
        
        prompt = f"""
        You are a data visualization expert. Your job is to select the best chart type to answer a user's question and to identify the correct columns for the chart's labels and values.
        You can choose from these chart types: 'pie', 'bar', 'line'.

        Here is a sample of the data retrieved from the database:
        ---
        {json.dumps(data_sample, indent=2, default=str)}
        ---
        
        Here are the rules for choosing a chart type:
        - Use 'pie' for breakdowns of a whole (e.g., "breakdown by type", "distribution of statuses"). This usually involves a 'count' and a category name.
        - Use 'bar' for comparing quantities across different categories (e.g., "crimes per district", "arrests per officer").
        - Use 'line' for showing a trend over time (e.g., "monthly counts", "trend over the last year"). This requires a date column.
        - If no chart is suitable, respond with 'none'.

        Now, analyze the user's question and the data sample.
        User Question: "{user_question}"

        Based on the question and data, provide a JSON object with three keys:
        1. "chart_type": The best chart type ('pie', 'bar', 'line', or 'none').
        2. "label_column": The name of the column that should be used for the chart labels (e.g., 'district_name', 'crime_name', 'incident_date').
        3. "value_column": The name of the column that should be used for the chart values (this is often a 'count' or another numerical value).

        Your response MUST be ONLY the JSON object.
        """
        return prompt

    async def generate_chart_definition(self, user_question: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes data and a question, and returns a JSON definition for a chart.
        """
        if not data or len(data) < 2:
            print("GraphAgent: Not enough data to generate a chart.")
            return {"chart_type": "none"}

        charting_prompt = self._create_charting_prompt(user_question, data)
        
        try:
            response_str = await self.llm.generate_response(charting_prompt)
            cleaned_response = re.sub(r'```(json)?', '', response_str, flags=re.IGNORECASE).strip()
            chart_definition = json.loads(cleaned_response)

            if all(k in chart_definition for k in ["chart_type", "label_column", "value_column"]):
                print(f"GraphAgent: Successfully generated chart definition: {chart_definition}")
                return chart_definition
            else:
                print("GraphAgent: LLM returned invalid JSON structure.")
                return {"chart_type": "none"}
        except Exception as e:
            print(f"GraphAgent: Failed to generate or parse chart definition. Error: {e}")
            return {"chart_type": "none"}