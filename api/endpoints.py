# File: api/endpoints.py
# --- CORRECTED: Properly uses Pydantic models for validation and conversion ---
print("--- api/endpoints.py: File imported ---") # ADD THIS LINE

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
import shutil
import os
import traceback
import json
from typing import Any, List, Dict, Optional

from agents.core_agent import CoreInvestigationAgent
from core.auth import verify_firebase_token
from services.transcription_service import TranscriptionService

router = APIRouter()
agent = CoreInvestigationAgent()
transcriber = TranscriptionService()

print("--- api/endpoints.py: Creating CoreInvestigationAgent instance... ---") # ADD THIS LINE
print("--- api/endpoints.py: CoreInvestigationAgent instance created. ---") # ADD THIS LINE

# --- Pydantic Models for API Validation ---

class MessageHistoryItem(BaseModel):
    """Defines the structure for a single message in the conversation history for validation."""
    role: str
    content: str
    data_payload: Optional[List[Dict[str, Any]]] = None

class TextQueryRequest(BaseModel):
    """Defines the request body for the /text endpoint."""
    query_text: str
    conversation_history: Optional[List[MessageHistoryItem]] = []

class BaseQueryResponse(BaseModel):
    """The base shape for all query responses."""
    response_text: str
    data_sources: List[str]
    data_payload: Optional[List[Dict[str, Any]]] = None
    chart_payload: Optional[Dict[str, Any]] = None

class TextQueryResponse(BaseQueryResponse):
    pass

class VoiceQueryResponse(BaseQueryResponse):
    transcribed_text: str


# --- API Endpoints ---

@router.post("/text", response_model=TextQueryResponse, tags=["Investigation"])
async def handle_text_query(request: TextQueryRequest, token: dict = Depends(verify_firebase_token)):
    """Handles standard text-based queries with conversation history."""
    try:
        # Convert the list of Pydantic models into a list of simple dictionaries for the agent
        history_dicts = [item.model_dump() for item in request.conversation_history] if request.conversation_history else []
        
        result = await agent.process_query(request.query_text, history_dicts)
        return TextQueryResponse(**result)
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@router.post("/voice", response_model=VoiceQueryResponse, tags=["Investigation"])
async def handle_voice_query(
    audio_file: UploadFile = File(...), 
    conversation_history: str = Form('[]'),
    token: dict = Depends(verify_firebase_token)
):
    """Handles voice queries by transcribing first, then processing."""
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    input_audio_path = os.path.join(temp_dir, f"input_{os.urandom(8).hex()}.m4a")
    
    try:
        with open(input_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        transcribed_text = transcriber.transcribe(input_audio_path)
        if not transcribed_text or not transcribed_text.strip():
            raise HTTPException(status_code=400, detail="Could not understand audio.")
        
        # Parse the JSON string and validate it using our Pydantic model
        history_list = json.loads(conversation_history)
        validated_history = [MessageHistoryItem(**item) for item in history_list]
        # Convert the validated models into simple dictionaries for the agent
        history_dicts = [item.model_dump() for item in validated_history]
        
        result = await agent.process_query(transcribed_text, history_dicts)
        
        return VoiceQueryResponse(
            transcribed_text=transcribed_text,
            **result
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    finally:
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)