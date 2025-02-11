import os
from typing import List, Tuple
from django.db import connection
from django.conf import settings  # Make sure to import settings for configuration
from ..models import TextChunk
import google.generativeai as genai

class QAService:
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        # Configure the Gemini (Google Generative AI) API using the API key set in settings
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')  # Use the Gemini model of your choice

    def find_relevant_chunks(self, query_embedding: List[float], limit: int = 3) -> List[TextChunk]:
        # Using pgvector's cosine similarity search to retrieve the most similar text chunks
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, content
                FROM chat_textchunk
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, [query_embedding, limit])
            results = cursor.fetchall()
        
        return [TextChunk.objects.get(id=row[0]) for row in results]

    def generate_response(self, query: str, context: str) -> str:
        prompt = f"""
        Context: {context}
        
        Question: {query}
        
        Please answer the question based on the context provided. If the context doesn't contain relevant information,
        please indicate that and provide a general response.
        
        Answer:"""
        # Use Gemini to generate a response based on the prompt.
        response = self.model.generate_content(prompt)
        return response.text

    def get_answer(self, query: str) -> str:
        query_embedding = self.embedding_service.generate_embedding(query)
        relevant_chunks = self.find_relevant_chunks(query_embedding)
        
        if not relevant_chunks:
            return self.generate_response(query, "No relevant context found.")
        
        context = "\n".join([chunk.content for chunk in relevant_chunks])
        return self.generate_response(query, context)