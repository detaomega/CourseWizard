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
    
    def test_time_parsing(self) -> bool:
        """Test time slot parsing functionality"""
        try:
            test_cases = [
                ("weekday 4, 234. ", 3),  # Thursday periods 2,3,4
                ("weekday 2, 789. ", 3),  # Tuesday periods 7,8,9
                ("weekday 3, 345. ", 3),  # Wednesday periods 3,4,5
                ("", 0),                  # Empty time
            ]
            
            for time_str, expected_slots in test_cases:
                slots = self.parse_time_slots(time_str)
                if len(slots) == expected_slots:
                    if expected_slots > 0:
                        print(f"PASS - Time parsing '{time_str}' → {len(slots)} slots")
                    else:
                        print(f"PASS - Empty time string handled correctly")
                else:
                    print(f"FAIL - Time parsing '{time_str}' expected {expected_slots} slots, got {len(slots)}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"FAIL - Time parsing test failed: {e}")
            return False
    
    def parse_time_slots(self, time_str: str) -> List[Dict[str, Any]]:
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
        """Run all tests"""
        tests = [
            ("Database Connection", self.test_connection),
            ("Collection Check", self.test_collection_exists),
            ("Data Count", self.test_data_count),
            ("Semantic Search", self.test_semantic_search),
            ("Time Parsing", self.test_time_parsing),
            ("Metadata Filtering", self.test_metadata_filtering),
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


def main():
    """Main test execution"""
    tester = VectorDBTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 