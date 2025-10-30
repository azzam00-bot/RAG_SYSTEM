# RAG-Based Multi-Agent Question Generation System - Setup & Running Instructions

## Quick Start Guide

### System Requirements
- Python 3.11+
- 4GB RAM minimum
- Docker (optional, for containerized deployment)

### Installation & Running (Local)

**Step 1: Navigate to backend directory**
```bash
cd /app/backend
```

**Step 2: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3: Set up environment variables**
The `.env` file is already configured with:
```env
GOOGLE_API_KEY=AIzaSyCfOj8mhTVuUT2P6tvtu10KVzbC9OtpCNg
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

**Step 4: Run the server**
```bash
uvicorn server:app --host 0.0.0.0 --port 8001
```

The server will start on: `http://localhost:8001`

- API Documentation: `http://localhost:8001/docs`
- Health Check: `http://localhost:8001/api/health`

---

## Usage Examples

### 1. Ingest a PDF Document

```bash
curl -X POST "http://localhost:8001/api/ingest" \
  -F "file=@A_Quick_Algebra_Review.pdf"
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully ingested A_Quick_Algebra_Review.pdf",
  "chunks_processed": 47,
  "table_of_contents": [
    "Page 1: 1.  Simplifying Expressions",
    "Page 1: 2.  Solving Equations",
    "Page 1: 3.  Problem Solving",
    ...
  ]
}
```

### 2. Generate MCQ Questions

```bash
curl -X POST "http://localhost:8001/api/generate/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quadratic equations",
    "num_retrieved_docs": 3
  }'
```

**Response:**
```json
{
  "query": "quadratic equations",
  "num_questions": 5,
  "questions": [
    {
      "question": "The quadratic formula is specifically designed to solve equations of what general form?",
      "options": {
        "A": "ax + b = 0",
        "B": "ax^2 + bx + c = 0",
        "C": "ax^3 + bx^2 + cx + d = 0",
        "D": "x^2 = c"
      },
      "correct_answer": "B",
      "explanation": "Document 3 explicitly states: The quadratic formula solves equations of the form: ax^2 + bx + c = 0.",
      "quality_score": 10,
      "evaluator_feedback": "Excellent question, tests a fundamental definition directly from the source.",
      "approved": true
    },
    ...
  ]
}
```

---

## Docker Deployment

### Build Docker Image
```bash
cd /app/backend
docker build -t rag-question-system .
```

### Run Container
```bash
docker run -p 8001:8001 \
  -e GOOGLE_API_KEY=your_api_key_here \
  -v $(pwd)/chroma_db:/app/chroma_db \
  rag-question-system
```

### Access the Application
- API: `http://localhost:8001/api/`
- Swagger Docs: `http://localhost:8001/docs`

---

## Sample Generated Questions

A file named `sample_questions.json` contains 5 example questions generated from the "A Quick Algebra Review" PDF.

To view:
```bash
cat /app/backend/sample_questions.json
```

---

## Architecture Overview

### Multi-Agent Workflow
1. **User Query** → System retrieves relevant document chunks from ChromaDB
2. **Generator Agent** → Creates 5 MCQ questions from retrieved content
3. **Evaluator Agent** → Reviews questions, assigns quality scores (1-10), provides feedback
4. **Finalizer** → Filters questions (keeps score ≥ 6), returns final set

### Technology Stack
- **Backend**: FastAPI
- **LLM**: Google Gemini 2.5 Flash
- **Vector DB**: ChromaDB with HuggingFace embeddings (all-MiniLM-L6-v2)
- **Agent Framework**: LangGraph
- **PDF Processing**: pypdf

---

## Project Structure

```
backend/
├── server.py              # FastAPI application with endpoints
├── rag_service.py         # RAG pipeline and vector storage
├── agent_system.py        # Multi-agent system with LangGraph
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .env                  # Environment variables
├── README.md             # Documentation
├── test_api.py           # API testing script
├── sample_questions.json # Example generated questions
├── A_Quick_Algebra_Review.pdf # Test PDF file
└── chroma_db/            # Vector database storage directory
```

---

## API Endpoints

### GET /api/
Root endpoint with API information

### GET /api/health
Health check endpoint

### POST /api/ingest
Upload and process PDF files

**Request:** Form-data with `file` field
**Response:** JSON with status, chunks processed, and table of contents

### POST /api/generate/questions
Generate MCQ questions based on query

**Request Body:**
```json
{
  "query": "topic to generate questions about",
  "num_retrieved_docs": 5
}
```

**Response:** JSON with generated questions including evaluations

---

## Key Features

✅ Multi-agent system (Generator + Evaluator)  
✅ RAG pipeline with semantic search  
✅ Local embeddings (no API limits)  
✅ Automatic quality control (scoring & filtering)  
✅ Table of contents extraction from PDFs  
✅ Comprehensive error handling  
✅ Docker support  
✅ Interactive API documentation (Swagger UI)  

---

## Troubleshooting

**Issue**: Vector store initialization fails  
**Solution**: Ensure `chroma_db` directory exists and has write permissions

**Issue**: Question generation returns empty array  
**Solution**: Make sure to ingest a PDF first using `/api/ingest`

**Issue**: API timeout  
**Solution**: LLM calls can take 30-40 seconds. Increase request timeout if needed

---

## Testing

Run the test script:
```bash
python test_api.py
```

This will:
1. Test health check endpoint
2. Ingest the sample PDF
3. Generate questions for multiple queries
4. Save sample questions to file

---

## Technical Requirements Compliance

✅ Multi-agent system with 2 agents (Generator + Evaluator)  
✅ LangGraph for agent orchestration  
✅ Google Gemini LLM integration  
✅ ChromaDB vector database (open-source)  
✅ FastAPI endpoints (`/ingest`, `/generate/questions`)  
✅ Dockerfile for deployment  
✅ Clean code organization (separate modules)  
✅ Comprehensive documentation  
✅ Sample questions provided  

---

## Contact

For questions regarding this technical test:  
Email: technicaltest@alefeducation.com
