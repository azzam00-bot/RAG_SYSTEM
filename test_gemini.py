#!/usr/bin/env python3
"""Test Google Gemini API connectivity and model availability"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

# Test 1: Check API key
api_key = "AIzaSyCfOj8mhTVuUT2P6tvtu10KVzbC9OtpCNg"
print("Testing Google Gemini API...")
print(f"API Key (first 10 chars): {api_key[:10]}...")

# Test 2: List available models
print("\nListing available models...")
genai.configure(api_key=api_key)
try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")

# Test 3: Try different model names
model_names = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]

for model_name in model_names:
    print(f"\n\nTesting model: {model_name}")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7
        )
        response = llm.invoke("Say hello in one word")
        print(f"✅ {model_name} WORKS! Response: {response.content}")
        break
    except Exception as e:
        print(f"❌ {model_name} failed: {str(e)[:100]}")
