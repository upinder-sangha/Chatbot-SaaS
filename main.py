from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from utils.parser import parse_file
from utils.embedding import store_embedding
from utils.emailer import send_embed_script_email
from utils.tracker import log_upload

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Chatbot API is live 🎉"}

@app.post("/upload")
async def upload_doc(file: UploadFile, email: str = Form(...)):
    text = await parse_file(file)
    if not text:
        raise HTTPException(status_code=400, detail="Unsupported file type or empty content")

    bot_id = await store_embedding(text, email)
    log_upload(email, bot_id, file.filename)


    # Send the script tag to user's email
    try:
        send_embed_script_email(email, bot_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return JSONResponse(content={
        "email": email,
        "bot_id": bot_id,
        "message": "Embedding stored successfully and email sent"
    })
