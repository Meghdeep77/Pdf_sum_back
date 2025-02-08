from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
import openai
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from starlette.responses import JSONResponse

from database import Base, engine, SessionLocal
from models import User,Subscription
import utils
import gptapi
from authentication import router as auth_router
from payment import router as pay_router

# Load environment variables

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(pay_router, prefix="/pay", tags=["Payment"])


Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schema for request validation
class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: constr(min_length=3, max_length=50)
    password: constr(min_length=8)


@app.post("/summarize_pdf/")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Form(...),db: Session = Depends(get_db)):
    try:

        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Save the uploaded file temporarily
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Summarize the PDF
        summary, tokens = gptapi.summarize_pdf(temp_file_path, Save_to_txt=False)


        # Update tokens in subscription table
        try:
            utils.update_tokens(user_id_int, tokens,db)
            utils.update_uses(user_id_int, tokens,db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update tokens: {str(e)}")

        # Clean up temporary file
        os.remove(temp_file_path)

        return JSONResponse(content={"summary": summary}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/summarize_ppt/")
async def upload_ppt(file: UploadFile = File(...), user_id: str = Form(...), db: Session = Depends(get_db)):
    try:
        # Validate and convert user ID
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Save the uploaded file temporarily
        with NamedTemporaryFile(delete=False, suffix=".pptx") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Summarize the PowerPoint
        summary, tokens = gptapi.summarize_ppt(temp_file_path, Save_to_txt=False)

        # Update tokens in subscription table
        try:
            utils.update_tokens(user_id_int, tokens, db)
            utils.update_uses(user_id_int, tokens, db)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update tokens: {str(e)}")

        # Clean up temporary file
        os.remove(temp_file_path)

        return JSONResponse(content={"summary": summary}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")




@app.post("/gen_ques_pdf")
async def gen_ques_pdf(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    try:

        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Save the uploaded file temporarily
        temp_file_path = None
        try:
            with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(await file.read())
                temp_file_path = temp_file.name

            # Generate questions from the PDF
            try:
                summary, tokens = gptapi.gen_ques_from_pdf(temp_file_path)

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

            # Update tokens in subscription table
            try:
                utils.update_tokens(user_id_int, tokens, db)
                utils.update_uses(user_id_int, tokens, db)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update tokens: {str(e)}")

            # Return the generated questions
            return JSONResponse(content={"questions": summary, "tokens_used": tokens}, status_code=200)

        finally:
            # Clean up the temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except HTTPException as http_exc:
        raise http_exc  # Reraise HTTP exceptions to keep status codes intact
    except Exception as e:
        # Catch all other exceptions
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/gen_ques_ppt/")
async def gen_ques_ppt(file: UploadFile = File(...), user_id: str = Form(...), db: Session = Depends(get_db)):
    try:
        # Validate and convert user ID
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Save the uploaded file temporarily
        with NamedTemporaryFile(delete=False, suffix=".pptx") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Generate questions from the PowerPoint
        summary, tokens = gptapi.gen_ques_from_ppt(temp_file_path, Save_to_txt=False)

        # Update tokens in subscription table
        try:

            utils.update_tokens(user_id_int, tokens, db)
            utils.update_uses(user_id_int, tokens, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update tokens: {str(e)}")

        # Clean up temporary file
        os.remove(temp_file_path)

        return JSONResponse(content={"questions": summary}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/")
def root():
    return {"message": "Welcome to the PDF Summarizer API! The real Deal !"}

@app.post("/register", status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if username or email already exists
        if db.query(User).filter(User.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already exists")
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already exists")

        # Hash the password
        hashed_password = utils.hash_password(user.password)

        # Create a new user
        new_user = User(username=user.username, email=user.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create an entry in the subscriptions table
        new_subscription = Subscription(
            id=new_user.id,  # Associate with the newly created user
            subscription=False,  # Default subscription status
            tokens_used=0,
            free_trial_used =False,
            uses=0# Initialize tokens used to 0
        )
        db.add(new_subscription)
        db.commit()

        return {"message": "User registered successfully", "user_id": new_user.id}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
