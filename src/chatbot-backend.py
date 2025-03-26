# Imports
import pandas as pd
import os
import numpy as np
import openai

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter, TextSplitter
from langchain import OpenAI, VectorDBQA
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.document_loaders import CSVLoader

import tiktoken

from langchain import PromptTemplate, LLMChain
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain import vectorstores
from langchain.vectorstores.base import VectorStore

from langchain import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory

# USER INPUT
#User will input their desired job title and their resume through the Streamlit UI

# Load API Keys
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

# CREATING VECTOR DATABASE
#CSV has Job Postings with Job Title, Company, Location, Salary, Job Description, Skills/Qualifications

# Loading csv
loader = CSVLoader(file_path="data/job-postings.csv")
docs = loader.load()

# Shard dataset
text_splitter = CharacterTextSplitter(chunk_size=5000, chunk_overlap=0)
texts = text_splitter.split_documents(docs)
print("Number of shards =", len(texts))

# Calculating number of tokens for dataset - to make sure we don't exceed context length
def tiktoken_tokens(documents,model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model) 

    tokens_length = [len(encoding.encode(documents[i].page_content)) for i in range(len(documents))]

    return tokens_length
chunks_length = tiktoken_tokens(texts,model="gpt-3.5-turbo")
print(f"Number of tokens - Average : {int(np.mean(chunks_length))}")
print(f"Number of tokens - 75% percentile : {int(np.quantile(chunks_length,0.75))}")

# Chat Model -- using OpenAI
gpt35 = ChatOpenAI(model_name='gpt-3.5-turbo')

# Directory where Chroma embeddings will be saved
persist_directory = "./chroma_db"

# Convert the document-shards into embeddings
embeddings = OpenAIEmbeddings()
vectordb = Chroma.from_documents(texts, embeddings, persist_directory=persist_directory)
retriever = vectordb.as_retriever()


# PROMPT ENGINEERING
custom_prompt = PromptTemplate(
    input_variables=["context", "question", "chat_history"],  # Input variables for the prompt
    template="""You are a helpful job search assistant.  Your goal is to help users find the most relevant job postings based 
    on their skills and experiences. 
    
    - Recommend job postings that closely match the user's experiences and job preference
    - If a user asks job search related questions, provide actionable guidance
    - If a question is unclear, ask follow-up questions

    Conversation history: {chat_history}
    Retrieved job postings: {context}

    User's question: {question}

    Provide a well-structured and relevant answer.
    """
)


# CONVERSATION RETRIEVAL -- keeping memory during the conversation
memory = ConversationSummaryBufferMemory(
    max_token_limit=1024,
    llm=gpt35,
    return_messages=True,
    memory_key="chat_history"
)


# INSTANTIATING THE CHATBOT OBJECT
qa = ConversationalRetrievalChain.from_llm(
    llm=gpt35,
    retriever=retriever,  # Using the vector database retriever
    memory=memory,  # Using the conversation memory
    combine_docs_chain_kwargs={"prompt": custom_prompt}  # Using the custom prompt
)