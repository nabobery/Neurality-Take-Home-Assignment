import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Document, TextChunk
from .services.document_processor import DocumentProcessor
from .services.embedding_service import EmbeddingService
# from .services.qa_service import QAService
from .services.advanced_qa_service import AdvancedQAService
from django.conf import settings
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    document_processor = DocumentProcessor()
    embedding_service = EmbeddingService()
    # qa_service = QAService(embedding_service)

    @action(detail=False, methods=['POST'])
    def upload(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Save file
        file_path = os.path.join(settings.MEDIA_ROOT, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Process document
        text = self.document_processor.extract_text_from_pdf(file_path)
        document = Document.objects.create(
            title=file.name,
            content=text,
            file_path=file_path
        )

        # Generate chunks and embeddings
        chunks = self.document_processor.split_text(text)
        embeddings = self.embedding_service.generate_embeddings(chunks)

        # Save chunks with embeddings
        for chunk_text, embedding in zip(chunks, embeddings):
            TextChunk.objects.create(
                document=document,
                content=chunk_text,
                embedding=embedding
            )

        return Response({'message': 'Document processed successfully'}, status=status.HTTP_201_CREATED)

    # @action(detail=False, methods=['POST'])
    # def ask(self, request):
    #     query = request.data.get('query')
    #     if not query:
    #         return Response({'error': 'No query provided'}, status=status.HTTP_400_BAD_REQUEST)

    #     answer = self.qa_service.get_answer(query)
    #     return Response({'answer': answer})
    
    @action(detail=False, methods=['POST'])
    def ask(self, request):
        query = request.data.get("query", "")
        if not query:
            return Response({'error': 'No query provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Retrieve all text chunks from the database
        # (In a real scenario, you might only load chunks relevant to the documents in question)
        # texts = list(TextChunk.objects.values_list("content", flat=True))
        text_chunks = list(TextChunk.objects.all())
        
        # Initialize the embedding service and Advanced QA Service
        embedding_service = EmbeddingService()
        advanced_qa_service = AdvancedQAService(embedding_service=embedding_service, text_chunks=text_chunks)
        
        # Get recent chat history if needed (e.g., last 5 messages stored in the session)
        chat_memory = request.session.get("chat_history", "")
        
        try:
            answer = advanced_qa_service.get_answer(query, chat_memory)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"answer": answer})