#!/usr/bin/env python3
"""
Course Vector Database Upload Script
Loads course data, creates embeddings, and uploads to Qdrant vector database
"""

import json
import re
import os
import logging
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# --- Logger Setup ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "embed_upload.log") # Updated LOG_FILE path

# Create logs directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        # This might happen in a race condition if another process creates it.
        # Or if there are permission issues.
        print(f"Error creating log directory {LOG_DIR}: {e}")
        # Fallback to current directory if log dir creation fails
        LOG_FILE = "embed_upload.log" 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(LOG_FILE, mode='w') # Overwrite log file each run
file_handler.setLevel(logging.INFO)

# Console handler (optional, for also printing to console)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
# logger.addHandler(console_handler)
# --- End Logger Setup ---


class CourseEmbedder:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize course embedder with Qdrant client"""
        logger.info("Initializing course embedder...")
        print("Initializing course embedder...")
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port, check_compatibility=False)
        self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.collection_name = "ntu_courses"
        logger.info("Loading multilingual semantic model...")
        print("Loading multilingual semantic model...")
        logger.info("Initialization complete.")
        print("Initialization complete.")
    
    def parse_time_slots(self, time_str: str) -> List[Dict]:
        """Parse time string into structured time slots"""
        if not time_str or time_str.strip() == "":
            return []
        
        time_slots = []
        
        # Handle patterns like "weekday 4, 234. " or "weekday 2, 789. "
        weekday_pattern = r'weekday (\d+), ([0-9X]+)\.?'
        matches = re.findall(weekday_pattern, time_str)
        
        for day, periods in matches:
            # Convert day number to Chinese weekday
            day_map = {
                '1': '星期一', '2': '星期二', '3': '星期三', 
                '4': '星期四', '5': '星期五', '6': '星期六', '0': '星期日'
            }
            
            weekday = day_map.get(day, f'星期{day}')
            
            # Parse periods (like "234" means periods 2,3,4)
            for char in periods:
                if char.isdigit():
                    period_num = int(char)
                    time_slots.append({
                        "weekday": weekday,
                        "period": period_num,
                        "time": f"{weekday}第{period_num}節"
                    })
        
        return time_slots
    
    def create_embedding_text(self, course: Dict) -> str:
        """Create text for embedding from course data"""
        texts = []
        
        # Course name (most important)
        if course.get('name'):
            texts.append(course['name'])
        
        # Course overview and objectives
        if course.get('course_overview'):
            texts.append(course['course_overview'])
        
        if course.get('course_objective'):
            texts.append(course['course_objective'])
        
        # Teacher name
        if course.get('teacger'):  # Note: keeping original field name
            texts.append(f"授課教師: {course['teacger']}")
        
        # Department
        if course.get('department'):
            texts.append(f"開課單位: {course['department']}")
        
        # Course number for technical courses
        if course.get('course_number'):
            texts.append(f"課號: {course['course_number']}")
        
        # Comments (often contain important info)
        if course.get('comment'):
            texts.append(course['comment'])
        
        return " ".join(texts)
    
    def process_course(self, course: Dict, index: int) -> PointStruct:
        """Process a single course into vector database format"""
        
        # Create embedding text
        embedding_text = self.create_embedding_text(course)
        
        # Generate embedding
        embedding = self.model.encode(embedding_text).tolist()
        
        # Parse time slots
        time_slots = self.parse_time_slots(course.get('time', ''))
        
        # Create payload with new structure
        payload = {
            # Basic info
            "name": course.get('name', ''),
            "course_number": course.get('course_number', ''),
            "code": course.get('code', ''),
            "semester": course.get('semester', ''),
            "department": course.get('department', ''),
            "teacher": course.get('teacger', ''),  # Note: original field name
            "credit": course.get('credit', 0),
            
            # Time and location
            "time_raw": course.get('time', ''),
            "time_slots": time_slots,
            "classroom": course.get('classroom'),
            
            # Target audience
            "targets": course.get('targets', []),
            
            # Course content
            "course_overview": course.get('course_overview'),
            "course_objective": course.get('course_objective'),
            "comment": course.get('comment'),
            
            # Embedding text for debugging
            "embedding_text": embedding_text,
            
            # Searchable fields
            "full_text": embedding_text
        }
        
        return PointStruct(
            id=index,
            vector=embedding,
            payload=payload
        )
    
    def create_collection(self):
        """Create or recreate the courses collection"""
        msg = "\nCreating vector database collection..."
        logger.info(msg)
        print(msg)
        
        try:
            # Delete existing collection if it exists
            self.client.delete_collection(collection_name=self.collection_name)
            msg = f"Deleted existing collection: {self.collection_name}"
            logger.info(msg)
            print(msg)
        except Exception as e:
            msg = f"Collection {self.collection_name} may not exist or could not be deleted: {e}"
            logger.warning(msg)
            print(f"Warning: {msg}")
        
        # Create new collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=384,  # paraphrase-multilingual-MiniLM-L12-v2 embedding size
                distance=Distance.COSINE
            )
        )
        msg = f"Created collection: {self.collection_name}"
        logger.info(msg)
        print(msg)
    
    def upload_courses(self, courses: List[Dict]):
        """Upload course data to vector database"""
        msg_uploading = "\nUploading course data..."
        logger.info(msg_uploading)
        print(msg_uploading)
        
        msg_starting = f"Starting upload of {len(courses)} courses..."
        logger.info(msg_starting)
        print(msg_starting)
        
        points = []
        for i, course in enumerate(courses):
            logger.debug(f"Processing course {i+1}: {course.get('name', 'Unknown')[:30]}...") # Keep detailed processing to debug
            point = self.process_course(course, i)
            points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        
        msg_success = f"Successfully uploaded {len(courses)} courses to vector database"
        logger.info(msg_success)
        print(msg_success)


def load_course_data(data_dir: str = "data/") -> List[Dict]:
    """Load course data from all JSON files in the specified directory and its subdirectories (recursively)"""
    msg_loading = f"Loading course data recursively from directory: {data_dir}"
    logger.info(msg_loading)
    print(msg_loading)
    all_courses = []
    
    try:
        if not os.path.isdir(data_dir):
            err_msg = f"Data directory not found at {data_dir}"
            logger.error(err_msg)
            print(f"ERROR: {err_msg}")
            return []
            
        for root, _, files in os.walk(data_dir):
            for filename in files:
                if filename.endswith(".json"):
                    file_path = os.path.join(root, filename)
                    logger.info(f"Processing file: {file_path}...") # Log individual file processing
                    # print(f"Processing file: {file_path}...") # Decided against printing for every file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            courses_in_file = json.load(f)
                            if isinstance(courses_in_file, list):
                                all_courses.extend(courses_in_file)
                                # logger.info(f"Successfully loaded {len(courses_in_file)} courses from {filename}") # User commented this out
                            elif isinstance(courses_in_file, dict):
                                all_courses.append(courses_in_file)
                                # logger.info(f"Successfully loaded 1 course from {filename}") # User commented this out
                            else:
                                warn_msg = f"{filename} does not contain a list or a single dictionary of courses. Skipping."
                                logger.warning(warn_msg)
                                print(f"Warning: {warn_msg}")
                    except json.JSONDecodeError as e:
                        err_msg_json = f"Error parsing JSON file {filename}: {e}"
                        logger.error(err_msg_json)
                        print(f"ERROR: {err_msg_json}")
                    except Exception as e:
                        err_msg_proc = f"An unexpected error occurred while processing {filename}: {e}"
                        logger.error(err_msg_proc)
                        print(f"ERROR: {err_msg_proc}")
        
        if not all_courses:
            warn_msg_none = f"No courses found in JSON files in {data_dir} or its subdirectories"
            logger.warning(warn_msg_none)
            print(f"Warning: {warn_msg_none}")
        else:
            success_msg_load = f"Successfully loaded a total of {len(all_courses)} courses from {data_dir} and its subdirectories"
            logger.info(success_msg_load)
            print(success_msg_load)
        return all_courses

    except Exception as e:
        err_msg_walk = f"An unexpected error occurred while recursively searching for JSON files in {data_dir}: {e}"
        logger.error(err_msg_walk)
        print(f"ERROR: {err_msg_walk}")
        return []


def main():
    """Main execution function"""
    start_msg = "Course Vector Database Upload Script Started"
    separator = "=" * 40
    logger.info(start_msg)
    print(start_msg)
    logger.info(separator)
    print(separator)
    
    courses = load_course_data() 
    if not courses:
        exit_msg = "No course data to process. Exiting."
        logger.warning(exit_msg)
        print(exit_msg)
        return
    
    embedder = CourseEmbedder()
    
    embedder.create_collection()
    
    embedder.upload_courses(courses)
    
    complete_msg = "\nUpload complete!"
    ready_msg = "Vector database is ready for use."
    logger.info(complete_msg)
    print(complete_msg)
    logger.info(ready_msg)
    print(ready_msg)


if __name__ == "__main__":
    main() 