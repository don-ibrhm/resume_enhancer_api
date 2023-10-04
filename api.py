import utils.utils_file
import utils.extract_resume
from utils.dataclass import ResumeText, ResumeModel, BasicInfoModel, WorkExperienceModel, EducationModel, ProjectExperienceModel
from utils.mirror_class import Resume
import json
import tiktoken
import openai 
from dotenv import load_dotenv
import os
import logging
import shutil
import json

from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from functions import *

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
encoding = tiktoken.get_encoding("cl100k_base")

# If backup_folder directory does not exist, create it
if not os.path.exists("backup_folder"):
    os.makedirs("backup_folder")

app = FastAPI()

# allowed domains (currently: all '*')
origins = [
    "*",
]

# allow access with cors
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

# API Methods:
## All enhance methods take the latest version of the resume from the front end, and enhance the requested portion
@app.post('/enhance-objective/')
def _enhance_objective(resume: Resume):
    # Get localised resume model, then enhance
    resume_model = parse_resume(resume)
    enhance_objective(resume_model)
    return {'status': 'success',
            'response': resume_model.model_dump()['objective']}

@app.post('/enhance-experience/')
def _enhance_experience(resume: Resume):
    # Get localised resume model, then enhance
    resume_model = parse_resume(resume)
    enhance_experience(resume_model)
    # Revert to OpenResume's resume model for work experiences
    work_experiences = resume_model.model_dump()['work_experience']
    f_work_experiences = [{
        'company': exp["company"],
        'jobTitle': exp["job_title"],
        'date': exp["duration"],
        'descriptions': exp["job_summary"].split('\n'),
    } for exp in work_experiences]
    return {'status': 'success',
            'response': f_work_experiences}

@app.post('/enhance-projects/')
def _enhance_project(resume: Resume):
    # Get localised resume model, then enhance
    resume_model = parse_resume(resume)
    enhance_project(resume_model)
    # Revert to OpenResume's resume model for projects
    projects = resume_model.model_dump()['project_experience']
    f_projects = [{
        'project': proj["project_name"],
        'date': "Add Date",
        'descriptions': proj["project_description"].split('\n'),
    } for proj in projects]
    return {'status': 'success',
            'response': f_projects}

@app.post('/enhance-skills')
def _enhance_skills(resume: Resume):
    # Get localised resume model, then enhance
    resume_model = parse_resume(resume)
    enhance_skills(resume_model)
    # Try to clear the enhanced skills to remove repeated starting word ('enhanced'), and format, else return as is
    enhanced_skills = resume_model.model_dump()['skills']
    try:
        if len({skill.split()[0] for skill in skills}) == 1:
            skills = [' '.join(skill.split()[1:]) for skill in enhanced_skills]
            skills = [skill + '.'  if not skill.endswith('.') else skill for skill in skills]
            skills = [skill[0].upper() + skill[1:] for skill in skills]
        return {'status': 'success',
                'response': skills}
    except Exception as e:
        return {'status': 'success',
                'response': resume_model.model_dump()['skills']}
    
# Function to get localised resume model from OpenResume's resume model
def parse_resume(resume: Resume):
    resume_dict = resume.model_dump()
    # As ['profile']['name'] will be split, give it a value in case it's empty, to avoid errors when .split() and indexed
    if not resume_dict['profile']['name']:
        resume_dict['profile']['name'] = '-'
    print(resume_dict)

    # Populate each of the attributes of the localized resume model (and thier attributes) with the equivalent or approximate from OpenResume's resume model
    resume_model = ResumeModel(
        basic_info = BasicInfoModel(
            first_name = ' '.join(resume_dict['profile']['name'].split()[:-1]),
            last_name = resume_dict['profile']['name'].split()[-1],
            full_name = resume_dict['profile']['name'],
            email = resume_dict['profile']['email'],
            phone_number = resume_dict['profile']['phone'],
            location = resume_dict['profile']['location'],
            portfolio_website_url = resume_dict['profile']['url'],
            linkedin_url = "",
            github_main_page_url = ""
        ),
        objective = resume_dict['profile']['summary'],
        work_experience = [WorkExperienceModel(
                job_title = work_experience['jobTitle'],
                company = work_experience['company'],
                location = "",
                duration = work_experience['date'],
                job_summary = '. '.join(work_experience['descriptions']),
            ) for work_experience in resume_dict['workExperiences']],
        education = [EducationModel(
                university = education['school'],
                education_level = education['degree'],
                graduation_year = "",
                graduation_month = education['date'],
                majors = '. '.join(education['descriptions']),
                GPA = education['gpa'],
            ) for education in resume_dict['educations']],
        project_experience = [ProjectExperienceModel(
                project_name = project['project'],
                project_description = '. '.join(project['descriptions'])
            ) for project in resume_dict['projects']],
        skills = resume_dict['skills']['descriptions']
    )
    return resume_model


# Currently Defunct
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

# OpenAI may not completely respond as desired, 
# Solutions so far being:   casting as the correct types, 
#                           or extracting the useful information 
#                           or leaving blank
def correct_response(res: dict):
    if not isinstance(res['basic_info'], dict):
        print("-- Issue: with how basic_info was formed by ai function")
        print("Before:", res['basic_info'])
        res['basic_info'] = {
            'first_name': "",
            'last_name': "",
            'full_name': "",
            'email': "",
            'phone_number': "",
            'location': "",
            'portfolio_website_url': "",
            'linkedin_url': "",
            'github_main_page_url': "",
        }
        print("Now:", res['basic_info'])
    if not isinstance(res['objective'], str):
        print("-- Issue: with how objective was formed by ai function")
        print("Before:", res['objective'])
        if isinstance(res['objective'], dict) and res['objective'].keys():
            res['objective'] = res['objective'][list(res['objective'].keys())[0]]
        else:
            res['objective'] = str(res['objective'])
        print("Now:", res['objective'])
    if not isinstance(res['work_experience'], list):
        print("-- Issue: with how work_experience was formed by ai function")
        print("Before:", res['work_experience'])
        res['work_experience'] = [{
            'job_title': "",
            'company': "",
            'location': "",
            'duration': "",
            'job_summary': "",
        }]
        print("Now:", res['work_experience'])
    else:
        for i, work in enumerate(res['work_experience']):
            if not isinstance(work, dict):
                print("--- Issue:", res['work_experience'][i])
                res['work_experience'][i] = {
                    'job_title': "",
                    'company': "",
                    'location': "",
                    'duration': "",
                    'job_summary': "",
                }
    if not isinstance(res['education'], list):
        print("-- Issue: with how education was formed by ai function")
        print("Before:", res['education'])
        res['education'] = [{
            'university': "",
            'education_level': "",
            'graduation_year': "",
            'graduation_month': "",
            'majors': "",
            'GPA': "",
        }]
        print("Now:", res['education'])
    else:
        for i, edu in enumerate(res['education']):
            if not isinstance(edu, dict):
                print("--- Issue:", res['education'][i])
                res['education'][i] = {
                    'university': "",
                    'education_level': "",
                    'graduation_year': "",
                    'graduation_month': "",
                    'majors': "",
                    'GPA': "",
                }
    if not isinstance(res['project_experience'], list):
        print("-- Issue: with how project_experience was formed by ai function")
        print("Before:", res['project_experience'])
        res['project_experience'] = [{
            'project_name': "",
            'project_description': "",
        }]
        print("Now:", res['project_experience'])
    else:
        for i, project in enumerate(res['project_experience']):
            if not isinstance(project, dict):
                print("--- Issue:", res['project_experience'][i])
                res['project_experience'][i] = {
                    'project_name': "",
                    'project_description': "",
                }
    if not isinstance(res['skills'], list):
        print("-- Issue: with how skills was formed by ai function")
        print("Before:", res['skills'])
        if isinstance(res['skills'], dict):
            skills = []
            for key in res['skills']:
                if isinstance(res['skills'][key], list):
                    skills.extend(res['skills'][key])
                else:
                    skills.append(str(res['skills'][key]))
            res['skills'] = skills
        else:
            res['skills'] = [""]
        print("Now:", res['skills'])


# Takes raw text extracted from the docx/pdf in the front end, and parses with AI, then returns resume in OpenResume's format
# Used for the initial parsing
@app.post("/upload-text/")
def _upload_text_only(resume_text: ResumeText):
    text = utils.utils_file.process_clean_text(resume_text.text)

    # Use OpenAI to extract the data
    response = utils.extract_resume.extract_data_new(text)
    print(response)
    correct_response(response)

    # catching mistypes attributes and casting them to the correct type
    # if not isinstance(ans['work_experience'], list):
    #     print("-- Issue: with how work_experience was formed by ai function")
    #     ans['work_experience'] = [ans['work_experience']]
    # if not isinstance(ans['education'], list):
    #     print("-- Issue: with how education was formed by ai function")
    #     ans['education'] = [ans['education']]
    # if not isinstance(ans['project_experience'], list):
    #     print("-- Issue: with how project_experience was formed by ai function")
    #     ans['project_experience'] = [ans['project_experience']]
    # if not isinstance(ans['skills'], list):
    #     print("-- Issue: with how skills was formed by ai function")
    #     ans['skills'] = [ans['skills']]
    #NOTE: Is this a #TODO? Lol,: If any field of ans is empty, replace it with "" according to the ResumeModel; may Allah laugh with me
    # Turn it into a localized resume model
    if not response:
        print("Failed to get a valid response with 3 attempts")
        return None
    resume_model = ResumeModel(**response)
    print(resume_model)
    # Updating resume_model on disk (not necessary for basic front end functionlity, but maybe for testing inshaAllah
    # for key in resume_model.model_dump().keys():
    #     setattr(resume_model, key, getattr(new_resume_model, key))
    # Revert it to OpenResume's resume model and return
    return get_resume(resume_model)

# Currently unused, thank God, transferring files between front and back end isn't the simplest imo..
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
def pass_resume():
    return get_resume(resume_model)

# Localalized resume model -> OpenResume resume model
def get_resume(resume_model):
    # print("\n\n------- getting resume model\n\n", resume_model.model_dump())
    # Populate OpenResume's resume model with its equivalent or approximate from the localized resume model
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
            "featuredSkills": [
                {
                    'skill': "",
                    'rating': 0,
                },
            ],
            "descriptions": resume_model.skills
        },
        "custom": {
            "descriptions": [""]
        }
    }
    return open_resume_model

@app.get('/get-internal-resume/')
def _get_resume():
    return resume_model.model_dump()

@app.get("/")
def _ping():
    return "XD"