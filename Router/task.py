from langchain_community.vectorstores import Qdrant
from llama_cloud_services import LlamaParse
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
from langchain.schema import Document
from celery_app import celery
from .query import embedding


load_dotenv()

@celery.task(bind=True)
def make_qdrant(self, file_path: str):
    try:
        parser = LlamaParse()
        document = parser.load_data(file_path)
        all_text = "\n".join(doc.text for doc in document)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=50)
        texts = text_splitter.split_text(all_text)
        documents = [Document(page_content=chunk) for chunk in texts]

        qdrant = Qdrant.from_documents(
            documents,
            embedding,
            url="http://qdrant:6333",
            prefer_grpc=False,
            collection_name="db1"
        )

        return {"status": "success", "message": "Ingested into Qdrant"}
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)