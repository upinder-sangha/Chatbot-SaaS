from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.parser import parse_file
from utils.embedding import store_embedding
from utils.emailer import send_embed_script_email
from utils.tracker import log_upload
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from config import COLLECTION_NAME, EMBEDDING_MODEL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, TOP_K_CHUNKS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

app = FastAPI()

# CORS middleware for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization", "X-Requested-With"],
    expose_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    bot_id: str
    history: list[dict] = []  # Optional history

@app.options("/chat")
async def options_chat():
    logger.info("Handling OPTIONS request for /chat")
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization, X-Requested-With"
        }
    )

@app.get("/")
def read_root():
    return {"message": "Chatbot API is live 🎉"}

@app.post("/upload")
async def upload_doc(file: UploadFile, email: str = Form(...), name: str = Form(...)):
    logger.info(f"Processing upload for email: {email}, name: {name}")
    text = await parse_file(file)
    if not text:
        raise HTTPException(status_code=400, detail="Unsupported file type or empty content")

    bot_id = await store_embedding(text, email, name)
    log_upload(email, bot_id, file.filename, name)

    try:
        send_embed_script_email(email, bot_id, name)
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return JSONResponse(content={
        "email": email,
        "bot_id": bot_id,
        "name": name,
        "message": "Embedding stored successfully and email sent"
    })

@app.post("/chat")
async def chat(request: ChatRequest):
    logger.info(f"Processing chat request for bot_id: {request.bot_id}")
    try:
        # Initialize LangChain components
        embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
        vectorstore = QdrantVectorStore.from_existing_collection(
            collection_name=COLLECTION_NAME,
            embedding=embedding,
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )
        
        # Verify bot_id exists in collection
        points = vectorstore.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter={"must": [{"key": "metadata.bot_id", "match": {"value": request.bot_id}}]},
            limit=1
        )[0]
        if not points:
            logger.warning(f"No content found for bot_id: {request.bot_id}")
            raise HTTPException(status_code=404, detail=f"No content found for bot_id: {request.bot_id}")

        # Retrieve relevant context
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "filter": {"must": [{"key": "metadata.bot_id", "match": {"value": request.bot_id}}]},
                "k": TOP_K_CHUNKS
            }
        )
        context_docs = retriever.invoke(request.question)
        context = "\n".join([doc.page_content for doc in context_docs])

        # Format chat history for prompt
        history_text = ""
        if request.history:
            history_text = "\n".join(
                [f"{msg['sender']}: {msg['text']}" for msg in request.history[-10:]]  # Limit to last 10 messages
            ) + "\n"

        # Define prompt template
        prompt_template = PromptTemplate(
            input_variables=["context", "history", "question"],
            template="""Pretend to be the optimistic owner of the content you are answering questions about. Use the following context to answer the user's question concisely and accurately. You can be a bit creative about the details but make sure they align with the context. If the context doesn't contain relevant information, use the conversation history (if provided) to provide context for follow-up questions or say so politely. For questions that can be answered without the context, answer them as positively as possible.

Context: {context}

Conversation History:
{history}

Current Question: {question}

Answer:"""
        )

        # Set up LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )

        # Create LLMChain
        chain = LLMChain(llm=llm, prompt=prompt_template)

        # Run the query with history
        inputs = {
            "context": context,
            "history": history_text,
            "question": request.question
        }
        logger.info(f"Invoking chain with inputs: {inputs}")
        answer = chain.invoke(inputs)["text"].strip()

        if not answer:
            logger.warning(f"No relevant content found for bot_id: {request.bot_id}")
            raise HTTPException(status_code=404, detail="No relevant content found for this bot_id")

        logger.info(f"Chat response generated for bot_id: {request.bot_id}")
        return {"answer": answer}

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")