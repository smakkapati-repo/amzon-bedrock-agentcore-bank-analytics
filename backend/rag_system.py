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
        
    def load_documents_from_s3(self):
        """Load documents from S3 bucket as fallback"""
        import os
        bucket_name = os.environ.get('SEC_FILINGS_BUCKET')
        if not bucket_name:
            print("No S3 bucket configured")
            return False
            
        try:
            s3 = boto3.client('s3')
            print(f"Loading documents from S3 bucket: {bucket_name}")
            
            # List all objects in bucket
            paginator = s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key.endswith('.txt'):
                        # Parse S3 key: BANK/YEAR/FORM/accession.txt
                        parts = key.split('/')
                        if len(parts) == 4:
                            bank, year, form, filename = parts
                            
                            # Download content
                            response = s3.get_object(Bucket=bucket_name, Key=key)
                            content = response['Body'].read().decode('utf-8')
                            
                            # Chunk and add to documents
                            chunks = self.chunk_document(content)
                            for i, chunk in enumerate(chunks):
                                self.documents.append(chunk)
                                self.metadata.append({
                                    'bank': bank,
                                    'year': year,
                                    'filing_type': form,
                                    'file': filename,
                                    'chunk_id': i,
                                    'source': 's3'
                                })
                            
                            print(f"Loaded {len(chunks)} chunks from {key}")
            
            print(f"Loaded {len(self.documents)} document chunks from S3")
            return len(self.documents) > 0
            
        except Exception as e:
            print(f"Error loading from S3: {e}")
            return False
    
    def auto_populate_s3(self):
        """Automatically download and populate S3 with SEC data"""
        import os
        bucket_name = os.environ.get('SEC_FILINGS_BUCKET')
        if not bucket_name:
            return False
            
        try:
            import requests
            import time
            
            s3 = boto3.client('s3')
            print("Auto-populating S3 with SEC filings...")
            
            # Major banks and CIKs
            banks = {
                'JPMORGAN_CHASE': '19617', 'BANK_OF_AMERICA': '70858', 'WELLS_FARGO': '72971',
                'CITIGROUP': '831001', 'GOLDMAN_SACHS': '886982', 'MORGAN_STANLEY': '895421',
                'US_BANCORP': '36104', 'PNC_FINANCIAL': '713676', 'CAPITAL_ONE': '927628', 'TRUIST': '92230'
            }
            
            headers = {'User-Agent': 'BankIQ+ Research (contact@example.com)'}
            uploaded = 0
            
            for bank_name, cik in banks.items():
                print(f"Processing {bank_name}...")
                
                # Get recent filings only (faster)
                url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    recent = data.get('filings', {}).get('recent', {})
                    
                    forms = recent.get('form', [])
                    dates = recent.get('filingDate', [])
                    accessions = recent.get('accessionNumber', [])
                    primary_docs = recent.get('primaryDocument', [])
                    
                    # Get 2 recent filings per bank (faster startup)
                    count = 0
                    for i, (form, date, accession) in enumerate(zip(forms, dates, accessions)):
                        if form in ['10-K', '10-Q'] and date >= '2024-01-01' and count < 2:
                            primary_doc = primary_docs[i] if i < len(primary_docs) else None
                            
                            # Download filing
                            accession_clean = accession.replace('-', '')
                            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}" if primary_doc else f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}.txt"
                            
                            try:
                                filing_response = requests.get(filing_url, headers=headers, timeout=15)
                                if filing_response.status_code == 200:
                                    s3_key = f"{bank_name}/{date[:4]}/{form}/{accession}.txt"
                                    s3.put_object(
                                        Bucket=bucket_name,
                                        Key=s3_key,
                                        Body=filing_response.text.encode('utf-8'),
                                        ContentType='text/plain'
                                    )
                                    uploaded += 1
                                    count += 1
                                    print(f"  Uploaded {form} {date}")
                            except:
                                continue
                            
                            time.sleep(0.1)
                
                time.sleep(0.2)
            
            print(f"Auto-populated S3 with {uploaded} SEC filings")
            return uploaded > 0
            
        except Exception as e:
            print(f"Auto-population failed: {e}")
            return False
    
    def initialize(self):
        """Initialize RAG system with automatic S3 population"""
        # Try local FAISS index first (fastest)
        if self.load_index():
            print("Using pre-built FAISS index")
            return True
        
        print("FAISS index not found, checking S3...")
        
        # Check if S3 has data
        if self.load_documents_from_s3():
            print("Building FAISS index from S3 data...")
            self.build_index()
            self.save_index()
            return True
        
        # Auto-populate S3 if empty
        print("S3 empty, auto-populating with SEC data...")
        if self.auto_populate_s3():
            # Try loading from S3 again
            if self.load_documents_from_s3():
                print("Building FAISS index from auto-populated S3 data...")
                self.build_index()
                self.save_index()
                return True
        
        print("All initialization methods failed!")
        return False

# Global RAG instance
rag_system = SECFilingsRAG()