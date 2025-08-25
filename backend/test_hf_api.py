import requests
import os
from dotenv import load_dotenv
import pathlib

# Load environment
load_dotenv("../.env")

# Test Hugging Face API directly
api_key = os.getenv("HUGGINGFACE_API_KEY")
print(f"API Key: {api_key[:10]}...")

# Test with a simple model first
api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
headers = {"Authorization": f"Bearer {api_key}"}

# Simple test payload
payload = {
    "inputs": "What is demurrage in shipping?",
    "parameters": {"max_new_tokens": 100, "temperature": 0.7}
}

print("Testing Hugging Face API...")
response = requests.post(api_url, headers=headers, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code != 200:
    print("Error! Let's try a different model...")
    
    # Try a different model
    api_url = "https://api-inference.huggingface.co/models/gpt2"
    response2 = requests.post(api_url, headers=headers, json=payload)
    print(f"GPT-2 Status Code: {response2.status_code}")
    print(f"GPT-2 Response: {response2.text}")
