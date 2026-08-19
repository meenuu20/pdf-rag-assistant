# PDF RAG Assistant

A document question-answering application built using Retrieval-Augmented Generation (RAG).

The application allows a user to upload a PDF and ask questions about its content. It retrieves relevant information from the uploaded document and uses Gemini to generate an answer based only on the retrieved context.

## Features

- Upload PDF documents
- Extract text from PDF pages
- Split text into smaller chunks
- Generate embeddings using Gemini
- Store embeddings using FAISS
- Retrieve relevant document chunks using similarity search
- Generate answers using Gemini
- Display source page numbers
- FastAPI backend
- React + Vite frontend

## How It Works

The application follows this RAG pipeline:

```text
PDF Upload
    ↓
Text Extraction
    ↓
Text Chunking
    ↓
Gemini Embeddings
    ↓
FAISS Vector Index
    ↓
User Question
    ↓
Question Embedding
    ↓
Similarity Search
    ↓
Relevant Chunks
    ↓
Gemini
    ↓
Answer + Source Pages

Architecture

                React Frontend
                     │
                     │
              HTTP Requests
                     │
                     ▼
                FastAPI
                     │
                     ▼
                RAG Engine
                /        \
               /          \
            FAISS        Gemini
          Retrieval     Generation
               \          /
                \        /
                 PDF Context

Tech Stack

Frontend
React
Vite
JavaScript
CSS

Backend
Python
FastAPI
Uvicorn

RAG
PyMuPDF
Gemini Embeddings
FAISS
NumPy
Gemini Generative Model
