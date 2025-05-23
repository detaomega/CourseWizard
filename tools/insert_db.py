import json
import os

def gettime(schedules):
    """
    "schedules": [
        {
            "weekday": 5,
            "intervals": [
                "7",
                "8"
            ],
            "classroom": {
                "id": "6f80d3ac-deb3-4186-ad85-32839d301a4c",
                "name": "資105",
                "location": "資訊館",
                "buildingName": "資訊工程館",
                "buildingId": "AT3001",
                "accessibility": true,
                "layer": "build",
                "detail": "資訊系館105"
            }
        }
    ],
    """
    time = ""
    for schedule in schedules:
        weekday = schedule['weekday']
        intervals = schedule['intervals']
        intervals = ''.join(intervals)
        time += f"weekday {weekday}, {intervals}. "
    return time

def get_classroom(schedules):
    """
    "schedules": [
        {
            "weekday": 5,
            "intervals": [
                "7",
                "8"
            ],
            "classroom": {
                "id": "6f80d3ac-deb3-4186-ad85-32839d301a4c",
                "name": "資105",
                "location": "資訊館",
                "buildingName": "資訊工程館",
                "buildingId": "AT3001",
                "accessibility": true,
                "layer": "build",
                "detail": "資訊系館105"
            }
        }
    ],
    """
    classroom = None
    if len(schedules) > 0:
        classroom = schedules[0].get('classroom', {})
        if classroom:
            classroom = classroom.get('name', None)
    return classroom

if __name__ == '__main__':
    semesters = ["113-2"]
    infos = []
    for semester in semesters:
        courses_files = os.listdir(f'data/{semester}')
        
        for course_file in courses_files:
            course_path = os.path.join(f'data/{semester}', course_file)
            course_info = json.load(open(course_path, 'r', encoding='utf-8'))
            if "資訊工程學研究所" not in course_info['hostDepartment']:
                continue
            print(course_info)
            
            print(f"~/SQL_FINAL/{course_path}")
            info =   {
                "name": course_info["name"],
                "course_number": course_info["identifier"],
                "code": course_info["code"],
                "semester": semester,
                "targets": [target['department']['name'] for target in course_info['courseTargets']],
                "teacger": course_info["teacher"].get('name', None),
                "department": course_info["hostDepartment"],
                "credit": course_info["credits"],
                "time": gettime(course_info["schedules"]),
                "classroom": get_classroom(course_info["schedules"]),
                "comment": course_info["info"]["備註"],
                "course_overview": course_info["info"]["課程概述"],
                "course_objective": course_info["info"]["課程目標"],               
            }
            infos.append(info)
    with open('course.json', 'w', encoding='utf-8') as f:
        json.dump(infos, f, ensure_ascii=False, indent=4)   

# python3 -m tools.insert_db
