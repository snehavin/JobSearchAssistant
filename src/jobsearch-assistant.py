# Imports
import streamlit as st
import openai
import os
from chatbot-backend import qa
from langchain_openai import ChatOpenAI
from langchain.schema import Document

# Set API key for OpenAI
os.environ['OPENAI_API_KEY'] = OPENAI_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")  # Get API key from environment

st.title("Job Search Assistant")

st.write("Enter your job title and upload your resume to find matching jobs.")

# USER INPUT
# user inputs their desired job title and their resume file
job_title = st.text_input("Desired Job Title", "")
resume_file = st.file_uploader("Upload your resume (PDF or CSV)", type=["pdf", "csv"])

# FIND JOBS FUNCTION
if st.button("Find Jobs"):
    # error handling if user does not input required fields
    if not job_title or not resume_file:
        st.warning("Please enter a job title and upload your resume.")
    else:
        st.success(f"Searching for jobs matching: {job_title}")
        # Telling chatbot to return 3 jobs based on user's desired role and resume
        # Only return jobs from database -- fixing hallucination error 
        query = f"I am looking for {job_title} roles, give me 3 unique jobs to apply for based on {resume_file}. Only return jobs from the database. Explain why the role aligns with user's experience."
        response = qa.run(query)  #Using the imported chatbot object
        st.write(response) 

# CHAT FUNCTION
def generate_response(input_text):
    if not openai.api_key:
        st.warning("API Key is missing!", icon="⚠")
        return

    # Answer job search question based on user's desired title and resume
    query = f"{input_text}. Use {resume_file} and {job_title} to answer based on user's information."
    response = qa.run(query)
    st.info(response)

# Chat form
with st.form("chat_form"):
    text = st.text_area("Ask about skills, experience, or job recommendations:", "")
    submitted = st.form_submit_button("Submit")

    if submitted:
        generate_response(text) #Call the chat function