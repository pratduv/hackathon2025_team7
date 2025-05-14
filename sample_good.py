#!/usr/bin/env python3
import os
import json
import openai
from anthropic import Anthropic

# Set API keys
openai.api_key = os.environ.get("OPENAI_API_KEY")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = Anthropic(api_key=anthropic_api_key)

def generate_with_gpt4(prompt):
    """Generate text using GPT-4."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_with_gpt35(prompt):
    """Generate text using GPT-3.5 Turbo."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_with_claude(prompt):
    """Generate text using Claude."""
    response = anthropic_client.completions.create(
        model="claude-3-opus",
        prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
        max_tokens_to_sample=1000,
        temperature=0.7
    )
    return response.completion

def generate_embeddings(text):
    """Generate embeddings using OpenAI's embedding model."""
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response['data'][0]['embedding']

def process_user_query(query):
    """Process a user query using the appropriate model based on complexity."""
    # Determine complexity
    if len(query.split()) > 50:
        print("Using GPT-4 for complex query")
        return generate_with_gpt4(query)
    else:
        print("Using GPT-3.5 for simple query")
        return generate_with_gpt35(query)

def analyze_sentiment(text):
    """Analyze sentiment of text using Claude."""
    prompt = f"Analyze the sentiment of the following text and classify it as positive, negative, or neutral: {text}"
    return generate_with_claude(prompt)

if __name__ == "__main__":
    # Example usage
    user_query = "Explain the concept of quantum computing in simple terms."
    response = process_user_query(user_query)
    print(response)
    
    # Generate embeddings for semantic search
    embeddings = generate_embeddings("Quantum computing uses quantum bits or qubits.")
    print(f"Generated embedding with {len(embeddings)} dimensions")
    
    # Analyze sentiment
    sentiment = analyze_sentiment("I love this product! It's amazing and works perfectly.")
    print(f"Sentiment analysis: {sentiment}")
