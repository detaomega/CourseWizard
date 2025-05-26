import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Users, Clock, MapPin } from "lucide-react";

interface Course {
  id: string;
  name: string;
  credits: number;
  serial: string;
  semester: string;
  instructor: string;
  time: string;
  location: string;
  host_department: string;
  capacity: number;
  enrolled?: number;
  description?: string;
}

interface CourseListProps {
  courses: Course[];
  selectedCourses: Course[];
  toggleCourseSelection: (course: Course) => void;
}

const CourseList: React.FC<CourseListProps> = ({
  courses,
  selectedCourses,
  toggleCourseSelection,
}) => (
  <Card className="bg-white/90 backdrop-blur-sm border-blue-200 shadow-lg">
    <CardHeader>
      <CardTitle className="text-gray-900 flex items-center gap-2">
        <BookOpen className="w-5 h-5" />
        可選課程 ({courses.length} 門)
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {courses.map((course) => {
          // console.log("Rendering course:", course.id);
          // console.log(course);
          const isSelected = selectedCourses.find((c) => c.id === course.id);
          return (
            <div
              key={course.id + course.instructor + course.time}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                isSelected
                  ? "border-blue-500 bg-blue-50 shadow-md"
                  : "border-gray-300 bg-white hover:border-blue-400 hover:shadow-sm"
              }`}
              onClick={() => toggleCourseSelection(course)}
            >
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <h3 className="font-semibold text-gray-900 text-sm">{course.name}</h3>
                  <Badge className="bg-blue-100 text-blue-800 text-xs">{course.credits} 學分</Badge>
                </div>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    <span>{course.instructor}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>{course.time}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    <span>{course.location}</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <Badge variant="outline" className="border-purple-400 text-purple-700">
                    {course.host_department}
                  </Badge>
                  <Badge variant="outline" className="border-purple-400 text-purple-700">
                    <a
                    href={`https://course.ntu.edu.tw/courses/${course.semester}/${course.serial}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline"
                    >
                    course link
                    </a>
                  </Badge>
                  <span className="text-xs text-gray-500">
                    {course.enrolled}/{course.capacity} 人
                  </span>
                </div>
                <p className="text-xs text-gray-500 leading-relaxed">{course.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </CardContent>
  </Card>
);

export default CourseList;
