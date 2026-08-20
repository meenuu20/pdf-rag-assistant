import os
import pymupdf
import faiss
import numpy as np

from google import genai
from sentence_transformers import SentenceTransformer


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

embedding_model= SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# -------------------------
# Chunking
# -------------------------

def create_chunks(text, chunk_size=1000, overlap=100):

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

def create_embeddings(texts):

    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy= True,
        normalize_embeddings=True
    )
    return embeddings.astype("float32")

# -------------------------
# Load PDF
# -------------------------
def build_index(pdf_path):
    pdf = pymupdf.open(pdf_path)

    documents = []

    for page_number, page in enumerate(pdf):

        text = page.get_text()

        if text.strip():

            documents.append({
                "text": text,
                "page": page_number + 1
            })


    # -------------------------
    # Create chunks
    # -------------------------

    chunks = []

    for document in documents:

        page_chunks = create_chunks(
            document["text"]
        )

        for chunk in page_chunks:

            chunks.append({
                "text": chunk,
                "page": document["page"]
            })


    # -------------------------
    # Create embeddings
    # -------------------------

    texts = [
        chunk["text"]
        for chunk in chunks
    ]


    embeddings = create_embeddings(texts)

    # -------------------------
    # Create FAISS index
    # -------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index, chunks


# -------------------------
# RAG function
# -------------------------

def ask_question(question,index,chunks):

    # -------------------------
    # Embed user question
    # -------------------------

    query_embedding = embedding_model.encode(
        [question],
        convert_to_numpy= True,
        normalize_embeddings=True
    ).astype("float32")


    # Top 3
    similarities, indices = index.search(
        query_embedding,
        3
    )
    #print("Similarities:", similarities[0])

    # Similarity threshold
    threshold = 0.3

    retrieved_chunks = []


    for similarity, index_id in zip(
        similarities[0],
        indices[0]
    ):

        if similarity >= threshold:

            retrieved_chunks.append({
                "text":chunks[index_id]["text"],
                "page": chunks[index_id]["page"],
                "similarity": float(similarity)
            })


    # No relevant information
    if not retrieved_chunks:

        return {
            "answer": "I don't have enough information in the provided document.",
            "sources": []
        }


    # Build context
    context_parts = []

    for chunk in retrieved_chunks:

        context_parts.append(
            f"Page {chunk['page']}"
            f"(similarity: {chunk['similarity']:.2f}):\n"
            f"{chunk['text']}"
        )


    context = "\n\n".join(
        context_parts
    )


    # Prompt
    prompt = f"""
Answer the question using only the information
provided in the context.

Context:
{context}

Question:
{question}

Instructions:
- Use only the provided context.
- Do not use outside knowledge.
- If the answer is not present in the context, say:
  "I don't have enough information in the provided document."
- Mention the page number(s) that directly support your answer.
- Do not mention a page unless the information used in the answer
  actually comes from that page.
"""


    # Generate answer
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )


    # Get source pages
    sources = []

    for chunk in retrieved_chunks:

        page = chunk["page"]

        if page not in sources:
            sources.append(page)

    sources.sort()

    return {
        "answer": response.text,
        "sources": sources
    }