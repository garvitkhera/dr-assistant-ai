import streamlit as st
import requests
from datetime import datetime
from audio_recorder_streamlit import audio_recorder
import time
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Medical Consultation App",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #1e3a5f; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.2rem; color: #64748b; margin-bottom: 2rem; }
    .card { background: #f8fafc; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; }
    .success-msg { background: #ecfdf5; color: #065f46; padding: 1rem; border-radius: 8px; border: 1px solid #a7f3d0; }
    .timer-display { font-size: 2.5rem; font-weight: 700; text-align: center; color: #1e3a5f; font-family: monospace; }
    .stButton>button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# Session state initialization
def init_session_state():
    defaults = {
        "selected_doctor": None,
        "selected_patient": None,
        "audio_bytes": None,
        "recording_active": False,
        "consultation_result": None,
        "current_view": "dashboard",
        "show_history": False,
        "edit_mode": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# API Helper functions
def api_get(endpoint):
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint, data=None, json_data=None, files=None):
    try:
        response = requests.post(f"{BACKEND_URL}{endpoint}", data=data, json=json_data, files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def api_put(endpoint, json_data):
    try:
        response = requests.put(f"{BACKEND_URL}{endpoint}", json=json_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


# Component: Add Doctor Modal
def add_doctor_form():
    st.subheader("Add New Doctor")
    with st.form("add_doctor_form"):
        name = st.text_input("Name*", placeholder="Dr. John Smith")
        specialty = st.text_input("Specialty", placeholder="Cardiology")
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email", placeholder="doctor@hospital.com")
        with col2:
            phone = st.text_input("Phone", placeholder="+1 234 567 8900")
        
        submitted = st.form_submit_button("Add Doctor", use_container_width=True)
        if submitted and name:
            result = api_post("/api/doctors", json_data={
                "name": name,
                "specialty": specialty,
                "email": email,
                "phone": phone
            })
            if result:
                st.success(f"✓ Doctor '{name}' added successfully!")
                st.rerun()


# Component: Add Patient Modal
def add_patient_form(doctor_id=None):
    st.subheader("Add New Patient")
    with st.form("add_patient_form"):
        name = st.text_input("Full Name*", placeholder="Jane Doe")
        col1, col2 = st.columns(2)
        with col1:
            dob = st.date_input("Date of Birth", value=None, min_value=datetime(1900, 1, 1), max_value=datetime.now())
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
            blood_type = st.selectbox("Blood Type", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        with col2:
            phone = st.text_input("Phone", placeholder="+1 234 567 8900")
            email = st.text_input("Email", placeholder="patient@email.com")
            emergency_contact = st.text_input("Emergency Contact", placeholder="Name - Phone")
        
        allergies = st.text_area("Known Allergies", placeholder="Penicillin, Peanuts...")
        medical_history = st.text_area("Medical History", placeholder="Previous conditions, surgeries...")
        
        submitted = st.form_submit_button("Add Patient", use_container_width=True)
        if submitted and name:
            patient_data = {
                "name": name,
                "date_of_birth": dob.isoformat() if dob else None,
                "gender": gender if gender else None,
                "phone": phone if phone else None,
                "email": email if email else None,
                "blood_type": blood_type if blood_type else None,
                "allergies": allergies if allergies else None,
                "medical_history": medical_history if medical_history else None,
                "emergency_contact": emergency_contact if emergency_contact else None
            }
            patient_data = {k: v for k, v in patient_data.items() if v}
            result = api_post("/api/patients", json_data=patient_data)
            if result:
                if doctor_id:
                    api_post(f"/api/doctors/{doctor_id}/patients/{result['id']}")
                st.success(f"✓ Patient '{name}' added successfully!")
                st.rerun()


# Component: Patient History
def show_patient_history(patient_id, patient_name):
    st.subheader(f"📋 Consultation History - {patient_name}")
    consultations = api_get(f"/api/consultations/patient/{patient_id}")
    
    if not consultations:
        st.info("No consultation history found for this patient.")
        return
    
    for consult in consultations:
        date_str = consult.get("consultation_date", "")[:10]
        with st.expander(f"📅 {date_str} - {consult.get('chief_complaint', 'Consultation')}", expanded=False):
            st.markdown(f"**Diagnosis:** {consult.get('diagnosis', 'N/A')}")
            st.markdown(f"**Treatment Plan:** {consult.get('treatment_plan', 'N/A')}")
            st.markdown("---")
            st.markdown("**Notes:**")
            st.markdown(consult.get("formatted_notes", "No notes available"))
            
            with st.expander("View Raw Transcript"):
                st.text(consult.get("raw_transcript", "No transcript available"))


# Component: Consultation Result with Edit
def show_consultation_result(result, consultation_id):
    st.markdown('<div class="success-msg">✓ Consultation processed and saved!</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    ai_result = result.get("ai_result", {})
    consultation = result.get("consultation", {})
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.markdown(f"**Chief Complaint:** {ai_result.get('chief_complaint', 'N/A')}")
    with col2:
        st.markdown(f"**Diagnosis:** {ai_result.get('diagnosis', 'N/A')}")
        st.markdown(f"**Follow-up:** {ai_result.get('follow_up', 'N/A')}")
    
    st.markdown("---")
    
    if st.session_state.edit_mode:
        st.subheader("Edit Notes")
        with st.form("edit_notes_form"):
            edited_notes = st.text_area(
                "Formatted Notes",
                value=ai_result.get("formatted_notes", ""),
                height=300
            )
            edited_diagnosis = st.text_input("Diagnosis", value=ai_result.get("diagnosis", ""))
            edited_treatment = st.text_area("Treatment Plan", value=ai_result.get("treatment_plan", ""))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    update_result = api_put(f"/api/consultations/{consultation_id}", json_data={
                        "formatted_notes": edited_notes,
                        "diagnosis": edited_diagnosis,
                        "treatment_plan": edited_treatment
                    })
                    if update_result:
                        st.success("Notes updated successfully!")
                        st.session_state.edit_mode = False
                        st.rerun()
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
    else:
        st.subheader("Medical Notes (SOAP Format)")
        st.markdown(ai_result.get("formatted_notes", "No notes generated"))
        
        if st.button("✏️ Edit Notes"):
            st.session_state.edit_mode = True
            st.rerun()
    
    st.markdown("---")
    with st.expander("📝 View Raw Transcript"):
        st.text(ai_result.get("transcript", "No transcript available"))


# Main Dashboard
def dashboard():
    st.markdown('<p class="main-header">🏥 Medical Consultation</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Select a doctor to begin</p>', unsafe_allow_html=True)
    
    # Fetch doctors
    doctors = api_get("/api/doctors") or []
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Doctor", use_container_width=True):
            st.session_state.current_view = "add_doctor"
            st.rerun()
    
    if not doctors:
        st.info("No doctors found. Add a doctor to get started.")
        return
    
    # Doctor selection
    st.subheader("Select Doctor")
    cols = st.columns(min(len(doctors), 4))
    for idx, doctor in enumerate(doctors):
        with cols[idx % 4]:
            specialty = doctor.get("specialty", "General")
            if st.button(
                f"👨‍⚕️ {doctor['name']}\n{specialty}",
                key=f"doc_{doctor['id']}",
                use_container_width=True
            ):
                st.session_state.selected_doctor = doctor
                st.session_state.current_view = "patients"
                st.rerun()


# Patient Selection View
def patient_view():
    doctor = st.session_state.selected_doctor
    st.markdown(f'<p class="main-header">👨‍⚕️ Dr. {doctor["name"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{doctor.get("specialty", "General Practice")}</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.selected_doctor = None
            st.session_state.current_view = "dashboard"
            st.rerun()
    with col3:
        if st.button("➕ Add Patient", use_container_width=True):
            st.session_state.current_view = "add_patient"
            st.rerun()
    
    st.markdown("---")
    
    # Search patients
    search_query = st.text_input("🔍 Search patients", placeholder="Type patient name...")
    
    # Get doctor's patients
    patients = api_get(f"/api/doctors/{doctor['id']}/patients") or []
    
    # Also search all patients if query provided
    if search_query:
        all_patients = api_get(f"/api/patients?search={search_query}") or []
        existing_ids = {p["id"] for p in patients}
        for p in all_patients:
            if p["id"] not in existing_ids:
                p["_not_linked"] = True
                patients.append(p)
    
    if not patients:
        st.info("No patients found. Add a patient or search to link existing patients.")
        return
    
    st.subheader("Patients")
    for patient in patients:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            age = ""
            if patient.get("date_of_birth"):
                try:
                    dob = datetime.fromisoformat(patient["date_of_birth"])
                    age = f" ({(datetime.now() - dob).days // 365} yrs)"
                except:
                    pass
            st.markdown(f"**{patient['name']}**{age}")
            if patient.get("_not_linked"):
                st.caption("Not linked to this doctor")
        with col2:
            if patient.get("_not_linked"):
                if st.button("Link", key=f"link_{patient['id']}", use_container_width=True):
                    api_post(f"/api/doctors/{doctor['id']}/patients/{patient['id']}")
                    st.rerun()
            else:
                if st.button("📋 History", key=f"hist_{patient['id']}", use_container_width=True):
                    st.session_state.selected_patient = patient
                    st.session_state.current_view = "history"
                    st.rerun()
        with col3:
            if st.button("▶️ Start", key=f"start_{patient['id']}", use_container_width=True):
                st.session_state.selected_patient = patient
                st.session_state.current_view = "consultation"
                st.rerun()


# Consultation Recording View
def consultation_view():
    doctor = st.session_state.selected_doctor
    patient = st.session_state.selected_patient
    
    st.markdown(f'<p class="main-header">🎙️ Recording Consultation</p>', unsafe_allow_html=True)
    st.markdown(f"**Doctor:** Dr. {doctor['name']} | **Patient:** {patient['name']}")
    
    if st.button("← Back to Patients"):
        st.session_state.selected_patient = None
        st.session_state.audio_bytes = None
        st.session_state.consultation_result = None
        st.session_state.current_view = "patients"
        st.rerun()
    
    st.markdown("---")
    
    # Show result if exists
    if st.session_state.consultation_result:
        consultation_id = st.session_state.consultation_result.get("consultation", {}).get("id")
        show_consultation_result(st.session_state.consultation_result, consultation_id)
        
        if st.button("🔄 New Recording", use_container_width=True):
            st.session_state.audio_bytes = None
            st.session_state.consultation_result = None
            st.session_state.edit_mode = False
            st.rerun()
        return
    
    # Audio recorder
    st.markdown("### 🎤 Record Consultation (Max 30 seconds)")
    st.info("Click the microphone to start recording. Recording will auto-stop at 30 seconds.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#1e3a5f",
            icon_size="3x",
            pause_threshold=30.0,
            sample_rate=16000
        )
    
    if audio_bytes:
        st.session_state.audio_bytes = audio_bytes
        st.audio(audio_bytes, format="audio/wav")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Re-record", use_container_width=True):
                st.session_state.audio_bytes = None
                st.rerun()
        with col2:
            if st.button("✨ Process with AI", type="primary", use_container_width=True):
                with st.spinner("Processing audio with AI..."):
                    files = {"audio": ("recording.wav", audio_bytes, "audio/wav")}
                    data = {
                        "doctor_id": doctor["id"],
                        "patient_id": patient["id"],
                        "doctor_name": doctor["name"],
                        "patient_name": patient["name"]
                    }
                    result = api_post("/api/consultations/process-audio", data=data, files=files)
                    if result:
                        st.session_state.consultation_result = result
                        st.rerun()


# History View
def history_view():
    patient = st.session_state.selected_patient
    
    if st.button("← Back to Patients"):
        st.session_state.selected_patient = None
        st.session_state.current_view = "patients"
        st.rerun()
    
    show_patient_history(patient["id"], patient["name"])


# Add Doctor View
def add_doctor_view():
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = "dashboard"
        st.rerun()
    
    add_doctor_form()


# Add Patient View  
def add_patient_view():
    doctor = st.session_state.selected_doctor
    
    if st.button("← Back to Patients"):
        st.session_state.current_view = "patients"
        st.rerun()
    
    add_patient_form(doctor["id"] if doctor else None)


# Main Router
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### 🏥 Medical App")
        st.markdown("---")
        
        if st.session_state.selected_doctor:
            st.markdown(f"**Doctor:** {st.session_state.selected_doctor['name']}")
        if st.session_state.selected_patient:
            st.markdown(f"**Patient:** {st.session_state.selected_patient['name']}")
        
        st.markdown("---")
        st.caption(f"Backend: {BACKEND_URL}")
        
        # Health check
        try:
            health = api_get("/health")
            if health and health.get("status") == "healthy":
                st.success("✓ API Connected")
            else:
                st.error("✗ API Error")
        except:
            st.error("✗ API Offline")
    
    # Route to appropriate view
    view = st.session_state.current_view
    
    if view == "dashboard":
        dashboard()
    elif view == "patients":
        patient_view()
    elif view == "consultation":
        consultation_view()
    elif view == "history":
        history_view()
    elif view == "add_doctor":
        add_doctor_view()
    elif view == "add_patient":
        add_patient_view()


if __name__ == "__main__":
    main()
