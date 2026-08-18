import os
import pymupdf
import faiss
import numpy as np

from google import genai


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# -------------------------
# Chunking
# -------------------------

def create_chunks(text, chunk_size=500, overlap=50):

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


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


    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts
    )


    embeddings = np.array(
        [item.values for item in result.embeddings],
        dtype="float32"
    )


    # -------------------------
    # Create FAISS index
    # -------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    return index, chunks


# -------------------------
# RAG function
# -------------------------

def ask_question(question,index,chunks
):

    query_result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=question
    )


    query_embedding = np.array(
        [query_result.embeddings[0].values],
        dtype="float32"
    )


    # Top 3
    distances, indices = index.search(
        query_embedding,
        3
    )


    # Similarity threshold
    threshold = 0.7

    retrieved_chunks = []


    for distance, index_id in zip(
        distances[0],
        indices[0]
    ):

        if distance < threshold:

            retrieved_chunks.append(
                chunks[index_id]
            )


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
            f"Page {chunk['page']}:\n"
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

If the answer is not present in the context,
say:

"I don't have enough information in the
provided document."

Mention the page number when possible.
"""


    # Generate answer
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )


    # Get source pages
    sources = []

    for chunk in retrieved_chunks:

        page = chunk["page"]

        if page not in sources:
            sources.append(page)


    return {
        "answer": response.text,
        "sources": sources
    }