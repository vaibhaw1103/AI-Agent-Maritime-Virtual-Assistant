import os
from dotenv import load_dotenv
import pathlib

# Load environment
env_paths = [".env", "../.env", "../../.env"]
for env_path in env_paths:
    if pathlib.Path(env_path).exists():
        load_dotenv(env_path)
        print(f"Loaded: {env_path}")
        break

# Check what's loaded
print("Environment Variables:")
print(f"HUGGINGFACE_API_KEY: {os.getenv('HUGGINGFACE_API_KEY')}")
print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')}")  
print(f"GROQ_API_KEY: {os.getenv('GROQ_API_KEY')}")
print(f"OPENWEATHER_API_KEY: {os.getenv('OPENWEATHER_API_KEY')}")
