from requests import Session
import json
import os
from bs4 import BeautifulSoup
from tqdm import tqdm


class NTUClassCrawler(object):
    def __init__(self):
        self.session = Session()
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en,en-US;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://course.ntu.edu.tw',
            'Referer': 'https://course.ntu.edu.tw/search/quick?s=112-2',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        })

    def pre_load_ntu_course_website(self):
        response = self.session.get('https://course.ntu.edu.tw/search/quick?s=112-2')
        if response.status_code == 200:
            print("Pre-loading NTU course website successful.")
        else:
            print("Pre-loading NTU course website failed.")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")

    def fetch_course_list(self, semester, page_index=0, batch_size=1000):
        json_data = {
            'query': {
                'keyword': '',
                'time': [
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                ],
                'timeStrictMatch': False,
                'isFullYear': None,
                'excludedKeywords': [],
                'enrollMethods': [],
                'isEnglishTaught': False,
                'isDistanceLearning': False,
                'hasChanged': False,
                'isAdditionalCourse': False,
                'noPrerequisite': False,
                'isCanceled': False,
                'isIntensive': False,
                'semester': semester,
                'isPrecise': True,
                'departments': [],
                'isCompulsory': None,
            },
            'batchSize': batch_size,
            'pageIndex': page_index,
            'sorting': 'correlation',
        }

        response = self.session.post(
            'https://course.ntu.edu.tw/api/v1/courses/search/quick',
            json=json_data
        )
        return response

    def fetch_course_info(self, semester, course_id):
        # url = 'https://course.ntu.edu.tw/courses/112-2/40139'
        url = f'https://course.ntu.edu.tw/courses/{semester}/{course_id}'
        response = self.session.get(url)
        response.encoding = 'utf-8'
        course_info = {}
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            ul = soup.find('ul', class_='grow')
            if ul:
                lis = ul.find_all('li', recursive=False)

                for li in lis:
                    title_div = li.find('div', class_='group')
                    content_div = li.find('div', class_='prose')

                    if title_div:
                        title = title_div.get_text(strip=True)
                        if content_div:
                            content = content_div.get_text(strip=True)
                        else:
                            content = None
                        course_info[title] = content
        else:
            print(f"Error fetching course info for semester {semester}, course_id: {course_id}, : {response.status_code}")

        return course_info


if __name__ == '__main__':
    crawler = NTUClassCrawler()
    crawler.pre_load_ntu_course_website()
    for semester in ['112-1', '112-2', '113-1', '113-2']:
        total_courses = []
        for page_index in range(10):  # ntu course can only fetch 10000 courses
            response = crawler.fetch_course_list(semester, page_index, batch_size=1000)

            if response.status_code != 200:
                print(f"Error fetching course list for semester {semester}, page index: {page_index}, : {response.status_code}")
                crawler.pre_load_ntu_course_website()
                continue
            courses = response.json()['courses']
            total_courses.extend(courses)
            if len(courses) == 0:
                print(f"All courses for semester {semester} have been fetched.")
                break
            print(f"Fetched {len(courses)} courses for semester {semester}, page index: {page_index}")
        os.makedirs('data', exist_ok=True)
        with open(f'data/course_{semester}.json', 'w', encoding='utf-8') as f:
            json.dump(total_courses, f, ensure_ascii=False, indent=4)

    for semester in ['112-1', '112-2', '113-1', '113-2']:
        courses = json.load(open(f'data/course_{semester}.json', 'r', encoding='utf-8'))
        for course in tqdm(courses):
            course_serial = course["serial"]
            course_info = crawler.fetch_course_info(semester, course_serial)
            course['info'] = course_info
            os.makedirs('data', exist_ok=True)
            os.makedirs(f'data/{semester}', exist_ok=True)
            with open(f'data/{semester}/{course_serial}.json', 'w', encoding='utf-8') as f:
                json.dump(course, f, ensure_ascii=False, indent=4)

# python3 -m tools.course_crawler
