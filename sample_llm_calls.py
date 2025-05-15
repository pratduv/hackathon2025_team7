
import openai
from openai import OpenAI
import anthropic
from langchain.llms import OpenAI as LangchainOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_openai_completion(prompt, model="gpt-3.5-turbo"):
    """Get a completion from OpenAI"""
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content

def get_openai_embedding(text):
    """Get an embedding from OpenAI"""
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def get_anthropic_completion(prompt, model="claude-3-haiku"):
    """Get a completion from Anthropic"""
    response = anthropic_client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def rag_search_and_answer(query, docs):
    """RAG implementation with search and answer"""
    # 1. Convert query to embedding
    query_embedding = get_openai_embedding(query)
    
    # 2. Search for relevant documents (simulated)
    context = "\n".join(docs[:3])  # Pretend we found 3 relevant docs
    
    # 3. Generate answer with context
    prompt = f"""
    Answer the following question based on the provided context:
    
    Context:
    {context}
    
    Question: {query}
    """
    
    # This will use a lot of tokens due to the context
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                 {"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def batch_process_documents(documents):
    """Process multiple documents with LLM"""
    results = []
    
    for doc in documents:
        # This is an expensive operation for many documents
        summary = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Summarize the following document:"},
                {"role": "user", "content": doc}
            ],
            temperature=0.2,
            max_tokens=300
        )
        results.append(summary.choices[0].message.content)
    
    return results
