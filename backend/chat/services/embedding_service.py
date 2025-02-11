import google.generativeai as genai
from typing import List
from django.conf import settings
# import os

class EmbeddingService:
    def __init__(self):
        # genai.configure(api_key=os.environ["GOOGLE_API_KEY"]) # Use environment variable
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = 'models/embedding-001' # Gemini embedding model

    def generate_embedding(self, text: str) -> List[float]:
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query" # Important for RAG
        )
        return result['embedding']

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document" # Important for RAG
            )
            embeddings.append(result['embedding'])
        return embeddings