"""RAG Service for PDF processing and vector storage using ChromaDB"""
import os
from typing import List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader
import logging
import re

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.chroma_persist_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')
        
        # Initialize embeddings - using local HuggingFace model to avoid API quota issues
        logger.info("Initializing HuggingFace embeddings (local model)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",  # Fast, efficient local model
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("Embeddings initialized successfully")
        
        # Initialize ChromaDB
        self.vectorstore = None
        self._initialize_vectorstore()
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def _initialize_vectorstore(self):
        """Initialize ChromaDB vector store"""
        try:
            self.vectorstore = Chroma(
                collection_name="pdf_documents",
                embedding_function=self.embeddings,
                persist_directory=self.chroma_persist_dir
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> tuple[str, List[str]]:
        """Extract text and table of contents from PDF"""
        try:
            reader = PdfReader(pdf_path)
            full_text = ""
            toc = []
            
            # Extract text from all pages
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                full_text += f"\n--- Page {page_num} ---\n{text}"
                
                # Try to identify headings/sections (simple heuristic)
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    # Detect headings (lines that are short, capitalized, or numbered)
                    if line and (
                        (len(line) < 100 and line.isupper()) or
                        re.match(r'^\d+\.\d*\s+[A-Z]', line) or
                        re.match(r'^Chapter\s+\d+', line, re.IGNORECASE) or
                        re.match(r'^Section\s+\d+', line, re.IGNORECASE)
                    ):
                        toc.append(f"Page {page_num}: {line}")
            
            # If no TOC detected, create generic one
            if not toc:
                toc = [f"Page {i+1}" for i in range(len(reader.pages))]
            
            logger.info(f"Extracted {len(reader.pages)} pages from PDF")
            return full_text, toc
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def ingest_pdf(self, pdf_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest PDF into vector store"""
        try:
            # Extract text and TOC
            full_text, toc = self.extract_text_from_pdf(pdf_path)
            
            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)
            
            # Create documents with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    "chunk_id": i,
                    "source": pdf_path,
                    **(metadata or {})
                }
                documents.append(Document(page_content=chunk, metadata=doc_metadata))
            
            # Add to vector store
            self.vectorstore.add_documents(documents)
            
            logger.info(f"Ingested {len(documents)} chunks into vector store")
            
            return {
                "status": "success",
                "chunks_processed": len(documents),
                "table_of_contents": toc
            }
            
        except Exception as e:
            logger.error(f"Error ingesting PDF: {e}")
            raise
    
    def retrieve_relevant_docs(self, query: str, k: int = 5) -> List[Document]:
        """Retrieve relevant documents for a query"""
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"Retrieved {len(results)} relevant documents for query")
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            raise
    
    def clear_vectorstore(self):
        """Clear all documents from vector store"""
        try:
            # Re-initialize to clear
            if os.path.exists(self.chroma_persist_dir):
                import shutil
                shutil.rmtree(self.chroma_persist_dir)
            self._initialize_vectorstore()
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            raise
