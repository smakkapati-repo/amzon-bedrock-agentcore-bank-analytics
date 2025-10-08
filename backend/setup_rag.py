#!/usr/bin/env python3
"""
Setup script to initialize the RAG system with SEC filings
"""

from rag_system import SECFilingsRAG
import os

def main():
    print("Setting up RAG system for SEC filings...")
    
    # Initialize RAG system
    rag = SECFilingsRAG()
    
    # Check if data directory exists
    if not os.path.exists(rag.data_path):
        print(f"Error: Data directory not found at {rag.data_path}")
        print("Please ensure SEC filings are available in the data directory")
        return
    
    # Load documents and build index
    rag.load_documents()
    
    if not rag.documents:
        print("No documents found! Please check the data directory structure.")
        return
    
    print(f"Loaded {len(rag.documents)} document chunks")
    
    # Build and save FAISS index
    rag.build_index()
    rag.save_index()
    
    print("RAG system setup complete!")
    print("You can now start the Flask server with RAG capabilities.")

if __name__ == "__main__":
    main()