# File: rag/pipeline.py
# --- CORRECTED with robust checks for type safety ---

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Tuple, Dict, Any

from database.connection import Database

class RagPipeline:
    def __init__(self, db: Database):
        """
        Initializes the RAG pipeline with a database connection.
        """
        self.db = db
        # Use a lightweight model for generating embeddings
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.documents = []
        print("RAG Pipeline initialized.")

    def build_index(self, table_name: str, content_column: str, id_column: str):
        """
        Fetches data from the database and builds a FAISS vector index.
        """
        self.documents = self.db.fetch_all_for_rag(table_name, [id_column, content_column])
        
        if not self.documents:
            print(f"RAG Pipeline: No documents found in table '{table_name}' to build index.")
            return

        # --- FIX 1: Add 'if doc is not None' to prevent error on potential None values ---
        contents = [doc.get(content_column.lower(), "") or "" for doc in self.documents if doc is not None]
        
        # If after filtering, there are no contents, do nothing.
        if not contents:
            print(f"RAG Pipeline: No valid content found in documents to build index.")
            return

        print(f"RAG Pipeline: Creating embeddings for {len(contents)} documents...")
        embeddings = self.embedder.encode(contents, convert_to_tensor=False)
        
        # --- FIX 2: Add a check to ensure embeddings are not empty before adding to index ---
        if embeddings.size > 0:
            # Build the FAISS index for efficient similarity search
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(np.array(embeddings, dtype=np.float32))
            print("RAG Pipeline: Index built successfully.")
        else:
            print("RAG Pipeline: Embedding generation resulted in no data; index not built.")


    def get_context(
        self, 
        query: str, 
        table_name: str, 
        content_column: str, 
        id_column: str = 'FIR_REG_NUM', # Default to the correct ID for your main table
        k: int = 3
    ) -> Tuple[str, List[str]]:
        """
        Finds the most relevant documents for a query and returns them as context.
        """
        if self.index is None:
            self.build_index(table_name, content_column, id_column)

        if not self.documents or self.index is None:
            return "No relevant context found.", []

        query_embedding = self.embedder.encode([query], convert_to_tensor=False)
        
        # NOTE: The following line is functionally CORRECT, even if Pylance shows a warning.
        # This is a known issue with type checkers and the faiss library.
        distances, indices = self.index.search(np.array(query_embedding, dtype=np.float32), k)

        context_parts = []
        sources = []
        
        id_column_lower = id_column.lower()
        content_column_lower = content_column.lower()

        for i in indices[0]:
            if i < len(self.documents):
                doc = self.documents[i]
                if doc: # Added a check for doc just in case
                    source_id = doc.get(id_column_lower)
                    content = doc.get(content_column_lower, "No content available.")
                    
                    context_parts.append(content)
                    sources.append(f"Source FIR: {source_id}")

        context_str = "\n\n---\n\n".join(context_parts)
        return context_str, sources