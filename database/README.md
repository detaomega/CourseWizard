# Database Service

Semantic search and course recommendation system using Qdrant and sentence transformers.

## Overview

Provides vector database services for course data: semantic search and intelligent scheduling. Assumes course data (JSON) is in `database/data/`.

## Prerequisites

- Docker
- Python 3.8+

## Quick Start

1.  **Start Qdrant:**
    ```bash
    # Ensure Docker is running
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    ```
    (Or use `docker compose up -d` if you have a `docker-compose.yml` for Qdrant in the `database` directory or project root.)

2.  **Install Dependencies:**
    (From project root, where `requirements.txt` is)
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize Database:**
    (From `database` directory)
    ```bash
    python scripts/embed_upload.py
    ```
    This processes JSONs in `database/data/` using `BAAI/bge-m3` model.

4.  **Start API Service:**
    (From `database` directory)
    ```bash
    python api/api.py
    ```
    Or for development (hot-reloading):
    ```bash
    uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
    ```

## Services

- **Qdrant API:** `http://localhost:6333`
- **Qdrant Dashboard:** `http://localhost:6334`
- **Course API Docs:** `http://localhost:8000/docs` (when API service is running)

## Key API Endpoints

(See `http://localhost:8000/docs` for full details)
- `GET /search`: Semantic course search.
- `GET /course/{course_code}`: Get specific course details.
- `POST /schedule`: Generate conflict-free schedule.
- `POST /recommend`: AI-powered course recommendations.
- `GET /health`: Health check.

## Data Format

- Course data as JSON files in `database/data/` (and subdirectories).
- Each file: a list of course objects or a single course object.
- **Crucial field**: `"id": "unique_course_uuid"` for each course.
- `scripts/embed_upload.py` handles processing.

## Architecture

- **Vector DB:** Qdrant
- **Embedding Model:** `BAAI/bge-m3` (1024-dim)
- **API:** FastAPI

## Database Management

(Run from `database` directory)

- **Reset `ntu_courses` collection:**
  ```bash
  python scripts/reset_db.py
  ```
- **Reset and Re-upload:**
  ```bash
  python scripts/reset_db.py && python scripts/embed_upload.py
  ```

## Testing

(Run from `database` directory)

- **Core DB tests:** `python test/test_query.py`
- **API tests:** `python test/test_api.py`
- **Interactive query:** `python test/test_query_interact.py`

## Project Structure

```
database/
├── api/api.py             # FastAPI app
├── data/                  # Course JSON data
├── logs/                  # Log files
├── scripts/               # Utility scripts (embed_upload.py, reset_db.py)
└── test/                  # Test scripts

# Project root files
requirements.txt           # Dependencies
README.md                  # This file (if this is a submodule)
```

## Configuration

- Model (`BAAI/bge-m3`) & Qdrant settings: in `scripts/embed_upload.py`, `api/api.py`.
- Data path: `database/data/` (used by `scripts/embed_upload.py`).

## Integration

This service exposes RESTful APIs for integration with frontend applications or other services (e.g., course crawlers feeding data into the `database/data/` directory). The API documentation is available at `http://localhost:8000/docs` when the API service is running. 