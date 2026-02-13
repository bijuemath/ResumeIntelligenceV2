from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, Header
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import json
import sys

# Add root directoy to sys.path to access services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.agent_controller import run_resume_pipeline, generate_resume_from_linkedin
from services.resume_parser import extract_text
from services.db.lancedb_client import store_resume, get_or_create_table
from services.export_service import generate_docx

app = FastAPI(title="Resume Intelligence API")

# Configure CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific React URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/raw_resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class SearchRequest(BaseModel):
    query: str

class AnalyzeRequest(BaseModel):
    resume_text: str
    jd_text: Optional[str] = None

class GenerateRequest(BaseModel):
    profile: str

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    # Mock authentication
    if request.username == "recruit" and request.password == "admin123":
        return {"success": True, "token": "mock-token-123", "user": {"name": "Senior Recruiter"}}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/resumes/upload")
async def upload_resumes(files: List[UploadFile] = File(...), store_db: str = Form("true")):
    print(f"--- Uploading {len(files)} files ---")
    results = []
    store_db_bool = store_db.lower() == "true"
    
    for file in files:
        try:
            print(f"Processing: {file.filename}")
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            text = extract_text(file_path)
            if store_db_bool:
                print(f"Storing in DB: {file.filename}")
                store_resume(file.filename, text)
            
            results.append({"filename": file.filename, "status": "indexed"})
            print(f"Completed: {file.filename}")
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            results.append({"filename": file.filename, "status": "error", "error": str(e)})
    
    return {"success": True, "processed": results}

@app.post("/api/search")
async def search_resumes(
    request: SearchRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    # This logic is adapted from Search_Resumes.py but would ideally be in a service
    table = get_or_create_table()
    df = table.to_pandas()
    
    if df.empty:
        return {"results": []}

    resumes_text = ""
    for _, row in df.iterrows():
        resumes_text += f"Filename: {row['filename']}\nResume:\n{row['text']}\n--------------------\n"
    
    # We can reuse run_resume_pipeline if we add a search task, 
    # but for now, we'll implement it here or reuse the logic.
    # Actually, the existing run_resume_pipeline doesn't have "search" yet.
    # Let's use the existing logic from Search_Resumes.py (which uses a chain).
    
    # For now, let's return a mock or implement the LLM call here.
    # To keep it consistent, I'll use the chain logic.
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = PromptTemplate(
        input_variables=["resumes", "query"],
        template="""Identify resumes relevant to the query. Return ONLY valid JSON.
        FORMAT: {{ "results": [ {{ "filename": "...", "score": 0, "justification": "...", "missing_skills": [], "auto_screen": "..." }} ] }}
        Resumes: {resumes}
        Query: {query}"""
    )
    
    # Initialize LLM with dynamic config if available
    if x_openrouter_key:
        llm = ChatOpenAI(
            model=x_llm_model or "gpt-4o-mini",
            api_key=x_openrouter_key,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPEN_ROUTER_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
    chain = prompt | llm | StrOutputParser()
    raw_result = chain.invoke({"resumes": resumes_text, "query": request.query})
    
    try:
        from services.skill_gap_graph import clean_json_output
        clean_res = clean_json_output(raw_result)
        return json.loads(clean_res)
    except:
        return {"results": [], "error": "Failed to parse AI output"}

@app.post("/api/analyze/quality")
async def analyze_quality(
    request: AnalyzeRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    output = run_resume_pipeline(task="score", resumes=[request.resume_text], llm_config=llm_config)
    return output

@app.post("/api/analyze/gap")
async def analyze_gap(
    request: AnalyzeRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    output = run_resume_pipeline(task="skill_gap", resumes=[request.resume_text], query=request.jd_text, llm_config=llm_config)
    return output

@app.post("/api/analyze/screen")
async def analyze_screen(
    request: AnalyzeRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    output = run_resume_pipeline(task="screen", resumes=[request.resume_text], query=request.jd_text, llm_config=llm_config)
    return output

@app.post("/api/generate/resume")
async def generate_resume_endpoint(
    request: GenerateRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    output = run_resume_pipeline(task="generate", query=request.profile, llm_config=llm_config)
    return output

@app.post("/api/linkedin/scrape")
async def linkedin_scrape(
    request: SearchRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None),
    x_linkedin_user: Optional[str] = Header(None),
    x_linkedin_pass: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    linkedin_creds = {"email": x_linkedin_user, "password": x_linkedin_pass} if x_linkedin_user and x_linkedin_pass else None
    output = generate_resume_from_linkedin(request.query, llm_config=llm_config, linkedin_creds=linkedin_creds)
    return output

@app.get("/api/resumes/download/{filename}")
async def download_resume(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')

@app.post("/api/generate/export")
async def export_resume_docx(request: dict):
    # This endpoint receives the resume JSON and returns a DOCX file
    try:
        from io import BytesIO
        file_stream = generate_docx(request)
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=generated_resume.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
