import os
import re
import google.generativeai as genai
from typing import List, Tuple, Dict
from rank_bm25 import BM25Okapi
from django.db import connection
from django.conf import settings
from ..models import TextChunk
from .embedding_service import EmbeddingService
from core.log_config import LoggerSetup # Import the new logger setup class

# --- Get the configured logger ---
logger = LoggerSetup.get_logger(__name__) # Use the class method to get the logger
# --- End Logger Setup ---


class AdvancedQAService:
    """
    AdvancedQAService implements an enhanced RAG pipeline with minimal dependencies:
      - Query expansion using HyDE (via Gemini).
      - Hybrid retrieval combining pgvector (vector search) and BM25 (lexical search).
      - Reciprocal Rank Fusion (RRF) for combining search results.
      - Chat memory integration into the final prompt.
      - Generation via Gemini.
    """
    def __init__(self, embedding_service: EmbeddingService, text_chunks: List[TextChunk]):
        logger.info("Initializing AdvancedQAService...")
        self.embedding_service = embedding_service
        self.model_name = "gemini-1.5-pro"

        # --- Fetch data and initialize core components ---
        try:
            # Fetch all chunks once during initialization for BM25 and mapping
            # This assumes the number of chunks is manageable in memory.
            # For very large datasets, consider fetching BM25 candidates separately.
            # self.all_chunks: List[TextChunk] = list(TextChunk.objects.all())
            self.all_chunks = text_chunks
            logger.info(f"Fetched {len(self.all_chunks)} TextChunks.")
            if not self.all_chunks:
                # Handle case where there are no chunks in the DB
                print("Warning: No TextChunks found in the database.")
                # Depending on requirements, you might raise an error or allow proceeding
                raise ValueError("No TextChunks found in the database for AdvancedQAService.")
            self.chunk_map: Dict[int, TextChunk] = {chunk.id: chunk for chunk in self.all_chunks}
        except Exception as e:
            logger.error(f"Failed to fetch TextChunks from database: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch TextChunks from database: {e}")

        # Setup BM25 if chunks are available
        if self.all_chunks:
            self.setup_bm25()
        else:
            logger.warning("Skipping BM25 setup as no chunks were loaded.")
            self.bm25_model = None  # No model if no data

        try:
            logger.info("Configuring Gemini API...")
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            logger.info(f"Initializing Gemini model: {self.model_name}")
            self.model = genai.GenerativeModel("gemini-1.5-pro")
            logger.info("Gemini model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to configure or initialize Gemini model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to configure or initialize Gemini model: {e}")
        logger.info("AdvancedQAService initialized successfully.")

    def setup_bm25(self):
        """Prepare a BM25 model on the text chunk content."""
        logger.info("Setting up BM25 model...")
        tokenized_corpus = [
            re.sub(r"\W+", " ", chunk.content).lower().split()
            for chunk in self.all_chunks
        ]
        if not any(tokenized_corpus): # Check if corpus is empty after tokenization
            logger.warning("Warning: Corpus is empty after tokenization for BM25.")
            self.bm25_model = None
            return
        try:
            logger.info(f"Tokenized corpus for BM25 (sample: {len(tokenized_corpus)} documents).")
            self.bm25_model = BM25Okapi(tokenized_corpus)
            logger.info("BM25 model created successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize BM25 model: {e}", exc_info=True)
            self.bm25_model = None

    def hyde_query_expansion(self, query: str) -> str:
        """Expand the query using HyDE with the generative model."""
        logger.info(f"Performing HyDE query expansion for query: '{query[:50]}...'")
        prompt = f"Generate a hypothetical document that is highly relevant to the following query: {query}"
        try:
            # Use the configured Gemini model for HyDE
            response = self.model.generate_content(prompt)
            # It's often better to use the *query* embedding of the hypothetical doc,
            # but for simplicity here we combine the text. Alternatively, use the
            # generated doc directly for embedding search. Let's stick to text combination.
            expansion = response.text
            expanded_query = f"{query}\n{expansion}"
            logger.info(f"HyDE expansion successful. Expanded query length: {len(expanded_query)}")
            # Combine, ensuring query comes first
            return expanded_query
        except Exception as e:
            logger.warning(f"HyDE expansion failed: {e}. Falling back to original query.")
            return query # Fallback to the original query

    def _get_bm25_results(self, query: str, k: int) -> List[Tuple[int, float]]:
        """Get top K results from BM25 as (chunk_id, score) tuples."""
        logger.info(f"Performing BM25 search for query: '{query[:50]}...', k={k}")
        if not self.bm25_model or not self.all_chunks:
            logger.warning("BM25 model not available or no chunks loaded. Returning empty results.")
            return []
        tokenized_query = re.sub(r"\W+", " ", query).lower().split()
        try:
            bm25_scores = self.bm25_model.get_scores(tokenized_query)
        except Exception as e:
            logger.error(f"BM25 scoring failed: {e}", exc_info=True)
            return []

        # Get indices sorted by score, without numpy
        sorted_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

        # Map indices back to chunk IDs and return top K with scores
        results = []
        for i in sorted_indices[:k]:
            # Ensure score is not negative for RRF (BM25 scores can be negative)
            # We only care about rank here, so map score to a positive range if needed,
            # or just use rank directly. Let's use rank.
             results.append((self.all_chunks[i].id, float(k - len(results)))) # Rank-based score
            # Alternatively: results.append((self.all_chunks[i].id, max(0, bm25_scores[i])))
        logger.info(f"BM25 search returned {len(results)} results.")
        return results

    def _get_vector_results(self, query_embedding: List[float], k: int) -> List[Tuple[int, float]]:
        """Get top K results from pgvector as (chunk_id, similarity_score) tuples."""
        if not query_embedding:
            logger.warning("No query embedding provided for vector search. Returning empty results.")
            return []
        try:
            with connection.cursor() as cursor:
                # Using cosine similarity (1 - cosine distance)
                # pgvector's <=> operator gives distance (lower is better)
                # To get similarity (higher is better), use 1 - distance or use <#> operator (inner product)
                # Let's use cosine distance and convert to similarity later for RRF ranking.
                cursor.execute(
                    """
                    SELECT id, embedding <=> %s::vector AS distance
                    FROM chat_textchunk
                    ORDER BY distance ASC
                    LIMIT %s
                    """,
                    [query_embedding, k],
                )
                results = cursor.fetchall()
            final_results = [(row[0], float(row[1])) for row in results]
            logger.info(f"Vector search returned {len(final_results)} results.")
            # logger.debug(f"Vector results (IDs): {[r[0] for r in final_results]}")
            return final_results
        except Exception as e:
            logger.error(f"pgvector search failed: {e}", exc_info=True)
            return []

    def ensemble_retrieval(
        self, query: str, query_embedding: List[float], top_k: int = 10, rrf_k: int = 60
    ) -> List[TextChunk]:
        """
        Retrieve documents using BM25 and Vector Search, then combine using RRF.
        Args:
            query: The user query string.
            query_embedding: The embedding vector for the query.
            top_k: The final number of documents to return.
            rrf_k: The constant used in Reciprocal Rank Fusion scoring (usually 60).
        Returns:
            A list of the top_k most relevant TextChunk objects.
        """
        logger.info(f"Starting ensemble retrieval for query: '{query[:50]}...', top_k={top_k}")
        # 1. Get results from BM25 (lexical)
        # We get more results initially (e.g., 2*top_k) to feed into RRF
        bm25_results = self._get_bm25_results(query, k=top_k * 2) # List of (id, rank_score)

        # 2. Get results from Vector DB (semantic)
        vector_results = self._get_vector_results(query_embedding, k=top_k * 2) # List of (id, distance)

        # 3. Combine using Reciprocal Rank Fusion (RRF)
        # Create rank dictionaries (rank starts from 1)
        # For BM25, higher score is better rank (already sorted descending)
        bm25_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(bm25_results)}
        # For Vector, lower distance is better rank (already sorted ascending)
        vector_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(vector_results)}

        # Get all unique document IDs
        all_doc_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())

        # Calculate RRF scores
        rrf_scores: Dict[int, float] = {}
        for doc_id in all_doc_ids:
            score = 0.0
            if doc_id in bm25_ranks:
                score += 1.0 / (rrf_k + bm25_ranks[doc_id])
            if doc_id in vector_ranks:
                score += 1.0 / (rrf_k + vector_ranks[doc_id])
            rrf_scores[doc_id] = score

        # Sort documents by RRF score in descending order
        sorted_ids = sorted(all_doc_ids, key=lambda doc_id: rrf_scores[doc_id], reverse=True)

        # 4. Retrieve the final top_k TextChunk objects using the map
        final_chunk_ids = sorted_ids[:top_k]
        final_chunks = [self.chunk_map[doc_id] for doc_id in final_chunk_ids if doc_id in self.chunk_map]
        logger.info(f"Retrieved final {len(final_chunks)} chunks after RRF.")
        # logger.debug(f"Final chunk IDs after RRF: {final_chunk_ids}")

        # Log if fewer chunks were retrieved than requested due to mapping issues (should be rare)
        if len(final_chunks) < len(final_chunk_ids):
                logger.warning(f"Could not find all RRF-selected chunk IDs in the chunk map. Found {len(final_chunks)} out of {len(final_chunk_ids)}.")

        return final_chunks

    def generate_response(self, query: str, context: str, chat_memory: str = "") -> str:
        """Generates a response using the Gemini model based on query, context, and memory."""
        prompt = f"""
            Chat History (use for context and tone if relevant, but prioritize provided Context for answering the Question):
            {chat_memory}

            Context Documents:
            {context}

            Question:
            {query}

            Based *only* on the provided Context Documents and relevant Chat History, please provide a comprehensive and accurate answer to the Question. If the context does not contain the answer, state that clearly.

            Answer:
        """
        logger.info(f"Sending prompt to Gemini model ({self.model_name}). Prompt length: {len(prompt)}")
        try:
            response = self.model.generate_content(prompt)
            # Basic safety check example
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason = response.prompt_feedback.block_reason
                    logger.warning(f"Gemini response blocked due to safety concerns: {block_reason}")
                    return f"My response was blocked due to safety concerns ({block_reason}). Please rephrase your query."

            generated_text = response.text
            logger.info(f"Received response from Gemini. Response length: {len(generated_text)}")
            # logger.debug(f"Full response from Gemini:\n{generated_text}") # Log full response if needed
            return generated_text
        except Exception as e:
            print(f"Gemini generation failed: {e}")
            # Provide a fallback response
            return "I encountered an error trying to generate a response. Please try again."


    def get_answer(self, query: str, chat_memory: str = "") -> str:
        """
        Main method to get an answer for a query, incorporating the RAG pipeline.
        """
        logger.info(f"--- Starting get_answer process for query: '{query}' ---")
        # 1. Expand the query with HyDE (optional, could be configurable)
        # For minimal approach, maybe start without HyDE? Let's keep it for now.
        expanded_query = self.hyde_query_expansion(query) # Currently combines text

        # 2. Generate embedding for the *original* query (often better for retrieval)
        # Alternatively use expanded_query if HyDE is reliable. Let's use original.
        logger.info(f"Generating embedding for query: '{query[:50]}...'")
        try:
            query_embedding = self.embedding_service.generate_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}", exc_info=True)
            return "I could not process your query due to an embedding error."

        # 3. Retrieve relevant chunks using Hybrid Search + RRF
        # Pass the original query for BM25 and the embedding for vector search
        retrieval_top_k = 5 # Configurable: how many chunks to retrieve for context
        logger.info(f"Starting ensemble retrieval to find top {retrieval_top_k} chunks.")
        relevant_chunks = self.ensemble_retrieval(query, query_embedding, top_k=retrieval_top_k)

        # 4. Build context
        logger.info("Building context from retrieved chunks.")
        if not relevant_chunks:
            context = "No relevant context documents were found in the knowledge base."
            logger.warning("No relevant chunks found during retrieval.")
        else:
            context = "\n\n---\n\n".join([chunk.content for chunk in relevant_chunks])
            logger.info(f"Context built successfully. Length: {len(context)}")
            # logger.debug(f"Context built:\n{context}") # Log full context if needed

        # 5. Generate the final response using the LLM
        logger.info("Generating final response using LLM.")
        final_answer = self.generate_response(query, context, chat_memory)
        logger.info(f"--- Finished get_answer process for query: '{query}' ---")
        return final_answer