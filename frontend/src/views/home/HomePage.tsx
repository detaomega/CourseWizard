import React, { useState } from "react";
import CourseSearchBar from "./component/CourseSearchBar";
import CourseList from "./component/CourseList";
import SelectedCoursesSummary from "./component/SelectedCoursesSummary";
import ScheduleTable from "./component/ScheduleTable";
import { getSearch } from "@/services/searchService";

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

interface ScheduleSlot {
  day: string;
  period: string;
  timeRange: string;
  course: Course | null;
}

const HomePage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [departments, setDepartments] = useState<string[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourses, setSelectedCourses] = useState<Course[]>([]);
  const [generatedSchedule, setGeneratedSchedule] = useState<ScheduleSlot[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // 台大節次對照表
  const periodTable = {
    "0": "07:10-08:00",
    "1": "08:10-09:00",
    "2": "09:10-10:00",
    "3": "10:20-11:10",
    "4": "11:20-12:10",
    "5": "12:20-13:10",
    "6": "13:20-14:10",
    "7": "14:20-15:10",
    "8": "15:30-16:20",
    "9": "16:30-17:20",
    "10": "17:30-18:20",
    A: "18:25-19:15",
    B: "19:20-20:10",
    C: "20:15-21:05",
    D: "21:10-22:00",
  };

  const handleSearch = async () => {
    setIsLoading(true);
    // 模擬 API 調用
    console.log("Searching for courses with query:", searchQuery);
    console.log("Selected departments:", departments);
    const filteredCourses = await getSearch(searchQuery, departments);
    console.log(filteredCourses);
    setCourses([]);
    setCourses(filteredCourses);
    setShowResults(true);
    setIsLoading(false);
    // setTimeout(() => {
    //   const filteredCourses = mockCourses.filter(
    //     (course) =>
    //       course.name.includes(searchQuery) ||
    //       course.description.includes(searchQuery) ||
    //       searchQuery.includes("資安")
    //   );
    //   setCourses(filteredCourses);
    //   setShowResults(true);
    //   setIsLoading(false);
    // }, 1000);
    // console.log("Searching for courses with query:", await getSearch("川普"));
  };

  const toggleCourseSelection = (course: Course) => {
    setSelectedCourses((prev) => {
      const isSelected = prev.find((c) => c.id === course.id);
      if (isSelected) {
        return prev.filter((c) => c.id !== course.id);
      } else {
        return [...prev, course];
      }
    });
  };

  const generateSchedule = () => {
    setIsLoading(true);
    // 模擬排課邏輯
    setTimeout(() => {
      const schedule: ScheduleSlot[] = [];
      const days = ["週一", "週二", "週三", "週四", "週五"];
      const periods = ["2", "3", "4", "6", "7", "8", "9", "A", "B"];

      // 初始化課表
      days.forEach((day) => {
        periods.forEach((period) => {
          const timeRange = periodTable[period as keyof typeof periodTable];
          schedule.push({
            day,
            period,
            timeRange,
            course: null,
          });
        });
      });

      // 安排已選課程到課表中
      selectedCourses.forEach((course) => {
        // 解析課程時間 (例如: "週一 3-4")
        const timeMatch = course.time.match(/週([一二三四五六日])\s+([0-9A-D-]+)/);
        if (timeMatch) {
          const day = timeMatch[1];
          const periodStr = timeMatch[2];
          const coursePeriods = periodStr.includes("-") ? periodStr.split("-") : [periodStr];

          coursePeriods.forEach((period) => {
            const slot = schedule.find((s) => s.day === `週${day}` && s.period === period);
            if (slot) {
              slot.course = course;
            }
          });
        }
      });

      setGeneratedSchedule(schedule);
      setIsLoading(false);
    }, 1500);
  };

  const totalCredits = selectedCourses.reduce((sum, course) => sum + course.credits, 0);
  const securityCourses = selectedCourses.filter((course) => course.host_department.includes("資安")).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 標題區域 */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-gray-900">台大智慧排課系統</h1>
          <p className="text-lg text-gray-700">依據台大節次表，為您客製化最適合的課表安排</p>
        </div>

        {/* 搜索區域 */}
        <CourseSearchBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          departments={departments}
          setDepartments={setDepartments}
          handleSearch={handleSearch}
          isLoading={isLoading}
        />

        {/* 課程列表 */}
        {showResults && (
          <CourseList
            courses={courses}
            selectedCourses={selectedCourses}
            toggleCourseSelection={toggleCourseSelection}
          />
        )}

        {/* 已選課程統計 */}
        <SelectedCoursesSummary
          selectedCourses={selectedCourses}
          totalCredits={totalCredits}
          securityCourses={securityCourses}
          isLoading={isLoading}
          toggleCourseSelection={toggleCourseSelection}
          generateSchedule={generateSchedule}
        />

        {/* 生成的課表 */}
        <ScheduleTable
          generatedSchedule={generatedSchedule}
          totalCredits={totalCredits}
          securityCourses={securityCourses}
          periodTable={periodTable}
        />
      </div>
    </div>
  );
};

export default HomePage;
