#!/usr/bin/env python3
"""Test script for RAG-based Question Generation API"""
import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8001/api"

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_root():
    """Test root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_ingest_pdf(pdf_path: str):
    """Test PDF ingestion endpoint"""
    print("\n=== Testing PDF Ingestion ===")
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/ingest", files=files)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Chunks Processed: {result['chunks_processed']}")
        print(f"\nTable of Contents ({len(result['table_of_contents'])} entries):")
        for i, toc_entry in enumerate(result['table_of_contents'][:10], 1):
            print(f"  {i}. {toc_entry}")
        if len(result['table_of_contents']) > 10:
            print(f"  ... and {len(result['table_of_contents']) - 10} more entries")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_generate_questions(query: str):
    """Test question generation endpoint"""
    print(f"\n=== Testing Question Generation ===")
    print(f"Query: {query}")
    
    payload = {
        "query": query,
        "num_retrieved_docs": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/generate/questions",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nGenerated {result['num_questions']} questions:\n")
        
        for i, q in enumerate(result['questions'], 1):
            print(f"\n--- Question {i} ---")
            print(f"Q: {q['question']}")
            print(f"\nOptions:")
            for key, value in q['options'].items():
                print(f"  {key}. {value}")
            print(f"\nCorrect Answer: {q['correct_answer']}")
            print(f"Explanation: {q['explanation']}")
            if 'quality_score' in q:
                print(f"Quality Score: {q['quality_score']}/10")
            if 'evaluator_feedback' in q:
                print(f"Evaluator Feedback: {q['evaluator_feedback']}")
        
        return True
    else:
        print(f"Error: {response.text}")
        return False

def save_sample_questions(query: str, output_file: str = "sample_questions.json"):
    """Generate and save sample questions to a file"""
    print(f"\n=== Saving Sample Questions to {output_file} ===")
    
    payload = {
        "query": query,
        "num_retrieved_docs": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/generate/questions",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        with open(output_file, 'w') as f:
            json.dump(response.json(), f, indent=2)
        print(f"Sample questions saved to {output_file}")
        return True
    else:
        print(f"Error generating questions: {response.text}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("RAG-Based Question Generation System - API Tests")
    print("="*60)
    
    # Test 1: Health check
    if not test_health_check():
        print("❌ Health check failed")
        return
    print("✅ Health check passed")
    
    # Test 2: Root endpoint
    if not test_root():
        print("❌ Root endpoint failed")
        return
    print("✅ Root endpoint passed")
    
    # Test 3: Ingest PDF
    # Update this path to your PDF file
    pdf_path = "A_Quick_Algebra_Review.pdf"
    if not test_ingest_pdf(pdf_path):
        print("❌ PDF ingestion failed")
        print("\nNote: Make sure the PDF file exists and the path is correct.")
        return
    print("✅ PDF ingestion passed")
    
    # Test 4: Generate questions - Test different queries
    test_queries = [
        "linear equations and solving methods",
        "quadratic equations",
        "algebra fundamentals"
    ]
    
    for query in test_queries:
        if not test_generate_questions(query):
            print(f"❌ Question generation failed for query: {query}")
        else:
            print(f"✅ Question generation passed for query: {query}")
    
    # Save sample questions
    save_sample_questions(test_queries[0])
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
