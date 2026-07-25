import os
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
load_dotenv()
import json
API_KEY=os.getenv("API_KEY")

class ChatBot():

    def __init__(self):
        
        self.embedding= HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")        
        with open("docs.json", "r") as f:
            self.docs = json.load(f)
        f.close()         
        self.vectorstore = FAISS.from_texts(
            texts=self.docs,
            embedding=self.embedding
        )    
        self.llm=ChatGroq(model="llama-3.3-70b-versatile", temperature=0,api_key=API_KEY)
    
    def chat(self, query):

        self.user_message=query
        docs=self.vectorstore.similarity_search(query,k=7)
        context= " ".join([doc.page_content for doc in docs])      
        prompt=f'''
'''
        
        response=self.llm.invoke(prompt)
        return response.content.strip()


