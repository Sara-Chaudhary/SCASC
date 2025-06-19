# download_model.py
from sentence_transformers import SentenceTransformer
model_name = "BAAI/bge-small-en-v1.5"
print(f"Downloading and caching model: {model_name}")
SentenceTransformer(model_name)
print("Model download complete.")