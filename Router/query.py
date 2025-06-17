from fastapi import Request,APIRouter ,Depends ,HTTPException,status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from .auth import get_current_user
from typing import Annotated
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# Load env vars
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

router = APIRouter(prefix='/query',tags=['query'])

user_dependency=Annotated[dict,Depends(get_current_user)]


# Initialize Embedding model
embedding = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# Connect to Qdrant
client = QdrantClient(
    url="http://localhost:6333",
    prefer_grpc=False
)
collection_name = "db1"

# Set up the Qdrant vector store
db = Qdrant(
    client=client,
    embeddings=embedding,
    collection_name=collection_name
)

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY
)

reranker_model_name = "BAAI/bge-reranker-base"
tokenizer = AutoTokenizer.from_pretrained(reranker_model_name)
model = AutoModelForSequenceClassification.from_pretrained(reranker_model_name)
model.eval()

def rerank(query, docs, top_k=5):
    pairs = [(query, doc.page_content) for doc in docs]
    inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        scores = model(**inputs).logits.squeeze(-1)
    scores = F.softmax(scores, dim=0)

    scored_docs = list(zip(docs, scores.tolist()))
    ranked = sorted(scored_docs, key=lambda x: x[1], reverse=True)
    return [doc for (doc, _) in ranked[:top_k]]

def keyword_search(query, all_docs, top_k=5):
    matches = [doc for doc in all_docs if query.lower() in doc.page_content.lower()]
    return matches[:top_k]

# In-memory chat history
chat_history = []

# Request schema
class QueryRequest(BaseModel):
    query: str

# POST endpoint for RAG chat
@router.post("/ask")
async def rag_chat(user :user_dependency ,request: QueryRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        user_input = request.query

        # Dense search
        docs_dense = [doc for doc, _ in db.similarity_search_with_score(query=user_input, k=10)]

        # Keyword search
        all_docs = db.similarity_search(query="", k=100)
        docs_keyword = keyword_search(user_input, all_docs, top_k=5)

        # Merge, deduplicate, rerank
        combined_docs = docs_dense + docs_keyword
        unique_docs = {doc.page_content: doc for doc in combined_docs}.values()
        reranked_docs = rerank(user_input, list(unique_docs), top_k=5)

        # Prepare context
        retrieved_context = "\n\n".join([doc.page_content for doc in reranked_docs])
        retrieved_chunks = [doc.page_content for doc in reranked_docs]
        retrieved_context = "\n\n".join(retrieved_chunks)

        prompt = f"""Use the context below to answer the question.

        Context:
        {retrieved_context}

        Chat history:
        {chr(10).join(chat_history)}

         Question:
        {user_input}

        Answer:"""

        # Get LLM Response
        response = llm.invoke(prompt)
        answer = response.content

        # # Log chunks to console
        # print("\n=== Retrieved Chunks ===")
        # for i, chunk in enumerate(retrieved_chunks, 1):
        #     print(f"\nChunk {i}:\n{chunk}\n")

        # Save to chat history
        chat_history.append(f"You: {user_input}")
        chat_history.append(f"Gemini: {answer}")

        return {
        "response": answer,
        "relevant_chunks": retrieved_chunks
    }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.delete("/history")
async def clear_history(user:user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)    
    chat_history.clear()