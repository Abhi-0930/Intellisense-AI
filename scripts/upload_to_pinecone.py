#!/usr/bin/env python3
"""
Script to upload sample data to Pinecone vector database.
Run this once to populate the index with the sample records.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.retrieval_agent.utils import (
    _get_index, 
    namespace, 
    records
)
from app.core.logging import log_info, log_error

def upload_records():
    """Upload records to Pinecone"""
    try:
        log_info("Starting Pinecone upload...")
        index = _get_index()
        
        # Clean and flatten records
        clean_records = []
        for r in records:
            clean_records.append({
                "_id": r["_id"],
                "chunk_text": r["chunk_text"],
                "source_type": r["source_type"],
                "source_url": r["source_url"],
                "category": r["metadata"]["category"]
            })
        
        log_info(f"Prepared {len(clean_records)} records for upload")
        
        # Upload to Pinecone
        index.upsert_records(namespace, clean_records)
        
        log_info(f"Successfully uploaded {len(clean_records)} records to Pinecone namespace: {namespace}")
        
        # Print index stats
        stats = index.describe_index_stats()
        log_info(f"Index stats: {stats}")
        
        return True
    except Exception as e:
        log_error(f"Failed to upload to Pinecone: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure you have:")
        print("1. PINECONE_API_KEY set in your .env file")
        print("2. A valid Pinecone account")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Pinecone Data Upload Script")
    print("=" * 60)
    print()
    
    success = upload_records()
    
    if success:
        print("\n✅ Upload completed successfully!")
        print("You can now use vector retrieval in your queries.")
    else:
        print("\n❌ Upload failed. Check the error messages above.")
        sys.exit(1)
