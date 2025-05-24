#!/usr/bin/env python3
"""
Course Search and Recommendation API
FastAPI service for semantic course search and intelligent scheduling
"""

import re
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
import uvicorn


# Pydantic models for API
class TimeSlotItem(BaseModel):
    weekday: int
    period: str
    classroom: str

class CourseResponse(BaseModel):
    name: str
    identifier: str
    code: str
    teacher_name: str
    host_department: str
    credits: int
    time_slots: List[TimeSlotItem]
    classroom: Optional[str]
    targets: List[str]
    course_overview: Optional[str]
    course_objective: Optional[str]
    notes: Optional[str]
    score: Optional[float] = None
    id: str
    serial: Optional[str] = None
    original_json_string: Optional[str] = None


class ScheduleRequest(BaseModel):
    course_codes: List[str]  # Using course codes instead of IDs
    max_credits: int = 18


class ScheduleResponse(BaseModel):
    courses: List[CourseResponse]
    total_credits: int
    conflicts: List[str]
    success: bool


class RecommendationRequest(BaseModel):
    query: str
    max_credits: int = 18
    semester: str = "113-2"


class CourseSearchAPI:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize API with Qdrant client and embedding model"""
        self.client = None
        self.model = None
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = "ntu_courses"
    
    def _lazy_init(self):
        """Lazy initialization of heavy components"""
        if self.client is None:
            print("Initializing Qdrant client...")
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port, check_compatibility=False)
        
        if self.model is None:
            model_name = "BAAI/bge-m3"
            print(f"Attempting to load embedding model: {model_name}...")
            try:
                self.model = SentenceTransformer(model_name)
                print(f"Successfully loaded embedding model: {model_name}.")
            except Exception as e:
                print(f"ERROR: Failed to load SentenceTransformer model '{model_name}'. Error: {e}")
                # Depending on API behavior, you might want to raise an error here
                # or let subsequent calls fail if the model is essential.
                # For now, it will print the error and proceed, potentially failing later.
                raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")
    
    def has_time_conflict(self, course1_slots: List[Dict], course2_slots: List[Dict]) -> bool:
        """Check if two courses have time conflicts based on new time_slots structure."""
        for slot1 in course1_slots:
            for slot2 in course2_slots:
                s1_weekday = slot1.get("weekday")
                s1_period = slot1.get("period")
                s2_weekday = slot2.get("weekday")
                s2_period = slot2.get("period")

                if (s1_weekday is not None and s1_period is not None and
                    s2_weekday is not None and s2_period is not None and
                    s1_weekday == s2_weekday and 
                    s1_period == s2_period):
                    return True
        return False
    
    def search_courses(self, query: str, semester: str = None, department: str = None, 
                      top_k: int = 10) -> List[Dict[str, Any]]:
        """Semantic search for courses"""
        self._lazy_init()
        
        query_vector = self.model.encode(query).tolist()
        
        # Build filters
        filters = {}
        if semester:
            filters["semester"] = semester
        if department:
            filters["department"] = department
        
        try:
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key=k, match=models.MatchValue(value=v)) 
                          for k, v in filters.items()]
                ) if filters else None,
                limit=top_k,
                with_payload=True
            )
            results = search_result.points
        except Exception:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=models.Filter(
                        must=[models.FieldCondition(key=k, match=models.MatchValue(value=v)) 
                              for k, v in filters.items()]
                    ) if filters else None,
                    limit=top_k,
                    with_payload=True
                )
            results = search_result
        
        courses = []
        for result in results:
            course = result.payload
            course["score"] = float(result.score)
            courses.append(course)
        
        return courses
    
    def get_course_by_code(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Get specific course by code"""
        self._lazy_init()
        
        try:
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(
                        key="code",
                        match=models.MatchValue(value=course_code)
                    )]
                ),
                limit=1
            )
            
            if search_result[0]:
                course = search_result[0][0].payload
                return course
        except Exception as e:
            print(f"Error retrieving course {course_code}: {e}")
        
        return None
    
    def generate_schedule(self, course_codes: List[str], max_credits: int = 18) -> Dict[str, Any]:
        """Generate conflict-free schedule from course codes"""
        courses = []
        for course_code in course_codes:
            course = self.get_course_by_code(course_code)
            if course:
                courses.append(course)
        
        if not courses:
            return {"schedule": [], "total_credits": 0, "conflicts": [], "message": "No valid courses found"}
        
        # Greedy algorithm for schedule optimization
        selected_courses = []
        total_credits = 0
        conflicts = []
        
        # Sort by credits (optional: could sort by other criteria)
        courses.sort(key=lambda x: x.get("credits", 0), reverse=True)
        
        for course in courses:
            course_credits = course.get("credits", 0)
            course_time_slots = course.get("time_slots", [])
            
            # Check credit limit
            if total_credits + course_credits > max_credits:
                conflicts.append(f"Credit limit exceeded: {course['name']} ({course_credits} credits)")
                continue
            
            # Check time conflicts
            has_conflict = False
            for selected_course in selected_courses:
                selected_time_slots = selected_course.get("time_slots", [])
                if self.has_time_conflict(course_time_slots, selected_time_slots):
                    conflicts.append(f"Time conflict: {course['name']} conflicts with {selected_course['name']}")
                    has_conflict = True
                    break
            
            if not has_conflict:
                selected_courses.append(course)
                total_credits += course_credits
        
        return {
            "schedule": selected_courses,
            "total_credits": total_credits,
            "conflicts": conflicts,
            "message": f"Successfully scheduled {len(selected_courses)} courses"
        }
    
    def recommend_courses(self, query: str, max_credits: int = 18, 
                         semester: str = "113-2") -> Dict[str, Any]:
        """AI-powered course recommendations"""
        # Get initial recommendations via semantic search
        recommended_courses = self.search_courses(
            query=query,
            semester=semester,
            top_k=20  # Get more candidates for filtering
        )
        
        # Generate optimized schedule from recommendations
        course_codes = [course["code"] for course in recommended_courses]
        schedule_result = self.generate_schedule(course_codes, max_credits)
        
        return {
            "query": query,
            "total_candidates": len(recommended_courses),
            "recommended_schedule": schedule_result["schedule"],
            "total_credits": schedule_result["total_credits"],
            "conflicts": schedule_result["conflicts"],
            "message": schedule_result["message"]
        }


# Initialize API
api = CourseSearchAPI()
app = FastAPI(title="Course Search API", description="Semantic course search and scheduling", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "Course Search and Recommendation API", "docs": "/docs"}


@app.get("/search")
async def search_courses(
    q: str = Query(..., description="Search query"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    department: Optional[str] = Query(None, description="Filter by department"),
    top_k: int = Query(10, description="Number of results to return")
):
    """Semantic search for courses"""
    try:
        results = api.search_courses(
            query=q,
            semester=semester,
            department=department,
            top_k=top_k
        )
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/course/{course_code}")
async def get_course(course_code: str):
    """Get specific course by code"""
    course = api.get_course_by_code(course_code)
    if course:
        return course
    else:
        raise HTTPException(status_code=404, detail="Course not found")


@app.post("/schedule")
async def create_schedule(request: ScheduleRequest):
    """Generate conflict-free schedule from course codes"""
    try:
        result = api.generate_schedule(request.course_codes, request.max_credits)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schedule generation failed: {str(e)}")


@app.post("/recommend")
async def recommend_courses(request: RecommendationRequest):
    """AI-powered course recommendations"""
    try:
        result = api.recommend_courses(
            query=request.query,
            max_credits=request.max_credits,
            semester=request.semester
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        api._lazy_init()
        # Test connection to Qdrant
        collections = api.client.get_collections()
        return {
            "status": "healthy",
            "qdrant_connected": True,
            "collections": [c.name for c in collections.collections]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    print("Starting Course Search API...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 