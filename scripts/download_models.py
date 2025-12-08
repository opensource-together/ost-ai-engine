import os
from sentence_transformers import SentenceTransformer

def download_model():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Downloading model {model_name}...")
    # This will download the model to the directory specified by SENTENCE_TRANSFORMERS_HOME
    # or default to ~/.cache/huggingface/sentence_transformers
    SentenceTransformer(model_name)
    print(f"Model {model_name} downloaded successfully.")

if __name__ == "__main__":
    download_model()
