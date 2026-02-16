import lancedb
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import os
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# ---------- DB PATH ----------
DB_PATH = Path("data/lancedb")
DB_PATH.mkdir(parents=True, exist_ok=True)

db = lancedb.connect(DB_PATH)

# ---------- EMBEDDINGS ----------
def get_embeddings_model(api_key=None, model="text-embedding-3-small"):
    key = api_key or os.getenv("OPEN_ROUTER_KEY")
    if not key:
        raise ValueError("OPEN_ROUTER_KEY is required for semantic search. Please set it in your .env file or environment.")
    
    # OpenRouter often requires 'openai/' prefix for OpenAI models
    model_name = model if "/" in model else f"openai/{model}"
    
    return OpenAIEmbeddings(
        model=model_name,
        openai_api_key=key,
        openai_api_base="https://openrouter.ai/api/v1"
    )

# ---------- SCHEMA ----------
resume_schema = pa.schema([
    pa.field("id", pa.string()),
    pa.field("user_id", pa.string()), # Added for multi-tenancy
    pa.field("filename", pa.string()),
    pa.field("text", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), 1536)) # Assuming text-embedding-3-small
])

# ---------- TABLE HANDLER ----------
def get_or_create_table():
    if "resumes" in db.table_names():
        return db.open_table("resumes")

    return db.create_table(
        name="resumes",
        schema=resume_schema,
        mode="create"
    )

# ---------- CHUNKING ----------
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """Simple sliding window chunking."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

# ---------- STORE ----------
def store_resume(filename: str, text: str, user_id: str, api_key: str = None):
    print(f"DEBUG: Storing resume {filename} for user {user_id} (text length: {len(text)})")
    table = get_or_create_table()
    embeddings = get_embeddings_model(api_key=api_key)
    
    # Chunk the resume text for better semantic search
    chunks = chunk_text(text)
    print(f"DEBUG: Created {len(chunks)} chunks for {filename}")
    
    data = []
    for i, chunk in enumerate(chunks):
        # Only print every 10th chunk to reduce noise
        if i % 10 == 0:
            print(f"DEBUG: Generating embedding for chunk {i+1}/{len(chunks)}...")
        vector = embeddings.embed_query(chunk)
        data.append({
            "id": str(uuid4()),
            "user_id": user_id,
            "filename": filename,
            "text": chunk, # Store the chunk text
            "vector": vector
        })
    
    print(f"DEBUG: Adding {len(data)} rows to LanceDB for {filename}")
    table.add(data)
    print(f"DEBUG: Successfully stored {filename}")

# ---------- ACTIVITY SCHEMA ----------
activity_schema = pa.schema([
    pa.field("id", pa.string()),
    pa.field("user_id", pa.string()), # Added for multi-tenancy
    pa.field("type", pa.string()), # 'screen', 'quality', 'skill_gap'
    pa.field("filename", pa.string()),
    pa.field("score", pa.int32()),
    pa.field("decision", pa.string()), # 'SELECTED', 'REJECTED', or N/A
    pa.field("timestamp", pa.string())
])

def get_or_create_activity_table():
    if "activity" in db.table_names():
        return db.open_table("activity")
    return db.create_table("activity", schema=activity_schema, mode="create")

def log_activity(user_id: str, activity_type: str, filename: str, score: int, decision: str = "N/A"):
    from datetime import datetime
    table = get_or_create_activity_table()
    table.add([{
        "id": str(uuid4()),
        "user_id": user_id,
        "type": activity_type,
        "filename": filename,
        "score": score,
        "decision": decision,
        "timestamp": datetime.now().isoformat()
    }])
    print(f"DEBUG: Logged activity: {activity_type} for {filename} (User: {user_id})")

def get_dashboard_stats(user_id: str):
    resumes_table = get_or_create_table()
    activity_table = get_or_create_activity_table()
    
    # Total Resumes (Unique filenames for THIS user)
    # LanceDB filtering support depends on version, usually via where clause or pandas post-filter
    # using pandas post-filter for simplicity in this version
    
    import pandas as pd
    resumes_df = resumes_table.to_pandas()
    
    total_resumes = 0
    if not resumes_df.empty:
        # Filter by user_id
        user_resumes = resumes_df[resumes_df['user_id'] == user_id]
        total_resumes = user_resumes['filename'].nunique()
    
    # Activity Stats
    activity_df = activity_table.to_pandas()
    
    total_screened = 0
    high_matches = 0
    skill_gaps = 0
    recent_activity = []

    if not activity_df.empty:
        # Filter by user_id
        user_activity = activity_df[activity_df['user_id'] == user_id]
        
        total_screened = len(user_activity[user_activity['type'] == 'screen'])
        high_matches = len(user_activity[user_activity['score'] >= 80])
        skill_gaps = len(user_activity[user_activity['type'] == 'skill_gap'])
        
        # Get 5 most recent activities
        recent_df = user_activity.sort_values(by="timestamp", ascending=False).head(5)
        for _, row in recent_df.iterrows():
            recent_activity.append({
                "type": row['type'],
                "filename": row['filename'],
                "score": row['score'],
                "decision": row['decision'],
                "timestamp": row['timestamp']
            })

    return {
        "total_resumes": total_resumes,
        "auto_screened": total_screened,
        "high_matches": high_matches,
        "skill_gaps": skill_gaps,
        "recent_activity": recent_activity
    }

# ---------- SEARCH ----------
def search_resumes_semantic(query: str, user_id: str, limit: int = 5, api_key: str = None):
    print(f"DEBUG: Semantic search query: {query} (User: {user_id})")
    table = get_or_create_table()
    
    total_rows = len(table)
    if total_rows == 0:
        import pandas as pd
        return pd.DataFrame()

    embeddings = get_embeddings_model(api_key=api_key)
    query_vector = embeddings.embed_query(query)
    
    # Use LanceDB's where clause for filtering
    results = table.search(query_vector).where(f"user_id = '{user_id}'").limit(limit).to_pandas()
    print(f"DEBUG: Found {len(results)} matches for user {user_id}")
    return results
