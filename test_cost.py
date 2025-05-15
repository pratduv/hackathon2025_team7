#!/usr/bin/env python3
import os
import json
import requests
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Use the existing sample file
SAMPLE_FILE = SCRIPT_DIR / "sample_good.py"

# URL for the MCP server
BASE_URL = "http://localhost:8000"

def test_cost_estimation():
    """Test the cost estimation endpoint"""
    url = f"{BASE_URL}/check-cost"
    
    # Prepare the file for upload
    files = {'file': open(SAMPLE_FILE, 'rb')}
    
    # Make the request
    print(f"Sending request to {url}...")
    response = requests.post(url, files=files)
    
    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        
        # Print the results
        print("\n=== COST ESTIMATION RESULTS ===")
        print(f"Filename: {result['filename']}")
        print(f"Total lines: {result['total_lines']}")
        print(f"Total LLM calls detected: {result['total_calls']}")
        print(f"Total estimated cost: ${result['total_estimated_cost']:.6f}")
        
        # Print details for each LLM call
        print("\n=== DETAILED LLM CALLS ===")
        for i, call in enumerate(result['llm_calls'], 1):
            print(f"\nCall #{i}:")
            print(f"  Lines: {call['start_line']}-{call['end_line']}")
            print(f"  Model: {call['model']}")
            print(f"  Type: {call['call_type']}")
            print(f"  Input tokens: {call['estimated_input_tokens']}")
            print(f"  Output tokens: {call['estimated_output_tokens']}")
            print(f"  Estimated cost: ${call['estimated_cost']:.6f}")
            print(f"  Description: {call['description']}")
        
        # Calculate total tokens
        total_input_tokens = sum(call['estimated_input_tokens'] for call in result['llm_calls'])
        total_output_tokens = sum(call['estimated_output_tokens'] for call in result['llm_calls'])
        print(f"\nTotal input tokens: {total_input_tokens}")
        print(f"Total output tokens: {total_output_tokens}")
        print(f"Total tokens: {total_input_tokens + total_output_tokens}")
        
        return True
    else:
        
        print(f"Error: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    print("Testing LLM cost estimation...")
    success = test_cost_estimation()
    print("\nTest completed successfully!" if success else "\nTest failed!")
