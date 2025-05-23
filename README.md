# CourseWizard

# Enviroment Setup
## 1. Create a python virtual environment
```
python -m venv venv
```
## 2. Activate the virtual environment
```
source venv/bin/activate
```

## 3. Install the required packages
```
pip install -r requirements.txt
```

# Crawl the courses data:
```
python3 -m tools.course_crawler
```
This will create a folder named `data` in the root directory, which contains the crawled course information data.

