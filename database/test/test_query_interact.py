#!/usr/bin/env python3
"""
Interactive Vector Database Query Script
Allows interactive querying of the course vector database.
"""

import sys
import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from database.config import collection_names, weights

class InteractiveQuery:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize interactive query tool"""
        self.client = None
        self.model = None
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_names = collection_names
        self.weights = weights
        
        print("Interactive Course Query Tool")
        print("Type 'exit' or 'quit' to stop.")
        print("=" * 40)
        self._lazy_init()

    def _lazy_init(self):
        """Initialize Qdrant client and sentence transformer model"""
        if self.client is None:
            try:
                print("Connecting to Qdrant...")
                self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port, check_compatibility=False)
                self.client.get_collections() # Test connection
                print("Qdrant connection successful.")
            except Exception as e:
                print(f"Error: Could not connect to Qdrant at {self.qdrant_host}:{self.qdrant_port}. Please ensure Qdrant is running.")
                print(f"Details: {e}")
                sys.exit(1)
        
        if self.model is None:
            try:
                model_name = "BAAI/bge-m3"
                print(f"Attempting to load embedding model: {model_name} (this may take a moment)...")
                self.model = SentenceTransformer(model_name)
                print(f"Successfully loaded embedding model: {model_name}.")
            except Exception as e:
                print(f"Error: Could not load sentence-transformer model '{model_name}'.")
                print(f"Details: {e}")
                sys.exit(1)

    def perform_search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search and return results"""
        if not self.client or not self.model:
            print("Error: Qdrant client or model not initialized.")
            return []
    
        query_vector = self.model.encode(query_text).tolist()

        course_scrores = {}
        course_data = {}
        # try:
        now_len = 0
        for attr, collection_name in self.collection_names.items():
            now_len += 1
            results = self.client.search(
                collection_name = collection_name,
                query_vector=query_vector,
                limit = top_k*len(self.collection_names),
                with_payload=True,
            )
            for point in results:
                course_id = point.payload['id']
                score = float(point.score) * self.weights[attr]
                if course_id not in course_scrores:
                    course_scrores[course_id] = []
                    course_data[course_id] = point.payload
                course_scrores[course_id].append(score)
            
            for course_id, scores in course_scrores.items():
                if len(scores) < now_len:
                    course_scrores[course_id].append(0.0)
        
        sorted_courses = sorted(course_scrores.items(), key=lambda x: sum(x[1]), reverse=True)
        print("Sorted course scores and names:")
        for course_id, scores in sorted_courses:
            name = course_data[course_id]["name"]
            print(f"Name: {name}, Scores: {scores}")
        final_results = []
        for course_id, score in sorted_courses[:top_k]:
            course = course_data[course_id]
            course["score"] = score
            final_results.append(course)
        
        return final_results

    def display_results(self, results: List[Dict[str, Any]]):
        """Display search results in a user-friendly format"""
        if not results:
            print("No results found or error in search.")
            return

        print("\nSearch Results:")
        print("-" * 30)
        for i, course in enumerate(results, 1):
            print(f"{i}. {course['name']} (ID: {course['id']}, Score: {course['score']})")
            print(f"   Identifier: {course['identifier']}")
            print(f"   Teacher: {course['teacher_name']}")
            print(f"   Department: {course['host_department']}")
            print(f"   Code: {course['code']}")
            print(f"   Credits: {course['credits']}")
            
            time_slots = course.get('time_slots', [])
            if time_slots:
                print("   Time Slots:")
                for slot in time_slots:
                    # Simple representation, can be enhanced with weekday mapping if desired
                    print(f"     - Day: {slot.get('weekday')}, Period: {slot.get('period')}, Classroom: {slot.get('classroom', 'N/A')}")
            else:
                print("   Time Slots: Not available")
            
            print(f"   Notes: {course['notes']}")
            print("-" * 30)

    def run_interactive_loop(self):
        """Run the main interactive query loop"""
        while True:
            try:
                query = input("\nEnter your search query: ")
                if query.lower() in ['exit', 'quit']:
                    print("Exiting interactive query tool.")
                    break
                if not query.strip():
                    continue

                results = self.perform_search(query)
                self.display_results(results)
            except KeyboardInterrupt:
                print("\nExiting due to KeyboardInterrupt.")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

def main():
    """Main execution function"""
    interactive_query_tool = InteractiveQuery()
    interactive_query_tool.run_interactive_loop()

if __name__ == "__main__":
    main() 