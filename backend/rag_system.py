import os
import json
import faiss
import numpy as np
import boto3
import pickle

class SECFilingsRAG:
    def __init__(self, data_path="../../peer-bank-analytics/data/sec-filings"):
        self.data_path = data_path
        self.bedrock = boto3.client('bedrock-runtime')
        self.index = None
        self.documents = []
        self.metadata = []
        
    def load_documents(self):
        """Load and chunk SEC filings"""
        print("Loading SEC filings...")
        
        for bank_dir in os.listdir(self.data_path):
            bank_path = os.path.join(self.data_path, bank_dir)
            if not os.path.isdir(bank_path):
                continue
                
            for year_dir in os.listdir(bank_path):
                year_path = os.path.join(bank_path, year_dir)
                if not os.path.isdir(year_path):
                    continue
                    
                for filing_type in os.listdir(year_path):
                    filing_path = os.path.join(year_path, filing_type)
                    if not os.path.isdir(filing_path):
                        continue
                        
                    # Limit to last 3 years only
                    if int(year_dir) < 2023:
                        continue
                        
                    for file_name in os.listdir(filing_path):
                        if file_name.endswith('.txt'):
                            file_path = os.path.join(filing_path, file_name)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # Process all files but with smart chunking
                                print(f"Processing: {file_name}")
                                    
                                # Chunk the document
                                chunks = self.chunk_document(content)
                                for i, chunk in enumerate(chunks):
                                    self.documents.append(chunk)
                                    self.metadata.append({
                                        'bank': bank_dir,
                                        'year': year_dir,
                                        'filing_type': filing_type,
                                        'file': file_name,
                                        'chunk_id': i
                                    })
                            except Exception as e:
                                print(f"Error loading {file_path}: {e}")
                                
        print(f"Loaded {len(self.documents)} document chunks from last 3 years (2023-2025)")
        
    def chunk_document(self, text, chunk_size=4000, overlap=800):
        """Split document into overlapping chunks"""
        # Skip if text is too short
        if len(text) < 1000:
            return []
            
        chunks = []
        # Take strategic sections: beginning, middle, end
        sections = [
            text[:len(text)//3],  # First third
            text[len(text)//3:2*len(text)//3],  # Middle third  
            text[2*len(text)//3:]  # Last third
        ]
        
        for section in sections:
            if len(section) > chunk_size:
                # Take first chunk from each section
                chunk = section[:chunk_size]
                last_period = chunk.rfind('.')
                if last_period > chunk_size * 0.7:
                    chunk = chunk[:last_period + 1]
                chunks.append(chunk.strip())
            else:
                chunks.append(section.strip())
                
        return chunks[:3]  # Max 3 chunks per document
        
    def get_embeddings(self, texts):
        """Generate embeddings using Amazon Titan Embeddings V2"""
        embeddings = []
        
        for text in texts:
            response = self.bedrock.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                body=json.dumps({
                    "inputText": text[:8000],  # Titan V2 limit
                    "dimensions": 1024,
                    "normalize": True
                })
            )
            
            result = json.loads(response['body'].read())
            embeddings.append(result['embedding'])
            
        return np.array(embeddings)
        
    def build_index(self):
        """Create FAISS index from documents"""
        print("Building FAISS index with Amazon Titan Embeddings V2...")
        
        # Generate embeddings in batches
        batch_size = 10
        all_embeddings = []
        
        for i in range(0, len(self.documents), batch_size):
            batch = self.documents[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(self.documents)-1)//batch_size + 1}")
            
            batch_embeddings = self.get_embeddings(batch)
            all_embeddings.append(batch_embeddings)
            
        embeddings = np.vstack(all_embeddings)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.index.add(embeddings.astype('float32'))
        
        print(f"Built index with {self.index.ntotal} vectors")
        
    def save_index(self, index_path="sec_filings_index"):
        """Save FAISS index and metadata"""
        faiss.write_index(self.index, f"{index_path}.faiss")
        
        with open(f"{index_path}_metadata.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata
            }, f)
            
        print(f"Saved index to {index_path}")
        
    def load_index(self, index_path="sec_filings_index"):
        """Load FAISS index and metadata"""
        try:
            self.index = faiss.read_index(f"{index_path}.faiss")
            
            with open(f"{index_path}_metadata.pkl", 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.metadata = data['metadata']
                
            print(f"Loaded index with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            print(f"Failed to load index: {e}")
            return False
            
    def search(self, query, bank_filter=None, k=5):
        """Search for relevant documents"""
        if self.index is None:
            return []
            
        # Generate query embedding
        query_embedding = self.get_embeddings([query])
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), k * 3)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
                
            metadata = self.metadata[idx]
            
            # Apply bank filter
            if bank_filter and bank_filter.upper() not in metadata['bank'].upper():
                continue
                
            results.append({
                'content': self.documents[idx],
                'score': float(score),
                'metadata': metadata
            })
            
            if len(results) >= k:
                break
                
        return results
        
    def initialize(self):
        """Initialize RAG system"""
        if not self.load_index():
            print("Index not found, building new one...")
            self.load_documents()
            if self.documents:
                self.build_index()
                self.save_index()
            else:
                print("No documents loaded!")
                return False
        return True

# Global RAG instance
rag_system = SECFilingsRAG()