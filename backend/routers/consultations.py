from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import re
from services.supabase_client import get_supabase
from services.openai_service import process_audio_with_gpt4o, process_audio_with_whisper_and_gpt4

router = APIRouter(prefix="/api/consultations", tags=["consultations"])


class ConsultationUpdate(BaseModel):
    formatted_notes: Optional[str] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    follow_up_date: Optional[str] = None


class ConsultationResponse(BaseModel):
    id: str
    doctor_id: Optional[str]
    patient_id: Optional[str]
    raw_transcript: Optional[str]
    formatted_notes: Optional[str]
    chief_complaint: Optional[str]
    diagnosis: Optional[str]
    treatment_plan: Optional[str]
    follow_up_date: Optional[str]
    consultation_date: str
    created_at: str


@router.post("/process-audio")
async def process_consultation_audio(
    audio: UploadFile = File(...),
    doctor_id: str = Form(...),
    patient_id: str = Form(...),
    doctor_name: str = Form(...),
    patient_name: str = Form(...)
):
    """Process audio recording and generate medical notes."""
    
    audio_bytes = await audio.read()
    
    try:
        result = await process_audio_with_gpt4o(audio_bytes, patient_name, doctor_name)
    except Exception as e:
        print(f"GPT-4o audio failed, falling back to Whisper: {e}")
        result = await process_audio_with_whisper_and_gpt4(audio_bytes, patient_name, doctor_name)
    
    supabase = get_supabase()
    consultation_data = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "raw_transcript": result.get("transcript", ""),
        "formatted_notes": result.get("formatted_notes", ""),
        "chief_complaint": result.get("chief_complaint", ""),
        "diagnosis": result.get("diagnosis", ""),
        "treatment_plan": result.get("treatment_plan", ""),
        "consultation_date": datetime.now().isoformat()
    }
    
    # Only set follow_up_date if it looks like a valid date
    follow_up = result.get("follow_up", "")
    if follow_up and follow_up.lower() not in ["not discussed", "n/a", "none", ""]:
        # Check if it matches a date pattern (YYYY-MM-DD or similar)
        if re.match(r'\d{4}-\d{2}-\d{2}', follow_up):
            consultation_data["follow_up_date"] = follow_up
    
    response = supabase.table("consultations").insert(consultation_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to save consultation")
    
    return {
        "consultation": response.data[0],
        "ai_result": result
    }


@router.get("/patient/{patient_id}", response_model=List[ConsultationResponse])
async def get_patient_consultations(patient_id: str):
    """Get all consultations for a patient."""
    supabase = get_supabase()
    response = supabase.table("consultations")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .order("consultation_date", desc=True)\
        .execute()
    return response.data


@router.get("/doctor/{doctor_id}", response_model=List[ConsultationResponse])
async def get_doctor_consultations(doctor_id: str):
    """Get all consultations by a doctor."""
    supabase = get_supabase()
    response = supabase.table("consultations")\
        .select("*")\
        .eq("doctor_id", doctor_id)\
        .order("consultation_date", desc=True)\
        .execute()
    return response.data


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(consultation_id: str):
    """Get a consultation by ID."""
    supabase = get_supabase()
    response = supabase.table("consultations")\
        .select("*")\
        .eq("id", consultation_id)\
        .single()\
        .execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return response.data


@router.put("/{consultation_id}", response_model=ConsultationResponse)
async def update_consultation(consultation_id: str, update: ConsultationUpdate):
    """Update consultation notes (for doctor edits)."""
    supabase = get_supabase()
    update_data = update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    response = supabase.table("consultations")\
        .update(update_data)\
        .eq("id", consultation_id)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return response.data[0]


@router.delete("/{consultation_id}")
async def delete_consultation(consultation_id: str):
    """Delete a consultation."""
    supabase = get_supabase()
    supabase.table("consultations").delete().eq("id", consultation_id).execute()
    return {"message": "Consultation deleted successfully"}
