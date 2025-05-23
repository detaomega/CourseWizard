# Database Service

A semantic search and course recommendation system built with Qdrant vector database and sentence transformers.

## Overview

This module provides vector database services for course data management, featuring semantic search capabilities and intelligent scheduling algorithms. It serves as the backend database layer for course recommendation systems.

**Important:** Place your course data, in JSON format (see "Data Format" below), inside the `database/data/` directory. The system will automatically process all `.json` files found in this location during the data embedding and upload process.

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- 2GB+ RAM for vector operations

## Quick Start

1. **Start the vector database**
   ```bash
   docker compose up -d
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database with sample data**
   ```bash
   python scripts/embed_upload.py
   ```
   Verify the functionality by running the test suite:
   ```bash
   python test/test_query.py
   ```

4. **Start the API service**
   ```bash
   python api/api.py
   ```

## Services

- **Qdrant Vector DB**: `http://localhost:6333` (API), `http://localhost:6334` (Dashboard)
- **Course API**: `http://localhost:8000` (FastAPI service)

## API Endpoints

- `GET /search` - Semantic course search
- `GET /course/{code}` - Get specific course details by code
- `POST /schedule` - Generate conflict-free schedules
- `POST /recommend` - AI-powered course recommendations

## Data Format

The system expects course data in JSON format. Each JSON file placed in the `database/data/` directory should contain a list of course objects. The `embed_upload.py` script will automatically discover and process all `.json` files within this directory.

Each course object should have the following structure:

```json
{
  "name": "計算機圖形",
  "course_number": "CSIE5085",
  "code": "922 U3090",
  "semester": "113-2",
  "targets": [
    "資訊工程學系",
    "智慧醫療學分學程",
    "資訊網路與多媒體研究所",
    "資訊工程學研究所"
  ],
  "teacger": "歐陽明",
  "department": "資訊工程學研究所",
  "credit": 3,
  "time": "weekday 4, 234. ",
  "classroom": "資104",
  "comment": "智慧醫療學分學程所屬電資學院影像領域課程",
  "course_overview": "Computer graphics course overview...",
  "course_objective": "Course learning objectives..."
}
```

## Architecture

- **Vector Storage**: Qdrant (384-dim embeddings)
- **Embedding Model**: `paraphrase-multilingual-MiniLM-L12-v2`
- **API Framework**: FastAPI
- **Search Type**: Cosine similarity with hybrid filtering

## Database Management

**Reset database (clear all data):**
```bash
python scripts/reset_db.py
```

**Reset specific collection:**
```bash
python scripts/reset_db.py --collection NAME
```

**Reset all collections:**
```bash
python scripts/reset_db.py --all
```

**Re-initialize with fresh data:**
```bash
python scripts/reset_db.py && python scripts/embed_upload.py
```

## Testing

Run the query test suite to verify functionality:

```bash
python test/test_query.py
```

Run the API test suite to verify endpoints:

```bash
python test/test_api.py
```

Run the interactive query script:

```bash
python test/test_query_interact.py
```

## Project Structure

```
database/
├── api/                         # API service
│   └── api.py                   # FastAPI application
├── data/                        # Course data
│   └── *.json                   # Course data files (e.g., course.json, ntu_courses.json)
├── scripts/                     # Utility scripts
│   ├── embed_upload.py          # Vector embedding and upload
│   └── reset_db.py              # Database reset tool
└── test/                        # Testing suite
    ├── test_query.py            # Query functionality tests
    ├── test_api.py              # API endpoint tests
    └── test_query_interact.py   # Interactive query script
```

## Configuration

Modify `docker-compose.yml` to adjust Qdrant settings or `requirements.txt` for different model versions.

## Integration

This service exposes RESTful APIs for integration with frontend applications and crawling services. See API documentation at `http://localhost:8000/docs` when running. 