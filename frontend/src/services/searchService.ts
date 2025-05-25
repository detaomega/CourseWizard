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

interface ApiResponse {
  results: Array<{
    id: string;
    identifier: string;
    name: string;
    credits: number;
    teacher_name: string;
    host_department: string;
    course_overview: string;
    time_slots: Array<{
      weekday: number;
      period: string;
      classroom: string;
    }>;
  }>;
}

const weekdayMap: { [key: number]: string } = {
  1: '週一',
  2: '週二', 
  3: '週三',
  4: '週四',
  5: '週五',
  6: '週六',
  7: '週日'
};

const formatTimeSlots = (timeSlots: Array<{ weekday: number; period: string; classroom: string }>): string => {
  if (!timeSlots || timeSlots.length === 0) return 'N/A';
  
  const groupedByDay: { [key: string]: string[] } = {};
  
  timeSlots.forEach(slot => {
    const day = weekdayMap[slot.weekday] || `週${slot.weekday}`;
    if (!groupedByDay[day]) {
      groupedByDay[day] = [];
    }
    groupedByDay[day].push(slot.period);
  });
  
  const formattedTimes = Object.entries(groupedByDay).map(([day, periods]) => {
    const sortedPeriods = periods.sort();
    return `${day} ${sortedPeriods.join('-')}`;
  });
  
  return formattedTimes.join(', ');
};

const getLocation = (timeSlots: Array<{ weekday: number; period: string; classroom: string }>): string => {
  if (!timeSlots || timeSlots.length === 0) return 'N/A';
  
  return timeSlots[0].classroom || 'N/A';
};

export const transformApiDataToCourses = (apiData: ApiResponse): Course[] => {
  if (!apiData.results || !Array.isArray(apiData.results)) {
    return [];
  }
  
  return apiData.results.map(item => ({
    id: item.identifier || item.id,
    name: item.name,
    credits: item.credits || 0,
    instructor: item.teacher_name,
    time: formatTimeSlots(item.time_slots),
    location: getLocation(item.time_slots),
    host_department: item.host_department,
    capacity: 40, // API 中沒有此資訊，使用預設值
    enrolled: undefined, // API 中沒有此資訊
  }));
};

export const getSearch = async (query: string): Promise<Course[]> => {
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
     
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const apiData: ApiResponse = await response.json();
    console.log(transformApiDataToCourses(apiData))
    return transformApiDataToCourses(apiData);
  } catch (error) {
    console.error('Error fetching search results:', error);
    return [];
  }
};