from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from utils.parser import parse_file
from utils.embedding import store_embedding
from utils.emailer import (
    send_embed_script_email,
    generate_script_tag,
    send_admin_notification,
)
from utils.tracker import log_upload
from utils.otp import generate_otp, store_otp, verify_otp, is_verified, send_otp_email
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import os
from dotenv import load_dotenv
from config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    TOP_K_CHUNKS,
)
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


class OTPRequest(BaseModel):
    email: str
    otp: str


@app.options("/chat")
async def options_chat():
    logger.info("Handling OPTIONS request for /chat")
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization, X-Requested-With",
        },
    )


@app.get("/")
def read_root():
    return {"message": "Chatbot API is live 🎉"}


# Add this function to check if user has existing bot
async def check_existing_bot(email: str) -> Optional[str]:
    """Check if user already has a bot and return bot_id if exists"""
    embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
    vectorstore = QdrantVectorStore.from_existing_collection(
        collection_name=COLLECTION_NAME,
        embedding=embedding,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    # Search for points with metadata.email = email
    points = vectorstore.client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="metadata.email", match=MatchValue(value=email))]
        ),
        limit=1,
    )[0]

    if points:
        return points[0].payload.get("metadata", {}).get("bot_id")
    return None


# Add this endpoint to check for existing bot
@app.post("/check-existing-bot")
async def check_bot_exists(email: str = Form(...)):
    bot_id = await check_existing_bot(email)
    return {"has_existing_bot": bot_id is not None, "bot_id": bot_id}


# Add endpoint to send OTP
@app.post("/send-otp")
async def send_otp_endpoint(email: str = Form(...)):
    """Send OTP to email for verification"""
    try:
        # Generate and store OTP
        otp = generate_otp()
        store_otp(email, otp)

        # Send OTP email
        send_otp_email(email, otp)

        logger.info(f"OTP sent to email: {email}")
        return JSONResponse(
            content={"message": "OTP sent successfully", "email": email}
        )
    except Exception as e:
        logger.error(f"Failed to send OTP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")


# Add endpoint to verify OTP
@app.post("/verify-otp")
async def verify_otp_endpoint(request: OTPRequest):
    """Verify OTP"""
    if verify_otp(request.email, request.otp):
        logger.info(f"OTP verified for email: {request.email}")
        return JSONResponse(
            content={"message": "OTP verified successfully", "email": request.email}
        )
    else:
        logger.warning(f"Invalid OTP for email: {request.email}")
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")


@app.post("/upload")
async def upload_doc(
    file: UploadFile,
    email: str = Form(...),
    name: str = Form(...),
    replace: bool = Form(False),  # Add replace parameter
):
    logger.info(
        f"Processing upload for email: {email}, name: {name}, replace: {replace}"
    )

    # Check if email is verified
    if not is_verified(email):
        logger.warning(f"Email not verified: {email}")
        return JSONResponse(
            status_code=403,
            content={
                "error": "email_not_verified",
                "message": "Please verify your email address first",
            },
        )

    # Check if user has existing bot and replace is not True
    existing_bot_id = await check_existing_bot(email)
    if existing_bot_id and not replace:
        return JSONResponse(
            status_code=409,
            content={
                "error": "existing_bot",
                "message": "You already have a Docative chatbot",
                "bot_id": existing_bot_id,
            },
        )

    # If replace is True and existing bot exists, delete it
    if existing_bot_id and replace:
        embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
        vectorstore = QdrantVectorStore.from_existing_collection(
            collection_name=COLLECTION_NAME,
            embedding=embedding,
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

        # Delete all points with this bot_id using proper Qdrant filter syntax
        vectorstore.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.bot_id", match=MatchValue(value=existing_bot_id)
                    )
                ]
            ),
        )
        logger.info(f"Deleted existing bot with bot_id: {existing_bot_id}")

    text = await parse_file(file)
    if not text:
        raise HTTPException(
            status_code=400, detail="Unsupported file type or empty content"
        )

    bot_id = await store_embedding(text, email, name)
    log_upload(email, bot_id, file.filename, name)

    # Generate script tag using emailer.py function
    script_tag = generate_script_tag(bot_id, name)

    try:
        send_embed_script_email(email, bot_id, name)
        # Send admin notification
        send_admin_notification(email, name, bot_id, file.filename)
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return JSONResponse(
        content={
            "email": email,
            "bot_id": bot_id,
            "name": name,
            "script_tag": script_tag,
            "message": "Embedding stored successfully and email sent",
        }
    )


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
            api_key=QDRANT_API_KEY,
        )

        # Verify bot_id exists in collection
        points = vectorstore.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.bot_id", match=MatchValue(value=request.bot_id)
                    )
                ]
            ),
            limit=1,
        )[0]
        if not points:
            logger.warning(f"No content found for bot_id: {request.bot_id}")
            raise HTTPException(
                status_code=404, detail=f"No content found for bot_id: {request.bot_id}"
            )

        # Retrieve relevant context
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "filter": {
                    "must": [
                        {"key": "metadata.bot_id", "match": {"value": request.bot_id}}
                    ]
                },
                "k": TOP_K_CHUNKS,
            }
        )
        context_docs = retriever.invoke(request.question)
        context = "\n".join([doc.page_content for doc in context_docs])

        # Format chat history for prompt
        history_text = ""
        if request.history:
            history_text = (
                "\n".join(
                    [
                        f"{msg['sender']}: {msg['text']}"
                        for msg in request.history[-10:]
                    ]  # Limit to last 10 messages
                )
                + "\n"
            )

        # Define prompt template
        prompt_template = PromptTemplate(
            input_variables=["context", "history", "question"],
            template="""You are Docative, an AI chatbot created from the user's content, representing him, his documents, website, or portfolio. Use the provided context to answer questions concisely and accurately, reflecting the tone and intent of the content (e.g., professional for resumes, engaging for websites). Be creative with details as long as they align with the context. If the context lacks relevant information, use conversation history (if available) to inform follow-ups or politely say, "I don't have enough info from your content to answer that, but feel free to ask something related!" For questions unrelated to the context, respond positively with general knowledge or encouragement, keeping it relevant to person's goals.
Context: {context}
Conversation History:
{history}
Current Question: {question}
Answer:""",
        )

        # Set up LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )

        # Create chain using RunnableSequence (modern approach)
        chain = prompt_template | llm

        # Run the query with history
        inputs = {
            "context": context,
            "history": history_text,
            "question": request.question,
        }
        logger.info(f"Invoking LLM chain")
        answer = chain.invoke(inputs).content.strip()

        if not answer:
            logger.warning(f"No relevant content found for bot_id: {request.bot_id}")
            raise HTTPException(
                status_code=404, detail="No relevant content found for this bot_id"
            )

        logger.info(f"Chat response generated for bot_id: {request.bot_id}")
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing chat request: {str(e)}"
        )
