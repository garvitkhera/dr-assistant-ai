from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.supabase_client import get_supabase

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


class DoctorCreate(BaseModel):
    name: str
    specialty: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class DoctorResponse(BaseModel):
    id: str
    name: str
    specialty: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    created_at: str


@router.get("", response_model=List[DoctorResponse])
async def list_doctors():
    """Get all doctors."""
    supabase = get_supabase()
    response = supabase.table("doctors").select("*").order("name").execute()
    return response.data


@router.post("", response_model=DoctorResponse)
async def create_doctor(doctor: DoctorCreate):
    """Create a new doctor."""
    supabase = get_supabase()
    response = supabase.table("doctors").insert(doctor.model_dump()).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create doctor")
    return response.data[0]


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: str):
    """Get a doctor by ID."""
    supabase = get_supabase()
    response = supabase.table("doctors").select("*").eq("id", doctor_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return response.data


@router.get("/{doctor_id}/patients")
async def get_doctor_patients(doctor_id: str):
    """Get all patients linked to a doctor."""
    supabase = get_supabase()
    response = supabase.table("doctor_patients")\
        .select("patient_id, patients(*)")\
        .eq("doctor_id", doctor_id)\
        .execute()
    
    patients = [item["patients"] for item in response.data if item.get("patients")]
    return patients


@router.post("/{doctor_id}/patients/{patient_id}")
async def link_patient_to_doctor(doctor_id: str, patient_id: str):
    """Link a patient to a doctor."""
    supabase = get_supabase()
    
    existing = supabase.table("doctor_patients")\
        .select("id")\
        .eq("doctor_id", doctor_id)\
        .eq("patient_id", patient_id)\
        .execute()
    
    if existing.data:
        return {"message": "Patient already linked to doctor"}
    
    response = supabase.table("doctor_patients").insert({
        "doctor_id": doctor_id,
        "patient_id": patient_id
    }).execute()
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to link patient")
    return {"message": "Patient linked successfully"}


@router.delete("/{doctor_id}/patients/{patient_id}")
async def unlink_patient_from_doctor(doctor_id: str, patient_id: str):
    """Unlink a patient from a doctor."""
    supabase = get_supabase()
    supabase.table("doctor_patients")\
        .delete()\
        .eq("doctor_id", doctor_id)\
        .eq("patient_id", patient_id)\
        .execute()
    return {"message": "Patient unlinked successfully"}
