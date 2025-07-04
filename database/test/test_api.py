#!/usr/bin/env python3
"""
API Test Suite
Tests FastAPI endpoints for the course vector database system
"""

import requests
import json
import time
from typing import Dict, List


class APITester:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """Initialize API tester"""
        self.base_url = api_base_url
        print(f"Testing API at: {self.base_url}")
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=20)
            if response.status_code == 200:
                data = response.json()
                print(f"PASS - Health Check: {data.get('status', 'OK')}")
                return True
            else:
                print(f"FAIL - Health Check: Status code {response.status_code}")
                return False
        except Exception as e:
            print(f"FAIL - Health Check: {e}")
            return False
    
    def test_search_endpoint(self) -> bool:
        """Test semantic search endpoint"""
        paramss = [
            {"q": "計算機圖形", "limit": 3},
            {"q": "machine learning", "limit": 3},
            {"q": "machine learning", "limit": 3, "departments": ["資訊工程學研究所"]},
            {"q": "data structures", "limit": 3},
            {"q": "english course", "limit": 3},
            {"q": "english course", "limit": 3, "departments": ["資訊工程學系"]},
            {"q": "計算機概論", "limit": 3}
        ]

        
        print("\nTesting search endpoint...")
        all_passed = True
        
        for params in paramss:
            try:
                response = requests.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results and len(results) > 0:
                        best_match = results[0]
                        score = best_match.get('score', 0)
                        name = best_match.get('name', 'Unknown')
                        # Verify new time_slots structure (example check on the first slot of the first result)
                        time_slots = best_match.get('time_slots', [])
                        if time_slots:
                            first_slot = time_slots[0]
                            if not (isinstance(first_slot.get('weekday'), int) and \
                                    isinstance(first_slot.get('period'), str) and \
                                    isinstance(first_slot.get('classroom'), str)):
                                print(f"  WARN - Query: '{params}' -> Time_slots structure incorrect: {first_slot}")
                                # all_passed = False # Decide if this is a hard fail
                        elif best_match.get('id'): # if id exists, time_slots should ideally exist, even if empty
                            print(f"  WARN - Query: '{params}' -> '{name}' has no time_slots array.")

                        print(f"  PASS - Query: '{params}' -> '{name}' (ID: {best_match.get('id')}, Score: {score:.3f})")
                    else:
                        print(f"  FAIL - Query: '{params}' -> No results")
                        all_passed = False
                else:
                    print(f"  FAIL - Query: '{params}' -> Status {response.status_code}, Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                print(f"  FAIL - Query: '{params}' -> Error: {e}")
                all_passed = False
        
        return all_passed
    
    def test_course_detail(self) -> bool:
        """Test course detail endpoint"""
        try:
            # First get a course code from search
            search_response = requests.get(
                f"{self.base_url}/search",
                params={"q": "計算機圖形", "limit": 1},
                timeout=10
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                search_results = search_data.get("results", [])
                if search_results and len(search_results) > 0:
                    course_code = search_results[0].get('code')
                    if not course_code:
                        print("FAIL - Course Detail: Could not retrieve a valid course code from search.")
                        return False
                    
                    # Test course detail endpoint
                    detail_response = requests.get(f"{self.base_url}/course/{course_code}", timeout=5)
                    
                    if detail_response.status_code == 200:
                        course_data = detail_response.json()
                        course_name = course_data.get('name', 'Unknown')
                        course_id = course_data.get('id', 'N/A')
                        # Basic check for new fields
                        if not (course_data.get('identifier') and course_data.get('teacher_name') and course_data.get('host_department') and course_data.get('credits') is not None):
                            print(f"FAIL - Course Detail: Missing some new fields for {course_name} (ID: {course_id})")
                            return False
                        # Check time_slots structure
                        time_slots = course_data.get('time_slots', [])
                        if time_slots:
                            first_slot = time_slots[0]
                            if not (isinstance(first_slot.get('weekday'), int) and \
                                    isinstance(first_slot.get('period'), str) and \
                                    isinstance(first_slot.get('classroom'), str)):
                                print(f"FAIL - Course Detail: Time_slots structure incorrect for {course_name} (ID: {course_id}): {first_slot}")
                                return False
                        elif course_id != 'N/A': # if id exists, time_slots should ideally exist, even if empty
                             print(f"WARN - Course Detail: '{course_name}' (ID: {course_id}) has no time_slots array.")

                        print(f"PASS - Course Detail: Retrieved '{course_name}' (ID: {course_id}, Code: {course_code})")
                        return True
                    else:
                        print(f"FAIL - Course Detail: Status {detail_response.status_code}, Response: {detail_response.text}")
                        return False
                else:
                    print("FAIL - Course Detail: No courses found from search for testing")
                    return False
            else:
                print(f"FAIL - Course Detail: Search failed with status {search_response.status_code}, Response: {search_response.text}")
                return False
                
        except Exception as e:
            print(f"FAIL - Course Detail: {e}")
            return False
    
    def test_schedule_generation(self) -> bool:
        """Test schedule generation endpoint"""
        try:
            # Test with sample course codes
            # Get some course codes first to ensure they exist
            search_response = requests.get(f"{self.base_url}/search", params={"q": "資訊工程", "limit": 5}, timeout=10)
            if search_response.status_code != 200:
                print(f"FAIL - Schedule Generation: Could not fetch course codes for test. Status: {search_response.status_code}")
                return False
            
            search_data = search_response.json()
            course_codes = [course.get('code') for course in search_data.get("results", []) if course.get('code')]
            
            if not course_codes or len(course_codes) < 2:
                print("FAIL - Schedule Generation: Not enough valid course codes retrieved for test.")
                return False
                
            test_schedule_request = {
                "course_codes": course_codes[:3],
                "max_credits": 10
            }
            
            response = requests.post(
                f"{self.base_url}/schedule",
                json=test_schedule_request,
                timeout=15
            )
            
            if response.status_code == 200:
                schedule_data = response.json()
                courses = schedule_data.get('schedule', [])
                conflicts = schedule_data.get('conflicts', [])
                
                print(f"PASS - Schedule Generation: {len(courses)} courses, {len(conflicts)} conflicts")
                
                # Show sample courses in schedule
                if courses:
                    print(f"  Sample courses: {[c.get('name', 'Unknown')[:30] for c in courses[:3]]}")
                    # Check structure of a sample course in schedule
                    sample_course_in_schedule = courses[0]
                    if not (sample_course_in_schedule.get('identifier') and sample_course_in_schedule.get('teacher_name')):
                        print(f"  WARN - Schedule Generation: Sample course in schedule might be missing new fields.")
                    time_slots_in_schedule = sample_course_in_schedule.get('time_slots', [])
                    if time_slots_in_schedule:
                        first_slot_schedule = time_slots_in_schedule[0]
                        if not (isinstance(first_slot_schedule.get('weekday'), int) and \
                                isinstance(first_slot_schedule.get('period'), str)):
                            print(f"  WARN - Schedule Generation: Time_slots structure in scheduled course incorrect.")
                
                return True
            else:
                print(f"FAIL - Schedule Generation: Status {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"FAIL - Schedule Generation: {e}")
            return False
    
    def test_recommendations(self) -> bool:
        """Test course recommendation endpoint"""
        try:
            test_recommendation_request = {
                "query": "artificial intelligence",
                "max_credits": 15,
                "semesters": ["113-2"]
            }
            
            response = requests.post(
                f"{self.base_url}/recommend",
                json=test_recommendation_request,
                timeout=20
            )
            
            if response.status_code == 200:
                recommendations_data = response.json()
                recommended_schedule = recommendations_data.get('recommended_schedule', [])
                if recommended_schedule and len(recommended_schedule) > 0:
                    print(f"PASS - Recommendations: Found {len(recommended_schedule)} suggestions in schedule")
                    
                    # Show top recommendations
                    for i, rec in enumerate(recommended_schedule[:3], 1):
                        name = rec.get('name', 'Unknown')
                        credits = rec.get('credits', 0) # Changed from credit
                        course_id = rec.get('id', 'N/A')
                        print(f"  {i}. {name} (ID: {course_id}, Credits: {credits})")
                    
                    # Check structure of a sample recommended course
                    sample_rec_course = recommended_schedule[0]
                    if not (sample_rec_course.get('identifier') and sample_rec_course.get('teacher_name')):
                        print(f"  WARN - Recommendations: Sample recommended course might be missing new fields.")
                    time_slots_rec = sample_rec_course.get('time_slots', [])
                    if time_slots_rec:
                        first_slot_rec = time_slots_rec[0]
                        if not (isinstance(first_slot_rec.get('weekday'), int) and \
                                isinstance(first_slot_rec.get('period'), str)):
                            print(f"  WARN - Recommendations: Time_slots structure in recommended course incorrect.")
                    
                    return True
                else:
                    print("FAIL - Recommendations: No recommendations found in schedule")
                    return False
            else:
                print(f"FAIL - Recommendations: Status {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"FAIL - Recommendations: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run complete API test suite"""
        print("=" * 50)
        print("API TEST SUITE")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Search Endpoint", self.test_search_endpoint),
            ("Course Detail", self.test_course_detail),
            ("Schedule Generation", self.test_schedule_generation),
            ("Recommendations", self.test_recommendations)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n[{test_name}]")
            if test_func():
                passed += 1
        
        print("\n" + "=" * 50)
        print(f"API TEST RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("All API tests passed! Service is working correctly.")
            return True
        else:
            print("Some API tests failed. Please check the service.")
            return False


def main():
    """Run the API test suite"""
    print("Starting API tests...")
    print("Make sure the API service is running: python api/api.py")
    
    # Wait a moment for potential startup
    time.sleep(1)
    
    tester = APITester()
    success = tester.run_all_tests()
    
    if success:
        print("\nAPI service is ready for integration!")
    else:
        print("\nPlease fix API issues before proceeding.")
    
    return success


if __name__ == "__main__":
    main() 