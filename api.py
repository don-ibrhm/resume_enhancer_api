### --- --- --- IMPORTS & SETUP

import utils.utils_file
import utils.extract_resume
from utils.dataclass import ResumeText, ResumeModel, BasicInfoModel, WorkExperienceModel, EducationModel, ProjectExperienceModel
from utils.mirror_class import Resume
from langchain.chat_models import ChatOpenAI
import json
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
import tiktoken
import openai 
from dotenv import load_dotenv
import os
import logging
import shutil

import json
from typing import List

from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from functions import *

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
encoding = tiktoken.get_encoding("cl100k_base")

# If backup_folder directory does not exist, create it
if not os.path.exists("backup_folder"):
    os.makedirs("backup_folder")

app = FastAPI()
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# @app.get('/set_example/')
# def _set_example():
## MAIN
uploaded_file = "sample_resume/Acting Manager_Learning.pdf"

if uploaded_file.endswith(".pdf"):
    text = utils.utils_file.parse_pdf(uploaded_file)
elif uploaded_file.endswith(".docx"):
    text = utils.utils_file.parse_docx(uploaded_file)

# the is the raw text after parsing 
text = utils.utils_file.process_clean_text(text)

# USe openai to extract the data
ans = utils.extract_resume.extract_data_new(text)

# If any field of ans is empty, replace it with "" according to the ResumeModel
resume_model = ResumeModel(**ans)

# Convert the resume_model to a dictionary
resume_dict = resume_model.model_dump()

# This will save the very first json file in the backup_folder
json_file_name = utils.utils_file.convert_filepath_to_json(uploaded_file)
# save ans as json locally
with open(json_file_name, "w") as f:
    json.dump(resume_dict, f)
print("\n\n\n[1] Running whenever?\n\n\n")
# return "done!"


@app.get('/enhance-objective/')
def _enhance_objective():
    try:
        enhance_objective(resume_model)
        return {'status': 'success',
                'response': resume_model.model_dump()['objective']}
    except Exception as e:
        return {'status': 'error',
                'response': e}

@app.get('/enhance-experience/')
def _enhance_experience():
    try:
        enhance_experience(resume_model)
        work_experiences = resume_model.model_dump()['work_experience']
        f_work_experiences = [{
            'company': exp["company"],
            'jobTitle': exp["job_title"],
            'date': exp["duration"],
            'descriptions': exp["job_summary"].split('\n'),
        } for exp in work_experiences]
        return {'status': 'success',
                'response': f_work_experiences}
    except Exception as e:
        return {'status': 'error',
                'response': e.args}

@app.get('/enhance-projects/')
def _enhance_project():
    # try:
    enhance_project(resume_model)
    projects = resume_model.model_dump()['project_experience']
    print(projects)
    # return {'response': projects}
    f_projects = [{
        'project': proj["project_name"],
        'date': "Add Date",
        'descriptions': proj["project_description"].split('\n'),
    } for proj in projects]
    return {'status': 'success',
            'response': f_projects}
    # except Exception as e:
    #     return {'status': 'error',
    #             'response': str(e) + f" - {reach}"}

@app.get('/enhance-skills/')
def _enhance_skill():
    try:
        enhance_skills(resume_model)
        return {'status': 'success',
                'response': resume_model.model_dump()['skills']}
    except Exception as e:
        return {'status': 'error',
                'response': e}

@app.post('/update/')
def _update_resume(resume: Resume):
    try:
        print(resume)
        resume_dict = resume.model_dump()
        resume_model.basic_info = BasicInfoModel(
            first_name = resume_dict['profile']['name'].split()[0],
            last_name = resume_dict['profile']['name'].split()[-1],
            full_name = resume_dict['profile']['name'],
            email = resume_dict['profile']['email'],
            phone_number = resume_dict['profile']['phone'],
            location = resume_dict['profile']['location'],
            portfolio_website_url = resume_dict['profile']['url'],
            linkedin_url = "",
            github_main_page_url = ""
        )
        resume_model.objective = resume_dict['profile']['summary']
        resume_model.work_experience = [WorkExperienceModel(
                job_title = work_experience['jobTitle'],
                company = work_experience['company'],
                location = "",
                duration = work_experience['date'],
                job_summary = '. '.join(work_experience['descriptions']),
            ) for work_experience in resume_dict['workExperiences']]
        resume_model.education = [EducationModel(
                university = education['school'],
                education_level = education['degree'],
                graduation_year = education['date'].split()[-1],
                graduation_month = education['date'].split()[0],
                majors = '. '.join(education['descriptions']),
                GPA = education['gpa'],
            ) for education in resume_dict['educations']]
        resume_model.project_experience = [ProjectExperienceModel(
                project_name = project['project'],
                project_description = '. '.join(project['descriptions'])
            ) for project in resume_dict['projects']],
        resume_model.skills = resume_dict['skills']
        print(resume_model)
        return "Success(?!?)"
    except Exception as e:
        return {e}

@app.post("/upload-text/")
def _upload_text_only(resume_text: ResumeText):
    # try:
        text = utils.utils_file.process_clean_text(resume_text.text)

        # USe openai to extract the data
        ans = utils.extract_resume.extract_data_new(text)
        print("\n\n-------\n\n", ans)
        # print("\n\n-------\n\n", ans['education'])
        if not isinstance(ans['work_experience'], list):
            print("Issue with how work_experience is stored")
            ans['work_experience'] = [ans['work_experience']]
        if not isinstance(ans['education'], list):
            print("Issue with how education is stored")
            ans['education'] = [ans['education']]
        if not isinstance(ans['project_experience'], list):
            print("Issue with how project_experience is stored")
            ans['project_experience'] = [ans['project_experience']]
        if not isinstance(ans['skills'], list):
            print("Issue with how skills is stored")
            ans['skills'] = [ans['skills']]
        # If any field of ans is empty, replace it with "" according to the ResumeModel
        new_resume_model = ResumeModel(**ans)
        for key in resume_model.model_dump().keys():
            setattr(resume_model, key, getattr(new_resume_model, key))
        print("\n\n------- uploading resume model\n\n", resume_model.model_dump())
        return "Upload complete"
    # except Exception as e:
    #     print("--------\n\n\nError:", str(e))
    #     return "Error: " + str(e)


@app.post("/upload-file/")
def _upload_pdf_or_docx(file: UploadFile):
    global resume_model
    upload_dir = "uploaded_resumes"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    # Combine the directory path and the file name to get the full path
    file_path = os.path.join(upload_dir, file.filename)

    # Open the file for writing in binary mode
    with open(file_path, "wb") as f:
        # Iterate through the file chunks and write them to the file
        shutil.copyfileobj(file.file, f)
    if file_path.endswith(".pdf"):
        text = utils.utils_file.parse_pdf(file_path)
    elif file_path.endswith(".docx"):
        text = utils.utils_file.parse_docx(file_path)
    else:
        return "File must be pdf or docx"

    # the is the raw text after parsing 
    text = utils.utils_file.process_clean_text(text)

    # USe openai to extract the data
    ans = utils.extract_resume.extract_data_new(text)

    # If any field of ans is empty, replace it with "" according to the ResumeModel
    resume_model = ResumeModel(**ans)
    
    
@app.get("/get-resume/")
def _get_resume():
    print("\n\n------- getting resume model\n\n", resume_model.model_dump())
    open_resume_model = {
        "profile": {
            "name": resume_model.basic_info.full_name,
            "email": resume_model.basic_info.email,
            "phone": resume_model.basic_info.phone_number,
            "url": resume_model.basic_info.portfolio_website_url,
            "summary": resume_model.objective,
            "location": resume_model.basic_info.location
        },
        "workExperiences": [
            {
            "company": work_experience.company,
            "jobTitle": work_experience.job_title,
            "date": work_experience.duration,
            "descriptions": work_experience.job_summary.split('\n')
            } for work_experience in resume_model.work_experience
        ],
        "educations": [
            {
            "school": education.university,
            "degree": education.education_level,
            "date": f"{education.graduation_month} {education.graduation_year}",
            "gpa": education.GPA,
            "descriptions": education.majors.split('\n')
            } for education in resume_model.education
        ],
        "projects": [
            {
            "project": project.project_name,
            "date": "", # TODO: 
            "descriptions": project.project_description.split('\n')
            } for project in resume_model.project_experience
        ],
        "skills": {
            "descriptions": resume_model.skills
        }
    }
    return open_resume_model

@app.get('/get-internal-resume/')
def _get_resume():
    return resume_model.model_dump()