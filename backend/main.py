from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import doctors, patients, consultations

app = FastAPI(
    title="Medical Consultation API",
    description="API for medical consultation recording and AI-powered note generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(consultations.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "code": 200}


@app.get("/")
async def root():
    return {"message": "Medical Consultation API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
