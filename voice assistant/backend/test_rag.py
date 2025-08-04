#!/usr/bin/env python3
"""
Test script for RAG system functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

load_dotenv()

def test_rag_system():
    """Test the RAG system functionality"""
    try:
        from app.services.rag_service import rag_service
        
        print("🧪 Testing RAG System...")
        
        # Test 1: Check if job descriptions are loaded
        print("\n1. Checking job descriptions...")
        jd_count = rag_service.jd_vector_store._collection.count()
        print(f"   ✅ Found {jd_count} job description documents in vector store")
        
        # Test 2: Test JD content retrieval
        print("\n2. Testing JD content retrieval...")
        jd_files = ['backend_developer.txt', 'frontend_developer.txt', 'genai_developer.txt', 'full_stack_developer.txt']
        
        for jd_file in jd_files:
            content = rag_service.get_jd_content(jd_file)
            if content:
                print(f"   ✅ Successfully retrieved content for {jd_file}")
            else:
                print(f"   ❌ Failed to retrieve content for {jd_file}")
        
        # Test 3: Test vector store retrieval
        print("\n3. Testing vector store retrieval...")
        try:
            retriever = rag_service.jd_vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={'k': 3, 'lambda_mult': 0.25}
            )
            
            docs = retriever.get_relevant_documents("backend developer python fastapi")
            print(f"   ✅ Successfully retrieved {len(docs)} relevant documents")
            
            for i, doc in enumerate(docs):
                print(f"      Document {i+1}: {doc.metadata.get('source', 'Unknown')}")
                
        except Exception as e:
            print(f"   ❌ Vector store retrieval failed: {e}")
        
        # Test 4: Test embeddings
        print("\n4. Testing embeddings...")
        try:
            test_text = "Python developer with FastAPI experience"
            embedding = rag_service.embeddings.embed_query(test_text)
            print(f"   ✅ Successfully generated embedding with {len(embedding)} dimensions")
        except Exception as e:
            print(f"   ❌ Embedding generation failed: {e}")
        
        # Test 5: Test LLM
        print("\n5. Testing LLM...")
        try:
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                ("user", "Say 'Hello, RAG system is working!'")
            ])
            
            chain = prompt | rag_service.model
            response = chain.invoke({})
            print(f"   ✅ LLM response: {response.content}")
            
        except Exception as e:
            print(f"   ❌ LLM test failed: {e}")
        
        print("\n🎉 RAG System Test Complete!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_rag_system() 