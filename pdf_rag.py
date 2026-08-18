import os
import pymupdf as fitz
import faiss
import numpy as np

from google import genai

client= genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def create_chunks(text, chunk_size=500, overlap=50):
    chunks=[]
    start=0

    while start<len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start += chunk_size - overlap
    return chunks

pdf= fitz.open("note.pdf")

documents = []

for page_number, page in enumerate(pdf):
    text = page.get_text()

    if text.strip():
        documents.append({
            "text": text,
            "page": page_number + 1
        })

chunks=[]

for document in documents:

    page_chunks = create_chunks(document["text"])

    for chunk in page_chunks:
        chunks.append({
            "text": chunk,
            "page": document["page"]
        }
        )

texts =[chunk["text"]
        for chunk in chunks]

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=texts
)

embeddings = np.array(
    [item.values for item in result.embeddings],
    dtype="float32"
)

dimension= embeddings.shape[1]

index= faiss.IndexFlatL2(dimension)
index.add(embeddings)


question = input("\n Ask a Question:")

query_result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=question
)

query_embedding = np.array(
    [query_result.embeddings[0].values],
    dtype="float32"
)

distances, indices =index.search(query_embedding,3)


threshold = 0.7
retrieved_chunks =[]

for distance, index_id in zip(distances[0], indices[0]):
    if distance < threshold:
        retrieved_chunks.append(chunks[index_id])

print("\nDistances:", distances)

print("\nRetrieved Chunks:")

if retrieved_chunks:

    for chunk in retrieved_chunks:

        print("--------------------")

        print("Page:", chunk["page"])

        print(chunk["text"])

else:

    print("No relevant chunks found.")

context_parts = []

for chunk in retrieved_chunks:
    context_parts.append(f"Page {chunk['page']}:\n {chunk['text']}")

context = "\n\n".join(context_parts)

prompt = f"""
Answer the question using only the information
provided in the context.

Context:
{context}

Question:
{question}

If the answer is not present in the context,
say:

"I don't have enough information in the provided document."

Mention the page number when possible.
"""
response =client.models.generate_content(
    model="gemini-3.5-flash",
    contents=prompt
)

print("\nResponse:")
print(response.text)
