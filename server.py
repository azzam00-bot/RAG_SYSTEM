from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any
import tempfile
import shutil

# Import custom services
from rag_service import RAGService
from agent_system import MultiAgentQuestionSystem

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize RAG and Agent systems
rag_service = RAGService()
agent_system = MultiAgentQuestionSystem()

# Create the main app
app = FastAPI(title="RAG-Based Question Generation API")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class IngestResponse(BaseModel):
    status: str
    message: str
    chunks_processed: int
    table_of_contents: List[str]

class QuestionGenerationRequest(BaseModel):
    query: str
    num_retrieved_docs: int = 5

class QuestionResponse(BaseModel):
    query: str
    questions: List[Dict[str, Any]]
    num_questions: int

# API Endpoints
@api_router.get("/")
async def root():
    return {
        "message": "RAG-Based Multi-Agent Question Generation System",
        "version": "1.0",
        "endpoints": {
            "/api/ingest": "POST - Upload and ingest PDF file",
            "/api/generate/questions": "POST - Generate MCQ questions"
        }
    }

@api_router.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)):
    """
    Endpoint to upload and process a PDF file.
    Returns the Table of Contents for the uploaded document.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Ingest PDF
            result = rag_service.ingest_pdf(
                pdf_path=tmp_path,
                metadata={"filename": file.filename}
            )
            
            response = IngestResponse(
                status="success",
                message=f"Successfully ingested {file.filename}",
                chunks_processed=result['chunks_processed'],
                table_of_contents=result['table_of_contents']
            )
            
            logging.info(f"Successfully ingested PDF: {file.filename}")
            return response
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    except Exception as e:
        logging.error(f"Error ingesting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@api_router.post("/generate/questions", response_model=QuestionResponse)
async def generate_questions(request: QuestionGenerationRequest):
    """
    Endpoint to generate MCQ questions based on a text query.
    The system retrieves relevant documents and uses multi-agent workflow
    to generate, evaluate, and return high-quality questions.
    """
    try:
        # Retrieve relevant documents
        retrieved_docs = rag_service.retrieve_relevant_docs(
            query=request.query,
            k=request.num_retrieved_docs
        )
        
        if not retrieved_docs:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found. Please ingest a PDF first."
            )
        
        # Generate questions using multi-agent system
        questions = agent_system.generate_questions(
            query=request.query,
            retrieved_docs=retrieved_docs
        )
        
        response = QuestionResponse(
            query=request.query,
            questions=questions,
            num_questions=len(questions)
        )
        
        logging.info(f"Generated {len(questions)} questions for query: {request.query}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAG Question Generation System"}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
