#!/usr/bin/env python3
"""
Azure OpenAI Setup Script
This script helps you set up the missing environment variable for Azure OpenAI.
"""

import os
from dotenv import load_dotenv

def main():
    print("🔧 Azure OpenAI Setup")
    print("=" * 50)
    
    # Load existing environment variables
    load_dotenv()
    
    # Check current status
    print("\n📋 Current Environment Variables Status:")
    print(f"AZURE_OPENAI_API_KEY: {'✅ Set' if os.getenv('AZURE_OPENAI_API_KEY') else '❌ Missing'}")
    print(f"AZURE_OPENAI_ENDPOINT: {'✅ Set' if os.getenv('AZURE_OPENAI_ENDPOINT') else '❌ Missing'}")
    print(f"AZURE_OPENAI_DEPLOYMENT_NAME: {'✅ Set' if os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME') else '❌ Missing'}")
    print(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: {'✅ Set' if os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME') else '❌ Missing'}")
    print(f"AZURE_OPENAI_API_VERSION: {'✅ Set' if os.getenv('AZURE_OPENAI_API_VERSION') else '❌ Missing'}")
    
    # Check if embedding deployment is missing
    if not os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME'):
        print("\n❌ MISSING: AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
        print("\n🔧 To fix this, you need to:")
        print("1. Go to your Azure OpenAI resource")
        print("2. Navigate to 'Deployments'")
        print("3. Find your embedding model deployment (usually 'text-embedding-ada-002')")
        print("4. Copy the deployment name")
        print("\n📝 Then set the environment variable:")
        print("export AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME='your-embedding-deployment-name'")
        print("\n💡 Or add it to your .env file:")
        print("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment-name")
        
        # Try to suggest based on common names
        print("\n🤖 Common embedding deployment names:")
        print("- text-embedding-ada-002")
        print("- text-embedding-ada-002-v2")
        print("- text-embedding-3-small")
        print("- text-embedding-3-large")
        
    else:
        print("\n✅ All environment variables are set!")
        print("🚀 Your RAG system should work properly now.")
        print("\n💡 To test, restart your backend server and try uploading a resume.")

if __name__ == "__main__":
    main() 