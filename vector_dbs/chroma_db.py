from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import pandas as pd
from typing import List, Dict, Any, Optional

# Testing
class ChromaVectorDB:
    def __init__(self,
                 collection_name: str = "default_collection",
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "mxbai-embed-large"):
        """
        Initialize ChromaVectorDB

        Args:
            collection_name: Name of the collection in Chroma
            persist_directory: Directory to persist the database
            embedding_model: Model name for embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.embeddings = OllamaEmbeddings(model=embedding_model)

        self.vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )

    
    def view_data(self, limit: int = 10):
        """
        View documents stored in the vector database

        Args:
            limit: Maximum number of documents to display
        """
        try:
            # Get all documents by doing a similarity search with a generic query
            # This is a workaround since Chroma doesn't have a direct "get all" method
            all_docs = self.vector_store.similarity_search("", k=limit)

            if not all_docs:
                print("No documents found in the database")
                return

            print(f"Found {len(all_docs)} documents in the database:")
            print("-" * 50)

            for i, doc in enumerate(all_docs, 1):
                print(f"Document {i}:")
                print(f"Content: {doc.page_content[:100]}...")  # Show first 100 chars
                print(f"Metadata: {doc.metadata}")
                print("-" * 30)

        except Exception as e:
            print(f"Error viewing data: {e}")
    
    
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store

        Args:
            documents: List of Document objects to add
        """
        self.vector_store.add_documents(documents=documents)


    def delete_all_data(self):
        """
        Delete all documents from the vector database collection
        """
        try:
            self.vector_store.delete_collection()
            print(f"Successfully deleted all data from collection '{self.collection_name}'")

            # Recreate the collection after deletion
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print(f"Collection '{self.collection_name}' recreated and ready for new data")

        except Exception as e:
            print(f"Error deleting data: {e}")

    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None):
        """
        Get a retriever for similarity search

        Args:
            search_kwargs: Additional search parameters (e.g., {"k": 5})

        Returns:
            Retriever object for similarity search
        """
        if search_kwargs is None:
            search_kwargs = {"k": 5}

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    # Untested similiairty search method 
    def similarity_search(self, query: str, k: int = 5):
        """
        Perform a similarity search in the vector database.

        Args:
            query: The search query string.
            k: Number of top similar documents to return.

        Returns:
            List of Document objects most similar to the query.
        """
        if not hasattr(self, 'vector_store') or self.vector_store is None:
            print("Vector store is not initialized.")
            return []

        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []


    # get collection count method

    def load_csv(self,
                csv: str,
                folder: str = "data",
                collection_name: Optional[str] = None,
                content_columns: Optional[List[str]] = None,
                metadata_columns: Optional[List[str]] = None,
                id_column: Optional[str] = None):
        """
        Load data from a CSV file into the vector database.

        Args:
            csv: Name of the CSV file (e.g., "my_data.csv").
            folder: Folder path to look for the CSV file. Default is "data".
            collection_name: Name of the collection. If None, csv filename (without extension) is used.
            content_columns: List of column names to combine for document content.
                            If None, all columns are used for content.
            metadata_columns: List of column names to include as metadata.
                            If None, no metadata is included.
            id_column: Column name to use as document ID (if None, uses row index).
        """
        import pandas as pd
        from langchain_core.documents import Document
        import os

        # Construct full path
        csv_path = os.path.join(folder, csv)

        # Determine collection name
        if collection_name is None:
            collection_name = os.path.splitext(csv)[0]

        df = pd.read_csv(csv_path)
        documents = []

        for i, row in df.iterrows():
            # Use all columns for content if content_columns is None
            if content_columns is None:
                content_parts = [f"{col}: {row[col]}" for col in df.columns]
            else:
                content_parts = [str(row[col]) for col in content_columns if col in df.columns]
            content = " ".join(content_parts)

            # Build metadata
            metadata = {}
            if metadata_columns:
                for col in metadata_columns:
                    if col in df.columns:
                        metadata[col] = row[col]

            # Determine document ID
            doc_id = str(row[id_column]) if id_column and id_column in df.columns else str(i)

            document = Document(
                page_content=content,
                metadata=metadata,
                id=doc_id
            )
            documents.append(document)

        # Initialize Chroma with the determined collection name
        self.vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

        self.add_documents(documents)
        print(f"Loaded {len(documents)} documents into collection '{collection_name}' from {csv_path}")