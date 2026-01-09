import base64
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

MEDICAL_SYSTEM_PROMPT = """You are a medical documentation assistant. Your task is to process audio recordings of doctor-patient consultations and generate professional medical notes.

When processing the audio, you must:
1. Transcribe the conversation accurately
2. Generate structured medical notes in SOAP format (Subjective, Objective, Assessment, Plan)

Respond in the following JSON format:
{
    "transcript": "Full transcription of the audio",
    "formatted_notes": "Structured SOAP notes in markdown format",
    "chief_complaint": "Primary reason for visit (brief)",
    "diagnosis": "Working diagnosis or differential diagnoses",
    "treatment_plan": "Recommended treatment and next steps",
    "follow_up": "Recommended follow-up timeframe if mentioned"
}

SOAP Notes Format:
## Subjective
- Chief Complaint
- History of Present Illness
- Review of Systems (if mentioned)

## Objective
- Vital Signs (if mentioned)
- Physical Exam Findings (if mentioned)

## Assessment
- Diagnosis/Differential Diagnoses
- Clinical Reasoning

## Plan
- Medications
- Tests/Procedures
- Patient Education
- Follow-up

Be concise but thorough. If information is not mentioned in the audio, note it as "Not discussed" rather than making assumptions."""


async def process_audio_with_gpt4o(audio_bytes: bytes, patient_name: str, doctor_name: str) -> dict:
    """Process audio using GPT-4o's native audio capabilities."""
    
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    context_prompt = f"""Process this medical consultation audio.
Patient: {patient_name}
Doctor: {doctor_name}

Generate comprehensive medical documentation."""

    response = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text"],
        messages=[
            {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": context_prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_base64,
                            "format": "wav"
                        }
                    }
                ]
            }
        ]
    )
    
    import json
    import re
    content = response.choices[0].message.content
    # Extract JSON from markdown code blocks if present
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        content = json_match.group(1)
    result = json.loads(content)
    return result


async def process_audio_with_whisper_and_gpt4(audio_bytes: bytes, patient_name: str, doctor_name: str) -> dict:
    """Fallback: Use Whisper for transcription + GPT-4 for notes."""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    
    try:
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcript = transcription.text
    finally:
        os.unlink(temp_path)
    
    context_prompt = f"""Process this medical consultation transcript.
Patient: {patient_name}
Doctor: {doctor_name}

Transcript:
{transcript}

Generate comprehensive medical documentation."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    import json
    result = json.loads(response.choices[0].message.content)
    result["transcript"] = transcript
    return result
