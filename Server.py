from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
import openai
import os
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

import gptapi

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace "*" with specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/summarize_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Summarize the PDF
        summary = gptapi.summarize_pdf(temp_file_path,Save_to_txt=True)

        # Clean up temporary file
        os.remove(temp_file_path)

        return JSONResponse(content={"summary": summary}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/gen_ques_pdf/")
async def gen_ques_pdf(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Summarize the PDF
        summary = gptapi.gen_ques_from_pdf(temp_file_path,Save_to_txt=True)

        # Clean up temporary file
        os.remove(temp_file_path)

        return JSONResponse(content={"summary": summary}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.get("/")
def root():
    return {"message": "Welcome to the PDF Summarizer API!"}
