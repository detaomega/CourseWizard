#!/usr/bin/env python3
"""
Course Vector Database Upload Script
Loads course data, creates embeddings, and uploads to Qdrant vector database
"""

import json
import re
import os
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from database.config import collection_names

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
        self.model_name = "BAAI/bge-m3"
        self.embedding_dim = 1024
        logger.info(f"Attempting to load multilingual semantic model: {self.model_name}...")
        print(f"Attempting to load multilingual semantic model: {self.model_name}...")
        try:
            self.model = SentenceTransformer(self.model_name)
            test_emb = self.model.encode("test")
            self.embedding_dim = len(test_emb)
            logger.info(f"Successfully loaded model {self.model_name}. Embedding dimension: {self.embedding_dim}")
            print(f"Successfully loaded model {self.model_name}. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model '{self.model_name}'. Error: {e}")
            print(f"ERROR: Failed to load SentenceTransformer model '{self.model_name}'. Ensure it is installed or accessible. Error: {e}")
            raise
        self.collection_names = collection_names
        logger.info("Initialization complete.")
        print("Initialization complete.")
    
    def parse_time_slots(self, schedules: List[Dict]) -> List[Dict]:
        """Parse schedule objects into structured time slots, keeping original values."""
        if not schedules:
            return []
        
        parsed_slots = []
        
        for schedule_item in schedules:
            weekday = schedule_item.get('weekday') # Keep as integer
            intervals = schedule_item.get('intervals', []) # Keep as list of strings/numbers
            
            # Safely get classroom_info, defaulting to an empty dict if 'classroom' is None or missing
            classroom_info = schedule_item.get('classroom') 
            if classroom_info is None:
                classroom_info = {}
            classroom_name = classroom_info.get('name', 'N/A')
            
            if weekday is None: # Skip if weekday is not defined
                logger.debug(f"Skipping schedule_item due to missing weekday: {schedule_item}")
                continue
                
            for period in intervals:
                parsed_slots.append({
                    "weekday": weekday,       # Store original integer weekday
                    "period": str(period),    # Store original period string/number
                    "classroom": classroom_name
                })
        return parsed_slots
    
    def _get_nested_value(self, data: Dict, path: List[str], default: Any = None) -> Any:
        """Safely get a value from a nested dictionary."""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def create_embedding_text(self, course: Dict) -> str:
        """Create text for embedding from new course data structure"""
        texts = []
        
        # Course name (most important)
        if course.get('name'):
            texts.append(course['name'])
        
        # Course overview and objectives from info sub-dictionary
        course_overview = self._get_nested_value(course, ['info', '課程概述'])
        if course_overview:
            texts.append(str(course_overview))
        
        course_objective = self._get_nested_value(course, ['info', '課程目標'])
        if course_objective:
            texts.append(str(course_objective))
        
        # Teacher name
        teacher_name = self._get_nested_value(course, ['teacher', 'name'])
        if teacher_name:
            texts.append(f"授課教師: {teacher_name}")
        
        # Host Department
        host_department = course.get('hostDepartment')
        if host_department:
            texts.append(f"開課單位: {host_department}")

        return " ".join(filter(None, texts))
    
    def process_course(self, course: Dict) -> Optional[PointStruct]:
        """Process a single course into vector database format using new structure"""
        
        course_id = course.get('id')
        if not course_id:
            logger.warning(f"Course missing 'id', skipping: {course.get('name', 'Unknown Name')}")
            print(f"Warning: Course missing 'id', skipping: {course.get('name', 'Unknown Name')}")
            return None

        # Create embedding text
        # embedding_text = self.create_embedding_text(course)
        
        # Generate embedding
        # embedding = self.model.encode(embedding_text).tolist()
        
        # Parse time slots from schedules array
        time_slots = self.parse_time_slots(course.get('schedules', []))
        
        # Store the entire original JSON as a string
        try:
            original_json_string = json.dumps(course, ensure_ascii=False)
        except TypeError as e:
            logger.error(f"Could not serialize course to JSON for id {course_id}: {e}")
            original_json_string = "Error serializing original JSON"

        # Extract specific fields for payload, adapting to new structure
        payload = {
            "id": course_id,
            "name": course.get('name', ''),
            "serial": course.get('serial', ''), # Added serial
            "identifier": course.get('identifier', ''), # Replaces course_number
            "code": course.get('code', ''),
            "semester": course.get('semester', ''),
            "host_department": course.get('hostDepartment', ''), # Renamed from department
            "teacher_name": self._get_nested_value(course, ['teacher', 'name'], ''),
            "teacher_id": self._get_nested_value(course, ['teacher', 'id'], ''),
            "credits": course.get('credits', 0),
            
            "notes": course.get('notes', ''),
            "time_slots": time_slots, # Parsed from schedules
            # Extracting first classroom as a simple representation, can be enhanced
            "classroom": self._get_nested_value(course, ['schedules', 0, 'classroom', 'name'], 'N/A') if course.get('schedules') else 'N/A',
            
            "targets": [target.get('department').get('name') if isinstance(target.get('department'), dict) else None for target in course.get('courseTargets', [])], # Extracting department names with type-check
            
            "course_overview": self._get_nested_value(course, ['info', '課程概述'], ''),
            "course_objective": self._get_nested_value(course, ['info', '課程目標'], ''),
            
            # "embedding_text": embedding_text, # For debugging
            "original_json_string": original_json_string # Store full original JSON
            # "full_text" was removed as embedding_text serves a similar purpose for search debugging
        }
        
        return payload
        # return PointStruct(
        #     id=course_id, # Use UUID from course data
        #     vector=embedding,
        #     payload=payload
        # )
    
    def create_collections(self):
        """Create or recreate the courses collection"""
        msg = "\nCreating vector database collection..."
        logger.info(msg)
        print(msg)
        
        for attr, collection_name in self.collection_names.items():
            try:
                # Delete existing collection if it exists
                self.client.delete_collection(collection_name=collection_name)
                msg = f"Deleted existing collection: {collection_name}"
                logger.info(msg)
                print(msg)
            except Exception as e:
                msg = f"Collection {collection_name} may not exist or could not be deleted: {e}"
                logger.warning(msg)
                print(f"Warning: {msg}")
        
            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,  # Use dynamic embedding_dim from loaded model
                    distance=Distance.COSINE
                )
            )
            msg = f"Created collection: {collection_name} with vector size {self.embedding_dim}"
            logger.info(msg)
            print(msg)
    
    def upload_courses(self, courses: List[Dict]):
        """Upload course data to vector database"""
        msg_uploading = "\nUploading course data..."
        logger.info(msg_uploading)
        print(msg_uploading)
        
        num_total_courses = len(courses)
        msg_starting = f"Starting upload of {num_total_courses} courses..."
        logger.info(msg_starting)
        print(msg_starting)
        
        processed_count = 0
        skipped_count = 0
        
        for attr, collection_name in self.collection_names.items():
            points = []
            for i, course_data in enumerate(courses):
                logger.debug(f"Processing course {i+1}/{num_total_courses}: {self._get_nested_value(course_data, ['name'], 'Unknown Name')[:50]}...")
                # point = self.process_course(course_data) # Pass the whole course dict
                # if point:
                #     points.append(point)
                #     processed_count += 1
                # else:
                #     skipped_count +=1

                parsed_data = self.process_course(course_data)
                if parsed_data:
                    processed_count += 1
                else:
                    skipped_count += 1
                    continue
                
                if parsed_data[attr] is None or parsed_data[attr] == '':
                    logger.warning(f"Skipping course {parsed_data['id']} due to missing attribute '{attr}'")
                    print(f"Warning: Skipping course {parsed_data['id']} due to missing attribute '{attr}'")
                    skipped_count += 1
                    continue
                embedding = self.model.encode(parsed_data[attr]).tolist()
                point = PointStruct(
                    id = parsed_data['id'],
                    vector = embedding,
                    payload = parsed_data
                )
                points.append(point)   
        
            if skipped_count > 0:
                msg_skipped = f"Skipped {skipped_count} courses due to missing 'id' or other processing issues."
                logger.warning(msg_skipped)
                print(f"Warning: {msg_skipped}")

            if not points:
                msg_no_points = "No valid course data points to upload after processing."
                logger.warning(msg_no_points)
                print(f"Warning: {msg_no_points}")
                continue
                # return

            # Upload in batches
            batch_size = 100
            actual_uploaded_count = 0
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                try:
                    self.client.upsert(
                        collection_name=collection_name,
                        points=batch
                    )
                    actual_uploaded_count += len(batch)
                    logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}, {len(batch)} points.")
                except Exception as e:
                    logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                    print(f"ERROR: Error uploading batch {i//batch_size + 1}: {e}")

            msg_success = f"Successfully processed {processed_count} courses. Uploaded {actual_uploaded_count} courses to vector database."
            logger.info(msg_success)
            print(msg_success)


def load_course_data(data_dir: str = "data/") -> List[Dict]:
    """Load course data from all JSON files in the specified directory and its subdirectories (recursively)"""
    msg_loading = f"Loading course data recursively from directory: {data_dir}"
    logger.info(msg_loading)
    print(msg_loading)
    all_courses = []
    
    if not os.path.isdir(data_dir):
        err_msg = f"Data directory not found at {data_dir}"
        logger.error(err_msg)
        print(f"ERROR: {err_msg}")
        return []
            
    for root, _, files in os.walk(data_dir):
        for filename in files:
            if filename.endswith(".json"):
                file_path = os.path.join(root, filename)
                logger.info(f"Processing file: {file_path}...")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        courses_in_file = json.load(f)
                        if isinstance(courses_in_file, list):
                            all_courses.extend(courses_in_file)
                        elif isinstance(courses_in_file, dict):
                            all_courses.append(courses_in_file)
                        else:
                            warn_msg = f"{filename} does not contain a list or a single dictionary of courses. Skipping."
                            logger.warning(warn_msg)
                            print(f"Warning: {warn_msg}")
                except json.JSONDecodeError as e:
                    err_msg_json = f"Error parsing JSON file {filename}: {e}"
                    logger.error(err_msg_json)
                    print(f"ERROR: {err_msg_json}")
                except Exception as e: # This except handles errors during file processing (not JSON parsing)
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
    
    embedder.create_collections()
    
    embedder.upload_courses(courses)
    
    complete_msg = "\nUpload complete!"
    ready_msg = "Vector database is ready for use."
    logger.info(complete_msg)
    print(complete_msg)
    logger.info(ready_msg)
    print(ready_msg)


if __name__ == "__main__":
    main() 