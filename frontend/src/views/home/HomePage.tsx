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

  // 模擬 API 資料 - 使用台大節次格式
  const mockCourses: Course[] = [
    {
      id: "CSIE5043",
      name: "網絡安全基礎",
      credits: 3,
      instructor: "王建民",
      time: "週一 3-4",
      location: "資訊系館 104",
      host_department: "資訊工程學系",
      capacity: 50,
      enrolled: 32,
      description: "介紹網絡安全的基本概念與實務應用，包含防火牆、入侵偵測等技術",
    },
    {
      id: "CSIE5044",
      name: "密碼學",
      credits: 3,
      instructor: "李宏毅",
      time: "週一 3-4",
      location: "資訊系館 201",
      host_department: "資訊工程學系",
      capacity: 40,
      enrolled: 28,
      description: "現代密碼學理論與加密演算法，包含對稱式與非對稱式加密",
    },
    {
      id: "CSIE5045",
      name: "系統安全",
      credits: 3,
      instructor: "張智星",
      time: "週三 8-9",
      location: "資訊系館 301",
      host_department: "資訊工程學系",
      capacity: 45,
      enrolled: 35,
      description: "作業系統與系統層級的安全機制，探討緩衝區溢位與權限控制",
    },
    {
      id: "MGMT5001",
      name: "資安法規與管理",
      credits: 3,
      instructor: "陳良弼",
      time: "週四 2-3",
      location: "管理學院 205",
      host_department: "資訊工程學系",
      capacity: 60,
      enrolled: 42,
      description: "資訊安全相關法規與風險管理，包含個資法、營業秘密法等",
    },
    {
      id: "CSIE5046",
      name: "惡意軟體分析",
      credits: 3,
      instructor: "林軒田",
      time: "週五 3-4",
      location: "資訊系館 401",
      host_department: "資訊工程學系",
      capacity: 30,
      enrolled: 25,
      description: "惡意軟體的檢測、分析與防護技術，包含靜態與動態分析方法",
    },
    {
      id: "CSIE5047",
      name: "滲透測試",
      credits: 3,
      instructor: "黃鐘揚",
      time: "週一 8-9",
      location: "資訊系館 501",
      host_department: "資訊工程學系",
      capacity: 25,
      enrolled: 20,
      description: "滲透測試方法論與實務操作，包含網頁應用程式與系統滲透",
    },
    {
      id: "CSIE5048",
      name: "數位鑑識",
      credits: 3,
      instructor: "呂學一",
      time: "週二 A-B",
      location: "資訊系館 601",
      host_department: "資訊工程學系",
      capacity: 35,
      enrolled: 18,
      description: "數位證據蒐集與分析技術，包含檔案系統與網路封包分析",
    },
    {
      id: "CSIE5049",
      name: "區塊鏈安全",
      credits: 3,
      instructor: "廖世偉",
      time: "週三 6-7",
      location: "資訊系館 102",
      host_department: "資訊工程學系",
      capacity: 40,
      description: "區塊鏈技術與智能合約安全，探討去中心化應用的安全議題",
    },
  ];

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
