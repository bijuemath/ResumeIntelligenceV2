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
def store_resume(filename: str, text: str, api_key: str = None):
    print(f"DEBUG: Storing resume {filename} (text length: {len(text)})")
    table = get_or_create_table()
    embeddings = get_embeddings_model(api_key=api_key)
    
    # Chunk the resume text for better semantic search
    chunks = chunk_text(text)
    print(f"DEBUG: Created {len(chunks)} chunks for {filename}")
    
    data = []
    for i, chunk in enumerate(chunks):
        print(f"DEBUG: Generating embedding for chunk {i+1}/{len(chunks)} of {filename}...")
        vector = embeddings.embed_query(chunk)
        data.append({
            "id": str(uuid4()),
            "filename": filename,
            "text": chunk, # Store the chunk text
            "vector": vector
        })
    
    print(f"DEBUG: Adding {len(data)} rows to LanceDB for {filename}")
    table.add(data)
    print(f"DEBUG: Successfully stored {filename}")

# ---------- SEARCH ----------
def search_resumes_semantic(query: str, limit: int = 5, api_key: str = None):
    print(f"DEBUG: Semantic search query: {query}")
    table = get_or_create_table()
    
    # Check if table has data
    total_rows = len(table)
    print(f"DEBUG: Total rows in resumes table: {total_rows}")
    if total_rows == 0:
        print("DEBUG: Table is empty, returning empty DataFrame")
        import pandas as pd
        return pd.DataFrame()

    embeddings = get_embeddings_model(api_key=api_key)
    print("DEBUG: Generating query embedding...")
    query_vector = embeddings.embed_query(query)
    
    print(f"DEBUG: Searching with limit={limit}...")
    results = table.search(query_vector).limit(limit).to_pandas()
    print(f"DEBUG: Found {len(results)} matches")
    return results
