from django.db import models
from pgvector.django import VectorField

class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=255)

class TextChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    # embedding = VectorField(dimensions=1536)  # OpenAI ada-002 embedding size
    embedding = VectorField(dimensions=768)
    # embedding = ArrayField(models.FloatField(), size=768)
    class Meta:
        indexes = [
            models.Index(fields=['document']),
        ]