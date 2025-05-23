#!/usr/bin/env python3
"""
Course Vector Database Upload Script
Loads course data, creates embeddings, and uploads to Qdrant vector database
"""

import json
import re
import os
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class CourseEmbedder:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize course embedder with Qdrant client"""
        print("Initializing course embedder...")
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port, check_compatibility=False)
        self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.collection_name = "ntu_courses"
        print("Loading multilingual semantic model...")
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
        print("\nCreating vector database collection...")
        
        try:
            # Delete existing collection if it exists
            self.client.delete_collection(collection_name=self.collection_name)
            print(f"Deleted existing collection: {self.collection_name}")
        except Exception as e:
            print(f"Collection may not exist: {e}")
        
        # Create new collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=384,  # paraphrase-multilingual-MiniLM-L12-v2 embedding size
                distance=Distance.COSINE
            )
        )
        print(f"Created collection: {self.collection_name}")
    
    def upload_courses(self, courses: List[Dict]):
        """Upload course data to vector database"""
        print(f"\nUploading course data...")
        print(f"Starting upload of {len(courses)} courses...")
        
        points = []
        for i, course in enumerate(courses):
            print(f"Processing course {i+1}: {course.get('name', 'Unknown')[:30]}...")
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
        
        print(f"Successfully uploaded {len(courses)} courses to vector database")


def load_course_data(data_dir: str = "data/") -> List[Dict]:
    """Load course data from all JSON files in the specified directory"""
    print(f"Loading course data from directory: {data_dir}")
    all_courses = []
    
    try:
        if not os.path.isdir(data_dir):
            print(f"Error: Data directory not found at {data_dir}")
            return []
            
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(data_dir, filename)
                print(f"Processing file: {file_path}...")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        courses_in_file = json.load(f)
                        if isinstance(courses_in_file, list): # Expecting a list of courses
                            all_courses.extend(courses_in_file)
                            print(f"Successfully loaded {len(courses_in_file)} courses from {filename}")
                        else:
                            print(f"Warning: {filename} does not contain a list of courses. Skipping.")
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON file {filename}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred while processing {filename}: {e}")
        
        if not all_courses:
            print(f"No courses found in JSON files in {data_dir}")
        else:
            print(f"Successfully loaded a total of {len(all_courses)} courses from {data_dir}")
        return all_courses

    except FileNotFoundError: # Should be caught by os.path.isdir check, but as a fallback
        print(f"Error: Data directory not found at {data_dir}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while accessing data directory {data_dir}: {e}")
        return []


def main():
    """Main execution function"""
    print("Course Vector Database Upload")
    print("=" * 40)
    
    # Load course data from data/ directory
    courses = load_course_data() # Updated call, uses default "data/"
    if not courses:
        print("No course data to process. Exiting.")
        return
    
    # Initialize embedder
    embedder = CourseEmbedder()
    
    # Create collection
    embedder.create_collection()
    
    # Upload courses
    embedder.upload_courses(courses)
    
    print("\nUpload complete!")
    print("Vector database is ready for use.")


if __name__ == "__main__":
    main() 