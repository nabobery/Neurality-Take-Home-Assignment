from rest_framework import serializers
from .models import Document, TextChunk

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'file_path']  # Include all relevant fields

class TextChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextChunk
        fields = ['id', 'document', 'content', 'embedding']  # Include all relevant fields