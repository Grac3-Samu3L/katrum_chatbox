from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2, numpy as np, requests, os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or set your Vercel frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    port=os.getenv("DB_PORT", 5432)
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", 11434)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

def get_embedding(text: str):
    response = requests.post(
        f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/embeddings",
        json={"model": OLLAMA_MODEL, "prompt": text},
        timeout=30
    )
    return np.array(response.json()['embedding'], dtype=np.float32)

def get_relevant_chunks(embedding, top_k=5):
    cur = conn.cursor()
    embedding_str = "[" + ",".join(str(x) for x in embedding.tolist()) + "]"
    sql = """
        SELECT content
        FROM book_vector
        ORDER BY embedding_768 <-> %s::vector
        LIMIT %s;
    """
    cur.execute(sql, (embedding_str, top_k))
    results = cur.fetchall()
    cur.close()
    return [row[0] for row in results]

def query_llm(context: str, question: str):
    full_prompt = f"""You are a medical assistant. Use the context below to answer the user's question.

Context:
{context}

Question:
{question}

Answer:"""
    response = requests.post(
        f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": False},
        timeout=60
    )
    return response.json()['response']

@app.post("/chat")
def chat(query: Query):
    question = query.question
    try:
        embedding = get_embedding(question)
        chunks = get_relevant_chunks(embedding)
        context = "\n\n".join(chunks)
        answer = query_llm(context, question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}
