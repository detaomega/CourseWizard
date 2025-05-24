#!/usr/bin/env python3
"""
Vector Database Query Test Suite
Tests the course vector database functionality
"""

import sys
import os
import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient


class VectorDBTester:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize tester"""
        self.client = None
        self.model = None
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = "ntu_courses"
        
        print("Vector Database Test Suite")
        print("=" * 40)
    
    def lazy_init(self):
        """Initialize connections"""
        if self.client is None:
            print("Connecting to Qdrant...")
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port, check_compatibility=False)
        
        if self.model is None:
            print("Loading embedding model...")
            self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    def test_connection(self) -> bool:
        """Test Qdrant connection"""
        try:
            self.lazy_init()
            info = self.client.get_collections()
            print("PASS - Qdrant connection successful")
            return True
        except Exception as e:
            print(f"FAIL - Qdrant connection failed: {e}")
            return False
    
    def test_collection_exists(self) -> bool:
        """Test if courses collection exists"""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name in collection_names:
                print(f"PASS - Collection '{self.collection_name}' exists")
                return True
            else:
                print(f"FAIL - Collection '{self.collection_name}' not found")
                return False
        except Exception as e:
            print(f"FAIL - Collection check failed: {e}")
            return False
    
    def test_data_count(self) -> bool:
        """Test if data is present in collection"""
        try:
            result = self.client.count(collection_name=self.collection_name)
            count = result.count
            
            if count > 0:
                print(f"PASS - Found {count} courses in database")
                return True
            else:
                print("FAIL - No courses found in database")
                return False
        except Exception as e:
            print(f"FAIL - Data count check failed: {e}")
            return False
    
    def test_semantic_search(self) -> bool:
        """Test semantic search functionality"""
        try:
            test_queries = [
                "機器學習",
                "計算機圖形",
                "資訊安全",
                "人工智慧"
            ]
            
            for query in test_queries:
                query_vector = self.model.encode(query).tolist()
                
                try:
                    # Try query_points (newer method)
                    results = self.client.query_points(
                        collection_name=self.collection_name,
                        query=query_vector,
                        limit=3
                    ).points
                except Exception:
                    # Fallback to search (older method)
                    results = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        limit=3
                    )
                
                if results:
                    top_result = results[0]
                    course_name = top_result.payload.get("name", "Unknown")
                    score = float(top_result.score)
                    print(f"PASS - Query '{query}' → {course_name} (score: {score:.3f})")
                else:
                    print(f"FAIL - No results for query '{query}'")
                    return False
            
            return True
            
        except Exception as e:
            print(f"FAIL - Semantic search test failed: {e}")
            return False
    
    def test_metadata_filtering(self) -> bool:
        """Test metadata filtering functionality"""
        try:
            # Test semester filtering
            query_vector = self.model.encode("計算機").tolist()
            
            from qdrant_client import models
            
            try:
                # Try query_points (newer method)
                results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=models.Filter(
                        must=[models.FieldCondition(
                            key="semester",
                            match=models.MatchValue(value="113-2")
                        )]
                    ),
                    limit=3
                ).points
            except Exception:
                # Fallback to search (older method)
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=models.Filter(
                        must=[models.FieldCondition(
                            key="semester",
                            match=models.MatchValue(value="113-2")
                        )]
                    ),
                    limit=3
                )
            
            if results:
                print(f"PASS - Metadata filtering found {len(results)} courses")
                return True
            else:
                print("FAIL - No results from metadata filtering")
                return False
                
        except Exception as e:
            print(f"FAIL - Metadata filtering test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and report summary"""
        self.lazy_init()
        
        tests = [
            self.test_connection,
            self.test_collection_exists,
            self.test_data_count,
            self.test_semantic_search,
            self.test_metadata_filtering
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"FAIL - {test_name} crashed: {e}")
                results.append(False)
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print(f"\n{'='*40}")
        print(f"Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("All tests passed! Vector database is working correctly.")
            return True
        else:
            print(f"{total - passed} test(s) failed. Please check the issues above.")
            return False

    def display_results(self, results: List[Any], query: str):
        """Display search results in a readable format"""
        print(f"\n--- Search Results for: '{query}' ---")
        if not results:
            print("No courses found.")
            return
        
        for i, hit in enumerate(results):
            payload = hit.payload
            print(f"\nResult {i+1}:")
            print(f"  Name: {payload.get('name')}")
            print(f"  ID: {payload.get('id')}")
            print(f"  Identifier: {payload.get('identifier')}")
            print(f"  Code: {payload.get('code')}")
            print(f"  Teacher: {payload.get('teacher_name')}")
            print(f"  Department: {payload.get('host_department')}")
            print(f"  Credits: {payload.get('credits')}")
            
            # Display new time_slots structure
            time_slots = payload.get('time_slots', [])
            if time_slots:
                print("  Time Slots:")
                for slot in time_slots:
                    print(f"    - {slot}")
            else:
                print("  Time Slots: Not available")

            print(f"  Notes: {payload.get('notes', 'N/A')}")
            print(f"  Score: {hit.score:.4f}" if hasattr(hit, 'score') and hit.score is not None else "Score: N/A")


def main():
    """Main test execution"""
    tester = VectorDBTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 