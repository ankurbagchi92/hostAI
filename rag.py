from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from transformers import AutoTokenizer, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
import re
import os
import database

db = {}
embeddings = None

def create_embeddings():
    global embeddings
    print("Initializing embeddings")

    # Define the path to the pre-trained model you want to use
    modelPath = "sentence-transformers/all-MiniLM-l6-v2"

    # Create a dictionary with model configuration options, specifying to use the CPU for computations
    model_kwargs = {'device':'cpu'}

    # Create a dictionary with encoding options, specifically setting 'normalize_embeddings' to False
    encode_kwargs = {'normalize_embeddings': False}

    # Initialize an instance of HuggingFaceEmbeddings with the specified parameters
    embeddings = HuggingFaceEmbeddings(
        model_name=modelPath,     # Provide the pre-trained model's path
        model_kwargs=model_kwargs, # Pass the model configuration options
        encode_kwargs=encode_kwargs # Pass the encoding options
    )

    print("Embeddings initialized")

async def init():

    global db
    global embeddings

    create_embeddings()

    # loader = TextLoader("./memory.txt")
    # docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    servers = await database.get_server_ids()

    for server_id in servers:
        # Apply the TextLoader function on the file
        server_log = database.get_logs(server_id)
        loader = TextLoader(server_log)
        docs = loader.load()
        data = text_splitter.split_documents(docs)
        db[server_id] = FAISS.from_documents(data, embeddings)
        print (f"Loaded db from: {server_id}")


    # for filename in os.listdir("./memory"):
    #     if filename.endswith(".txt"):
    #         file_path = os.path.join("./memory", filename)
    #         # Apply the TextLoader function on the file
    #         loader = TextLoader(file_path)
    #         docs = loader.load()
    #         data = text_splitter.split_documents(docs)
    #         db[os.path.splitext(filename)[0]] = FAISS.from_documents(data, embeddings)
    #         print (f"Loaded db from: {os.path.splitext(filename)}")


    # try:
    #     db = FAISS.load_local("faiss_index", embeddings)
    #     print("Loading local db")
    # except:
    #     print("No local store for db")
    #     db = FAISS.from_documents(data, embeddings)
    #     print ("Creating new db")

def add_to_db (content, server_id):

    global embeddings

    new = FAISS.from_texts([content], embeddings)

    if server_id in db:
        db[server_id].merge_from(new)
    else:
        db[server_id] = new

def lookup (content, server_id):

    global db

    try:
        searchDocs = db[server_id].similarity_search(content)

        result = ""

        for doc in searchDocs:
            result += "\n" + clean_doc(doc.page_content)

        return result
    except:
        return ""
    #if (searchDocs is not None):
    #    print(searchDocs[0].page_content)

def clean_doc(doc):
    # Split the string to separate the page content from the metadata
    content_part = doc.split(" metadata=")[0]

    # Remove the initial 'page_content="' part
    content_clean = content_part[len('page_content="'):]

    pattern = r'\[Channel: \d+\]'

    # Split by new lines and filter out lines containing 'Channel:'
    lines = content_clean.split('\n')

    cleaned_lines = [re.sub(pattern, '', line).strip() for line in lines]

    # Join the cleaned lines back into a single string
    cleaned_text = '\n'.join(cleaned_lines)

    return cleaned_text
