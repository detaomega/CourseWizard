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

class InteractiveQuery:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize interactive query tool"""
        self.client = None
        self.model = None
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = "ntu_courses"
        
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

        try:
            query_vector = self.model.encode(query_text).tolist()
            
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True
            )
            
            results = []
            for hit in search_results:
                payload = hit.payload
                result = {
                    "id": payload.get("id", "N/A"),
                    "name": payload.get("name", "N/A"),
                    "identifier": payload.get("identifier", "N/A"),
                    "teacher_name": payload.get("teacher_name", "N/A"),
                    "host_department": payload.get("host_department", "N/A"),
                    "code": payload.get("code", "N/A"),
                    "credits": payload.get("credits", 0),
                    "time_slots": payload.get("time_slots", []),
                    "notes": payload.get("notes", "N/A"),
                    "score": hit.score
                }
                results.append(result)
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def display_results(self, results: List[Dict[str, Any]]):
        """Display search results in a user-friendly format"""
        if not results:
            print("No results found or error in search.")
            return

        print("\nSearch Results:")
        print("-" * 30)
        for i, course in enumerate(results, 1):
            print(f"{i}. {course['name']} (ID: {course['id']}, Score: {course['score']:.4f})")
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