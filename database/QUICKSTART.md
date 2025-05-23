# Quick Start Guide

## Setup

1. **Start Qdrant database**
   ```bash
   docker compose up -d
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Load sample data**
   ```bash
   python scripts/embed_upload.py
   ```

4. **Start API service**
   ```bash
   python api/api.py
   ```

## Verify Installation

**Test query functionality:**
```bash
python test/test_query.py
```

**Test API endpoints:**
```bash
python test/test_api.py
```

**Run interactive query tool:**
```bash
python test/test_query_interact.py
```

## Database Management

```bash
# Reset database
python scripts/reset_db.py

# Reset and reload
python scripts/reset_db.py && python scripts/embed_upload.py
```

## Services

- API: `http://localhost:8000/docs`
- Qdrant: `http://localhost:6334` 