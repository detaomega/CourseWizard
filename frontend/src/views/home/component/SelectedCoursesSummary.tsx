import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Course {
  id: string;
  name: string;
  credits: number;
  instructor: string;
  time: string;
  location: string;
  type: string;
  capacity: number;
  enrolled: number;
  description: string;
}

interface SelectedCoursesSummaryProps {
  selectedCourses: Course[];
  totalCredits: number;
  securityCourses: number;
  isLoading: boolean;
  toggleCourseSelection: (course: Course) => void;
  generateSchedule: () => void;
}

const SelectedCoursesSummary: React.FC<SelectedCoursesSummaryProps> = ({
  selectedCourses,
  totalCredits,
  securityCourses,
  isLoading,
  toggleCourseSelection,
  generateSchedule,
}) => {
  if (selectedCourses.length === 0) return null;
  return (
    <Card className="bg-white/90 backdrop-blur-sm border-blue-200 shadow-lg">
      <CardHeader>
        <CardTitle className="text-gray-900">已選課程統計</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-4 mb-4">
          <div className="flex items-center gap-2">
            <span className="text-gray-700">總學分：</span>
            <Badge className="bg-green-100 text-green-800">{totalCredits} 學分</Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-700">資安課程：</span>
            <Badge className="bg-purple-100 text-purple-800">{securityCourses} 門</Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-700">已選課程：</span>
            <Badge className="bg-blue-100 text-blue-800">{selectedCourses.length} 門</Badge>
          </div>
        </div>
        <div className="space-y-2">
          {selectedCourses.map((course) => (
            <div
              key={course.id}
              className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <span className="text-gray-800 font-medium">{course.name}</span>
                <span className="text-gray-600 text-sm ml-2">({course.time})</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-blue-400 text-blue-700 text-xs">
                  {course.credits} 學分
                </Badge>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => toggleCourseSelection(course)}
                  className="text-red-600 border-red-300 hover:bg-red-50"
                >
                  移除
                </Button>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6">
          <Button
            onClick={generateSchedule}
            disabled={isLoading || selectedCourses.length === 0}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 text-lg font-semibold"
          >
            {isLoading ? "產生中..." : "產生課表"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SelectedCoursesSummary;
