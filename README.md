# RAG-Based Multi-Agent Question Generation System

## Overview
This system uses Retrieval Augmented Generation (RAG) and a multi-agent architecture to generate high-quality Multiple Choice Questions (MCQs) from PDF documents.

## Architecture

### Components
1. **RAG Service** (`rag_service.py`)
   - PDF text extraction and processing
   - ChromaDB vector storage
   - Semantic search and retrieval
   - Table of Contents extraction

2. **Multi-Agent System** (`agent_system.py`)
   - **Agent 1 (Generator)**: Creates MCQ questions from retrieved content
   - **Agent 2 (Evaluator)**: Evaluates and scores generated questions
   - **Finalizer**: Filters and returns high-quality questions
   - Built with LangGraph for agent orchestration

3. **FastAPI Server** (`server.py`)
   - RESTful API endpoints
   - File upload handling
   - Request/response validation

### Technology Stack
- **LLM**: Google Gemini (gemini-1.5-flash)
- **Vector Database**: ChromaDB
- **Embeddings**: Google Generative AI Embeddings (embedding-001)
- **Framework**: FastAPI, LangChain, LangGraph
- **PDF Processing**: pypdf

## API Endpoints

### 1. POST /api/ingest
Upload and process a PDF file.

**Request:**
```bash
curl -X POST "http://localhost:8001/api/ingest" \
  -F "file=@path/to/document.pdf"
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully ingested document.pdf",
  "chunks_processed": 45,
  "table_of_contents": [
    "Page 1: Introduction to Algebra",
    "Page 2: Linear Equations",
    "Page 3: Quadratic Equations"
  ]
}
```

### 2. POST /api/generate/questions
Generate MCQ questions based on a text query.

**Request:**
```bash
curl -X POST "http://localhost:8001/api/generate/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "linear equations and solving methods",
    "num_retrieved_docs": 5
  }'
```

**Response:**
```json
{
  "query": "linear equations and solving methods",
  "num_questions": 5,
  "questions": [
    {
      "question": "What is the solution to the equation 2x + 5 = 15?",
      "options": {
        "A": "x = 5",
        "B": "x = 10",
        "C": "x = 7.5",
        "D": "x = 2.5"
      },
      "correct_answer": "A",
      "explanation": "Subtract 5 from both sides: 2x = 10, then divide by 2: x = 5",
      "quality_score": 8,
      "evaluator_feedback": "Clear question with good distractors",
      "approved": true
    }
  ]
}
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Google AI Studio API Key
- Docker (optional, for containerized deployment)

### Local Installation

1. **Clone and navigate to backend directory:**
```bash
cd /app/backend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
Create a `.env` file:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=rag_qa_system
CORS_ORIGINS=*
GOOGLE_API_KEY=your_google_api_key_here
CHROMATIB_PERSIST_DIRECTORY=./chroma_db
```

4. **Run the server:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8001
```

5. **Access the API:**
- API Documentation: http://localhost:8001/docs
- Health Check: http://localhost:8001/api/health

### Docker Deployment

1. **Build the Docker image:**
```bash
cd /app/backend
docker build -t rag-question-system .
```

2. **Run the container:**
```bash
docker run -p 8001:8001 \
  -e GOOGLE_API_KEY=your_api_key \
  -v $(pwd)/chroma_db:/app/chroma_db \
  rag-question-system
```

3. **Access the API:**
- API: http://localhost:8001/api/
- Docs: http://localhost:8001/docs

## Usage Example

### Complete Workflow

```bash
# 1. Ingest a PDF document
curl -X POST "http://localhost:8001/api/ingest" \
  -F "file=@A_Quick_Algebra_Review.pdf"

# 2. Generate questions about specific topics
curl -X POST "http://localhost:8001/api/generate/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quadratic equations and factoring",
    "num_retrieved_docs": 5
  }'
```

## Multi-Agent Workflow

The system follows this workflow:

1. **User submits query** → System retrieves relevant document chunks from vector DB
2. **Generator Agent** → Creates 5 MCQ questions based on retrieved content
3. **Evaluator Agent** → Reviews each question, assigns quality scores, provides feedback
4. **Finalizer** → Filters questions (keeps score >= 6), returns final set

## Features

✅ **PDF Processing**: Extracts text and generates table of contents
✅ **Vector Storage**: Efficient semantic search with ChromaDB
✅ **Multi-Agent System**: Separate generation and evaluation for quality
✅ **LLM Integration**: Google Gemini for question generation
✅ **Quality Control**: Automatic scoring and filtering
✅ **RESTful API**: Easy integration with FastAPI
✅ **Docker Support**: Containerized deployment ready

## Testing

Run the included test script:
```bash
python test_api.py
```

## Project Structure

```
backend/
├── server.py              # FastAPI application
├── rag_service.py         # RAG pipeline and vector storage
├── agent_system.py        # Multi-agent system with LangGraph
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .env                  # Environment variables
├── README.md             # This file
└── chroma_db/            # Vector database storage
```

## Technical Requirements Checklist

✅ Multi-agent system design with 2 agents
✅ LangChain/LangGraph integration
✅ Google Gemini LLM via API
✅ ChromaDB vector database
✅ FastAPI endpoints (/ingest, /generate/questions)
✅ Dockerfile for deployment
✅ Clean code organization
✅ Comprehensive documentation

## Notes

- The system uses Google's embedding-001 model for document embeddings
- Questions are generated using gemini-1.5-flash for speed and quality
- ChromaDB data persists in the `chroma_db` directory
- The evaluator agent ensures only high-quality questions (score >= 6) are returned

## Troubleshooting

**Issue**: "No relevant documents found"
- **Solution**: Make sure to ingest a PDF first using `/api/ingest`

**Issue**: Docker build fails
- **Solution**: Ensure Docker is installed and running

**Issue**: API key errors
- **Solution**: Verify GOOGLE_API_KEY is correctly set in .env file

## Contact

For questions or issues, please contact: technicaltest@alefeducation.com
