from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from services.supabase_client import get_supabase

router = APIRouter(prefix="/api/patients", tags=["patients"])


class PatientCreate(BaseModel):
    name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    name: str
    date_of_birth: Optional[str]
    gender: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    blood_type: Optional[str]
    allergies: Optional[str]
    medical_history: Optional[str]
    created_at: str


@router.get("", response_model=List[PatientResponse])
async def list_patients(search: Optional[str] = Query(None)):
    """Get all patients, optionally filtered by search term."""
    supabase = get_supabase()
    query = supabase.table("patients").select("*")
    
    if search:
        query = query.ilike("name", f"%{search}%")
    
    response = query.order("name").execute()
    return response.data


@router.post("", response_model=PatientResponse)
async def create_patient(patient: PatientCreate):
    """Create a new patient."""
    supabase = get_supabase()
    response = supabase.table("patients").insert(patient.model_dump(exclude_none=True)).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create patient")
    return response.data[0]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """Get a patient by ID."""
    supabase = get_supabase()
    response = supabase.table("patients").select("*").eq("id", patient_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return response.data


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: str, patient: PatientUpdate):
    """Update a patient."""
    supabase = get_supabase()
    update_data = patient.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    response = supabase.table("patients").update(update_data).eq("id", patient_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return response.data[0]


@router.delete("/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient."""
    supabase = get_supabase()
    supabase.table("patients").delete().eq("id", patient_id).execute()
    return {"message": "Patient deleted successfully"}
