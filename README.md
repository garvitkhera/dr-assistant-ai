# Medical Consultation App

A FastAPI + Streamlit application for medical consultation recording and AI-powered note generation.

## Project Structure

```
medical_app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Environment configuration
│   ├── routers/
│   │   ├── doctors.py       # Doctor CRUD endpoints
│   │   ├── patients.py      # Patient CRUD endpoints
│   │   └── consultations.py # Consultation endpoints
│   └── services/
│       ├── supabase_client.py  # Supabase connection
│       └── openai_service.py   # OpenAI GPT-4o integration
├── frontend/
│   └── app.py               # Streamlit application
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── supabase_schema.sql      # Database schema
```

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Setup Supabase Database
Run the SQL in `supabase_schema.sql` in your Supabase SQL Editor.

### 4. Run Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Run Frontend (new terminal)
```bash
cd frontend
streamlit run app.py --server.port 8501
```

## API Endpoints

- `GET /health` - Health check
- `GET/POST /api/doctors` - List/Create doctors
- `GET/POST /api/patients` - List/Create patients
- `GET /api/doctors/{id}/patients` - Get doctor's patients
- `POST /api/doctors/{id}/patients/{patient_id}` - Link patient to doctor
- `POST /api/consultations/process-audio` - Process audio recording
- `GET /api/consultations/patient/{id}` - Get patient consultation history
- `PUT /api/consultations/{id}` - Update consultation notes
