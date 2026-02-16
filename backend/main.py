from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, Header, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import json
import sys
from dotenv import load_dotenv

load_dotenv()

# Add root directoy to sys.path to access services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.agent_controller import run_resume_pipeline, generate_resume_from_linkedin
from services.resume_parser import extract_text
from services.db.lancedb_client import store_resume, get_or_create_table, search_resumes_semantic, log_activity, get_dashboard_stats
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
    threshold: Optional[int] = 75

class GenerateRequest(BaseModel):
    profile: str

# Dependency to get current user
async def get_current_user(authorization: Optional[str] = Header(None)):
    # In a real app, verify JWT here. 
    # For now, we'll strip 'Bearer ' if present to get the "token"
    token = authorization.replace("Bearer ", "") if authorization else "guest"
    
    if "recruiter" in token or "linkedin" in token:
        return "user_recruiter_456"
    
    # Default to Alex Chen for "mock-token-123" or google login
    return "user_alex_chen_123"

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    # Mock authentication
    if request.username == "recruit" and request.password == "admin123":
        return {"success": True, "token": "mock-token-123", "user": {"name": "Senior Recruiter", "id": "user_recruiter_456"}}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "placeholder_id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "placeholder_secret")
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "placeholder_id")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "placeholder_secret")

@app.get("/api/auth/google")
async def auth_google():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri=http://localhost:8000/api/auth/google/callback&scope=openid%20email%20profile"
    )

@app.get("/api/auth/google/callback")
async def auth_google_callback(code: str):
    # In a real app, exchange code for token here
    # For now, redirect to frontend with a mock token
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:5173/auth/callback?token=mock-google-token&name=Alex%20Chen")

@app.get("/api/auth/linkedin")
async def auth_linkedin():
    print("--- [Auth] Redirecting to LinkedIn OAuth ---")
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={LINKEDIN_CLIENT_ID}&redirect_uri=http://localhost:8000/api/auth/linkedin/callback&scope=openid%20profile%20email"
    )

from fastapi import BackgroundTasks

@app.get("/api/auth/linkedin/callback")
async def auth_linkedin_callback(code: str, background_tasks: BackgroundTasks):
    import requests
    
    user_id = "user_recruiter_456"
    profile_data = None
    real_profile_url = None
    display_name = "LinkedIn User"
    email = "user@example.com"
    auth_debug_msg = ""
    
    # 1. Attempt Real Token Exchange if secrets are present
    if LINKEDIN_CLIENT_ID != "placeholder_id" and LINKEDIN_CLIENT_SECRET != "placeholder_secret":
        try:
            print("--- Attempting Real LinkedIn Token Exchange ---")
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "http://localhost:8000/api/auth/linkedin/callback",
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET
            }
            token_res = requests.post(token_url, data=payload)
            token_data = token_res.json()
            
            if "access_token" in token_data:
                access_token = token_data["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # A. Try OIDC UserInfo (Standard)
                try:
                    userinfo_res = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
                    if userinfo_res.status_code == 200:
                        user_data = userinfo_res.json()
                        first_name = user_data.get("given_name", "")
                        last_name = user_data.get("family_name", "")
                        email = user_data.get("email", "")
                        display_name = user_data.get("name", f"{first_name} {last_name}")
                        picture = user_data.get("picture", "")
                        # Construct a profile URL (OIDC doesn't give vanity URL)
                        # Remove special characters and handle spaces/hyphens better
                        def sanitize_slug(name):
                            import re
                            # Lowercase, replace non-alphanumeric with hyphen, then collapse sequential hyphens
                            # This handles "Mathew -Cousin" -> "mathew-cousin" (no double hyphens)
                            s = name.lower()
                            s = re.sub(r'[^a-z0-9]', '-', s)
                            s = re.sub(r'-+', '-', s)
                            return s.strip('-')
                            
                        real_profile_url = f"https://www.linkedin.com/in/{sanitize_slug(display_name)}" if first_name else None
                        
                        profile_data = f"Name: {display_name}\nEmail: {email}\nProfile URL: {real_profile_url or 'N/A'}\nAvatar: {picture}\nSource: LinkedIn OIDC"
                        print(f"--- Real LinkedIn Auth Success (OIDC) for {display_name} ---")
                    else:
                        auth_debug_msg += f"OIDC Failed ({userinfo_res.status_code}); "
                        raise Exception("OIDC endpoint failed")
                except Exception as oidce:
                    # B. Fallback to Legacy API (v2/me)
                    print(f"--- OIDC Failed, trying Legacy v2/me: {oidce} ---")
                    try:
                        me_res = requests.get("https://api.linkedin.com/v2/me", headers=headers)
                        if me_res.status_code == 200:
                            me_data = me_res.json()
                            first_name = me_data.get("localizedFirstName", "LinkedIn User")
                            last_name = me_data.get("localizedLastName", "")
                            profile_id = me_data.get("id", "unknown")
                            display_name = f"{first_name} {last_name}"
                            
                            # Try to get email (requires r_emailaddress)
                            email_res = requests.get("https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))", headers=headers)
                            email = "private@linkedin.com"
                            if email_res.status_code == 200:
                                email_data = email_res.json()
                                try:
                                    email = email_data["elements"][0]["handle~"]["emailAddress"]
                                except:
                                    pass
                            
                            real_profile_url = f"https://www.linkedin.com/in/{profile_id}"
                            profile_data = f"Name: {display_name}\nLinkedIn ID: {profile_id}\nEmail: {email}\nSource: LinkedIn Legacy v2"
                            print(f"--- Real LinkedIn Auth Success (Legacy) for {display_name} ---")
                        else:
                             auth_debug_msg += f"Legacy Failed ({me_res.status_code}: {me_res.text}); "
                             print(f"--- Legacy Auth Failed: {me_res.text} ---")
                    except Exception as legacy_e:
                        auth_debug_msg += f"Legacy Error ({str(legacy_e)}); "
                        print(f"--- Legacy Auth Exception: {legacy_e} ---")

                # DISABLE AUTOMATIC BACKGROUND SCRAPE
                # We now rely on the frontend to show the "Verify & Start AI Sync" button
                # so that the user can confirm the guessed URL or fix it.
                # if profile_data and real_profile_url and "linkedin.com/in/" in real_profile_url:
                #     from fastapi import BackgroundTasks
                #     if background_tasks:
                #         # Use the real service which handles scraping and AI parsing
                #         background_tasks.add_task(background_sync_linkedin, user_id, real_profile_url)

            else:
                auth_debug_msg += f"Token Exchange Failed ({str(token_data)}); "
                print(f"--- Real LinkedIn Token Exchange Failed: {token_data} ---")
        except Exception as e:
            auth_debug_msg += f"Auth Exception ({str(e)}); "
            print(f"--- Real LinkedIn Auth Exception: {e} ---")
    else:
        auth_debug_msg += "Missing Client ID/Secret; "

    # 2. Fallback to Mock Data if Real Auth failed
    if not profile_data:
        print("--- Using Mock LinkedIn Profile Data ---")
        real_profile_url = "https://www.linkedin.com/in/alex-chen-demo"
        display_name = "LinkedIn User"
        email = "user@example.com"
        profile_data = """
        Name: LinkedIn User
        Role: Senior Technical Recruiter
        Summary: Experienced recruiter with a passion for AI and automation.
        """
    
    # NUCLEAR WIPE: Delete any old LinkedIn profiles for this user to force a fresh sync
    print(f"--- [Wipe] Clearing stale LinkedIn records for {user_id} ---")
    try:
        table = get_or_create_table()
        table.delete(f"user_id = '{user_id}' AND filename = 'LinkedIn_Profile.pdf'")
    except Exception as e:
        print(f"DEBUG: Wipe failed (might be first time): {e}")

    # Remove early minimal data storage to prevent quality degradation.
    # The full scrape will be handles in the background task if triggered.
    print(f"--- Processed LinkedIn OAuth for {user_id} ---")
    # if profile_data:
    #     store_resume("LinkedIn_Profile.pdf", profile_data, user_id, api_key=None) 
    #     log_activity(user_id, "linkedin_sync_auth_only", "LinkedIn_Profile.pdf", 0, "AUTH")
    
    from fastapi.responses import RedirectResponse
    
    # Redirect with results AND debug info
    final_profile_url = real_profile_url if real_profile_url else ""
    redirect_url = f"http://localhost:5173/auth/callback?token=mock-linkedin-token&name={display_name}&email={email}&linkedin_connected=true&profile_url={final_profile_url}"
    if auth_debug_msg:
        import urllib.parse
        redirect_url += f"&auth_error={urllib.parse.quote(auth_debug_msg)}"
        
    return RedirectResponse(url=redirect_url)

@app.post("/api/resumes/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...), 
    store_db: str = Form("true"),
    x_openrouter_key: Optional[str] = Header(None),
    user_id: str = Depends(get_current_user)
):
    print(f"--- Uploading {len(files)} files for user {user_id} ---")
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
                # Pass the key to store_resume so it can compute embeddings
                store_resume(file.filename, text, user_id, api_key=x_openrouter_key)
            
            results.append({"filename": file.filename, "status": "indexed"})
            # Log activity
            log_activity(user_id, "upload", file.filename, 0, "N/A")

            print(f"Completed: {file.filename}")
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            results.append({"filename": file.filename, "status": "error", "error": str(e)})
    
    return {"success": True, "processed": results}

@app.get("/api/dashboard/stats")
async def dashboard_stats(user_id: str = Depends(get_current_user)):
    return get_dashboard_stats(user_id)

@app.post("/api/search")
async def search_resumes(
    request: SearchRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None),
    user_id: str = Depends(get_current_user)
):
    print(f"--- Search Request: '{request.query}' for user {user_id} ---")
    # Perform semantic search to filter relevant resumes/chunks
    df = search_resumes_semantic(request.query, user_id, limit=10, api_key=x_openrouter_key)
    
    if df.empty:
        print("DEBUG: Search returned 0 results from LanceDB.")
        return {"results": []}

    print(f"DEBUG: Search returned {len(df)} results. Passing to LLM...")
    # Format the filtered results for the Agentic AI
    resumes_text = ""
    for _, row in df.iterrows():
        resumes_text += f"Filename: {row['filename']}\nExcerpt:\n{row['text']}\n--------------------\n"
    
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = PromptTemplate(
        input_variables=["resumes", "query"],
        template="""Identify resumes relevant to the query based on the excerpts provided. 
        Return ONLY valid JSON.
        FORMAT: {{ "results": [ {{ "filename": "...", "score": 0, "justification": "...", "missing_skills": [], "auto_screen": "..." }} ] }}
        
        Excerpts:
        {resumes}
        
        Query: {query}"""
    )
    
    # Initialize LLM with dynamic config if available
    llm = ChatOpenAI(
        model=x_llm_model or "gpt-4o-mini",
        api_key=x_openrouter_key or os.getenv("OPEN_ROUTER_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    chain = prompt | llm | StrOutputParser()
    raw_result = chain.invoke({"resumes": resumes_text, "query": request.query})
    print(f"DEBUG: LLM Raw Output: {raw_result[:200]}...")
    
    try:
        from services.skill_gap_graph import clean_json_output
        clean_res = clean_json_output(raw_result)
        return json.loads(clean_res)
    except Exception as e:
        print(f"DEBUG: Failed to parse LLM output: {e}")
        return {"results": [], "error": f"Failed to parse AI output: {str(e)}"}

@app.post("/api/analyze/quality")
async def analyze_quality(
    request: AnalyzeRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    output = run_resume_pipeline(task="score", resumes=[request.resume_text], llm_config=llm_config)
    
    # Log activity
    try:
        score = output.get("score", {}).get("overall", 0)
        log_activity("quality", "Manual Input", score)
    except:
        pass
        
    return output

@app.post("/api/analyze/gap")
async def analyze_gap(
    request: AnalyzeRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    output = run_resume_pipeline(task="skill_gap", resumes=[request.resume_text], query=request.jd_text, llm_config=llm_config)
    
    # Log activity
    try:
        score = output.get("match_score", 0)
        log_activity("skill_gap", "Manual Input", score)
    except:
        pass

    return output

@app.post("/api/analyze/screen")
async def analyze_screen(
    request: AnalyzeRequest,
    x_openrouter_key: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    llm_config = {"api_key": x_openrouter_key, "model": x_llm_model} if x_openrouter_key else None
    output = run_resume_pipeline(
        task="screen", 
        resumes=[request.resume_text], 
        query=request.jd_text, 
        llm_config=llm_config,
        threshold=request.threshold
    )
    
    # Log activity
    try:
        score = output.get("score", {}).get("overall", 0)
        decision = "SELECTED" if output.get("decision", {}).get("selected") else "REJECTED"
        log_activity("screen", "Manual Input", score, decision)
    except:
        pass

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

# Background task for LinkedIn Scraping
def background_sync_linkedin(user_id: str, profile_url: str):
    print(f"--- [Background] Starting LinkedIn Sync for {user_id} at {profile_url} ---")
    
    # Check for credentials before starting
    li_user = os.getenv("LinkedinLogin")
    li_pass = os.getenv("LinkedinPassword")
    if not li_user or not li_pass:
        print("--- [Background] FAILED: Missing LinkedIn credentials in .env ---")
        log_activity(user_id, "linkedin_sync_failed", "LinkedIn_Profile.pdf", 0, "MISSING_CREDS")
        # Store a JSON error message so the UI can show it
        error_json = json.dumps({
            "error": "LinkedIn scraper credentials missing in .env file.",
            "raw_text": "Please configure LinkedinLogin and LinkedinPassword in your server environment."
        })
        store_resume("LinkedIn_Profile.pdf", error_json, user_id, api_key=None)
        return

    try:
        from services.agent_controller import generate_resume_from_linkedin
        # This will scrape, parse, and structure the resume via LangGraph
        output = generate_resume_from_linkedin(profile_url)
        
        if output and "resume" in output:
            resume_data = output["resume"]
            # Convert JSON data to a string for storage in LanceDB
            structured_text = json.dumps(resume_data, indent=2)
            
            # Store in DB with the reserved filename
            store_resume("LinkedIn_Profile.pdf", structured_text, user_id, api_key=None)
            log_activity(user_id, "linkedin_sync_complete", "LinkedIn_Profile.pdf", 100, "SYNCED")
            print(f"--- [Background] LinkedIn Sync Complete for {user_id} ---")
        else:
            print(f"--- [Background] LinkedIn Sync returned no resume for {user_id} ---")
            log_activity(user_id, "linkedin_sync_failed", "LinkedIn_Profile.pdf", 0, "NO_DATA")
        
    except Exception as e:
        print(f"--- [Background] LinkedIn Sync Failed: {e} ---")
        log_activity(user_id, "linkedin_sync_failed", "LinkedIn_Profile.pdf", 0, "ERROR")

@app.get("/api/user/profile")
async def get_user_synced_profile(user_id: str = Depends(get_current_user)):
    """
    Fetches the most recent 'LinkedIn_Profile.pdf' content for the user.
    """
    # We can search specifically for this filename
    # Or just use the search function with a specific filter
    # Ideally, store_resume should facilitate retrieval. 
    # Let's simple-search the DB for this user and filename
    
    # Check if we have an endpoint or service query for this. 
    # We'll use search_resumes_semantic with a special "filename" filter if possible, 
    # or just iterate dashboard stats? No, dashboard stats is aggregate.
    
    # Let's implement a direct fetch helper in lancedb_client or here.
    # For now, quick hack: use existing search but rely on filename match if we had one.
    # actually, allow's just use the `download_resume` logic if it were a file, but it's in DB.
    
    # Better: Query DB directly.
    from services.db.lancedb_client import get_or_create_table
    table = get_or_create_table()
    
    # Filter by user_id AND filename
    # distinct filename? 
    results = table.search([0]*1536).where(f"user_id = '{user_id}' AND filename = 'LinkedIn_Profile.pdf'").limit(1).to_pandas()
    
    if results.empty:
        return {"found": False}
        
    # We found it. Now we need to parse it back to JSON for the frontend
    # Since we stored flat text, we might need to structure it again or return raw.
    # The frontend expects a JSON object { contact: ..., experience: ... }
    # REALITY CHECK: The scraper returns raw text. The frontend wants structured JSON.
    # We should probably run the LLM parser on the scraped text BEFORE storing or AFTER retrieving.
    # Let's do it AFTER retrieving for now (on-demand), or if previously stored was just text.
    
    # If the stored content is just text, we return a mock-like structure wrapping that text 
    # so the frontend can at least show something, or we trigger a quick parse.
    
    row = results.iloc[0]
    text_content = row['text']
    
    try:
        # Try to parse the stored JSON
        resume_json = json.loads(text_content)
        
        # QUALITY CHECK: If it's just a name/email stub without real experience or summary,
        # we treat it as "not found" to force a real sync.
        has_summary = bool(resume_json.get("summary") and len(resume_json.get("summary", "")) > 50)
        has_exp = bool(resume_json.get("experience") and len(resume_json.get("experience", [])) > 0)
        
        if not (has_summary or has_exp) and not resume_json.get("error"):
            print(f"DEBUG: Found a stub for {user_id}, ignoring it to allow fresh sync.")
            return {"found": False}

        return {
            "found": True,
            "resume": resume_json
        }
    except:
        # Fallback if it's just raw text
        return {
            "found": True,
            "resume": {
                "contact": { "name": "Synced User", "email": "hidden@linkedin.com" },
                "summary": text_content[:500] + "...",
                "experience": [],
                "raw_text": text_content
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
