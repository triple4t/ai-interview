import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Environment Variables Check:")
print(f"AZURE_OPENAI_API_KEY: {'✅ Set' if os.getenv('AZURE_OPENAI_API_KEY') else '❌ Missing'}")
print(f"AZURE_OPENAI_ENDPOINT: {'✅ Set' if os.getenv('AZURE_OPENAI_ENDPOINT') else '❌ Missing'}")
print(f"AZURE_OPENAI_DEPLOYMENT_NAME: {'✅ Set' if os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME') else '❌ Missing'}")
print(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: {'✅ Set' if os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME') else '❌ Missing'}")
print(f"AZURE_OPENAI_API_VERSION: {'✅ Set' if os.getenv('AZURE_OPENAI_API_VERSION') else '❌ Missing'}")

# Show actual values (masked for security)
api_key = os.getenv('AZURE_OPENAI_API_KEY')
if api_key:
    print(f"API_KEY (first 10 chars): {api_key[:10]}...")
else:
    print("API_KEY: None")

endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
if endpoint:
    print(f"ENDPOINT: {endpoint}")
else:
    print("ENDPOINT: None") 