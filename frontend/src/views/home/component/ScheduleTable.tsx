import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "lucide-react";

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

interface ScheduleSlot {
  day: string;
  period: string;
  timeRange: string;
  course: Course | null;
}

interface ScheduleTableProps {
  generatedSchedule: ScheduleSlot[];
  totalCredits: number;
  securityCourses: number;
  periodTable: Record<string, string>;
}

const ScheduleTable: React.FC<ScheduleTableProps> = ({
  generatedSchedule,
  totalCredits,
  securityCourses,
  periodTable,
}) => {
  const periods = ['0', '1', '2', '3', '4', '6', '7', '8', '9', 'A', 'B', 'C', 'D'];
  const days = ['週一', '週二', '週三', '週四', '週五'];

  if (generatedSchedule.length === 0) return null;

  return (
    <Card className="bg-white/90 backdrop-blur-sm border-blue-200 shadow-lg">
      <CardHeader>
        <CardTitle className="text-gray-900 flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          推薦課表 (依台大節次表)
        </CardTitle>
        <CardDescription className="text-gray-600">
          已為您安排 {totalCredits} 學分，包含 {securityCourses} 門資安課程，無時間衝突
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="border border-gray-300 p-2 bg-blue-100 text-gray-900 font-semibold">節次</th>
                <th className="border border-gray-300 p-2 bg-blue-100 text-gray-900 font-semibold">時間</th>
                {days.map(day => (
                  <th key={day} className="border border-gray-300 p-2 bg-blue-100 text-gray-900 font-semibold">{day}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {periods.map((period) => (
                <tr key={period}>
                  <td className="border border-gray-300 p-2 bg-gray-50 text-gray-800 font-medium text-center">
                    {period}
                  </td>
                  <td className="border border-gray-300 p-2 bg-gray-50 text-gray-700 text-center text-xs">
                    {periodTable[period as keyof typeof periodTable]}
                  </td>
                  {days.map((day) => {
                    const slot = generatedSchedule.find(s => s.day === day && s.period === period);
                    return (
                      <td key={day} className="border border-gray-300 p-1 min-w-[120px]">
                        {slot?.course ? (
                          <div className="bg-gradient-to-br from-blue-100 to-purple-100 p-2 rounded-lg">
                            <div className="font-semibold text-gray-900 text-xs mb-1">
                              {slot.course.name}
                            </div>
                            <div className="text-xs text-gray-700">
                              {slot.course.instructor}
                            </div>
                            <div className="text-xs text-gray-600">
                              {slot.course.location}
                            </div>
                            <Badge className="mt-1 bg-blue-500 text-white text-xs">
                              {slot.course.credits}學分
                            </Badge>
                          </div>
                        ) : (
                          <div className="h-16 bg-gray-50 rounded-lg"></div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

export default ScheduleTable;