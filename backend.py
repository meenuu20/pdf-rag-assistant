import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_engine import build_index, ask_question

current_index = None
current_chunks=[]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pdf-rag-assistant-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {
        "message":"RAG API is running"
    }

@app.post("/ask")
def ask(request: QuestionRequest):
    if current_index is None:
        return{
            "answer": "No PDF uploaded yet. Please upload a PDF first.",
            "sources": []
        }
    
    result = ask_question(request.question, current_index,current_chunks)
    return result

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global current_index, current_chunks

    if not file.filename.endswith(".pdf"):
        return{
            "message" : "Invalid file type. Please upload a PDF file."
        }
    os.makedirs("uploads", exist_ok=True)

    filename = os.path.basename(file.filename)

    file_path = os.path.join(
        "uploads",
        filename
    )

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    current_index, current_chunks = build_index(file_path)

    return{
        "message" : "PDF uploaded successfully.",
        "filename": file.filename    }