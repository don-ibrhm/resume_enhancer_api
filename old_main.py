### --- --- --- IMPORTS & SETUP

import utils.utils_file
import utils.extract_resume
from utils.dataclass import ResumeModel, BasicInfoModel, WorkExperienceModel, EducationModel, ProjectExperienceModel
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



load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
encoding = tiktoken.get_encoding("cl100k_base")

# If backup_folder directory does not exist, create it
if not os.path.exists("backup_folder"):
    os.makedirs("backup_folder")
    
### FUNCTIONS
from pydantic import BaseModel, ValidationError

# ---------------------------- BASIC INFO ------------------------------------------        
def update_basic_info(resume_data: ResumeModel, updated_basic_info_dict: dict) -> ResumeModel:
    """
    This function takes a ResumeModel instance representing the existing resume data 
    and a dictionary representing the updated basic info.
    It validates and converts the dictionary to a BasicInfoModel instance,
    updates the basic info in the resume data, and returns the updated ResumeModel instance.
    """
    try:
        # Validate and convert the updated_basic_info_dict to a BasicInfoModel instance
        updated_basic_info = BasicInfoModel(**updated_basic_info_dict)
        
        # Update the basic_info section of the resume data with the updated basic info
        resume_data.basic_info = updated_basic_info
        
    except ValidationError as e:
        print(f"Validation Error: {e}")
    

# ---------------------------- OBJECTIVE ------------------------------------------
def create_objective_openai(current_objective, experience, skills):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                              temperature=0)

    system_template = ("""Create 2-3 lines resume objective using the following information. DO not mention the word objective.""")

    system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template)

    human_template = """Current Objective: {current_objective}
Experience: {experience}
Skills: {skills}"""

    human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

    # get a chat completion from the formatted messages
    response = chat(
            chat_prompt.format_prompt(
                current_objective=current_objective,
                experience=experience,
                skills=skills
            ).to_messages()
        )

    return response.content

def enhance_objective(resume_data: ResumeModel) -> ResumeModel:
    """
    This function takes a ResumeModel instance representing the existing resume data.
    It enhances the objective statement using the experience and skills in the resume data
    and returns the updated ResumeModel instance.
    """
    
    # Extract the current objective, experience, and skills from the resume data
    current_objective = resume_data.objective
    experiences = resume_data.work_experience or []
    skills = resume_data.skills or []
    
    # Identify key skills, roles, and responsibilities from the experience and skills sections
    key_skills = set()
    key_roles = set()
    for exp in experiences:
        key_roles.add(exp.job_title.lower())
        # Here you can also extract other important keywords from job_summary
    for skill in skills:
        key_skills.add(skill.lower())
    
    experience = ".".join(key_roles)
    skills = ".".join(key_skills)

    # Construct the enhanced objective statement
    enhanced_objective = create_objective_openai(current_objective, experience, skills)

    # Update the objective in the resume data with the enhanced objective
    resume_data.objective = enhanced_objective
    
    return resume_data

# ---------------------------- WORK EXPERIENCE ------------------------------------------

def create_job_summary_openai(current_job, skills):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                              temperature=0)

    system_template = ("""Create 1-2 lines job summary using the following information""")

    system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template)

    human_template = """Current Job summary : {job_summary}
Current Job title: {job_title}
Skills: {skills}"""

    human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )       
    
    # get a chat completion from the formatted messages
    response = chat(
                chat_prompt.format_prompt(
                        job_summary=current_job.job_summary,
                        job_title=current_job.job_title,
                        skills=skills
                        ).to_messages()
                )
    return response.content
    

def enhance_experience(resume_data: ResumeModel) -> ResumeModel:
    """
    This function takes a ResumeModel instance representing the existing resume data.
    It enhances the experience section using the objective and skills in the resume data
    and returns the updated ResumeModel instance.
    """
    
    # Generate job_summary for each experience in work_experience, using current job_summary, job_title and skills. Use function create_job_summary_openai
    enhanced_experience = []
    for exp in resume_data.work_experience:
        # Identify key skills from the skills section
        key_skills = set()
        for skill in resume_data.skills:
            key_skills.add(skill.lower())
        skills = ".".join(key_skills)
        
        # Construct the enhanced job summary
        enhanced_job_summary = create_job_summary_openai(exp, skills)
        
        # Update the job summary in the experience with the enhanced job summary
        exp.job_summary = enhanced_job_summary

        # Update the experience in the resume data with the updated experience
        enhanced_experience.append(exp)

    resume_data.work_experience = enhanced_experience

    return resume_data
    

# ---------------------------- EDUCATION ------------------------------------------
def update_education(resume_data: ResumeModel, updated_education_list: List) -> ResumeModel:
    """
    This function takes a ResumeModel instance representing the existing resume data 
    and a list of dictionaries representing the updated education.
    It validates and converts the list of dictionaries to a list of EducationModel instances,
    updates the education section in the resume data, and returns the updated ResumeModel instance.
    """
    try:
        # Validate and convert the updated_education_list to a list of EducationModel instances
        updated_education = [EducationModel(**edu) for edu in updated_education_list]
        
        # Update the education section of the resume data with the updated education
        resume_data.education = updated_education
        
    except ValidationError as e:
        print(f"Validation Error: {e}")
    
    return resume_data


# ---------------------------- PROJECT EXPERIENCE ------------------------------------------

# project_experience (including project_name, project_description),

# Generate project_description for each project in project_experience, using current project_name and project_description.
def create_project_description_openai(project_name, project_description, skills):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                      temperature=0)

    system_template = (
        """Create 1 line project description using the following information""")

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template)

    human_template = """Current Project description : {project_description}
Current Project name: {project_name}
Skills: {skills}"""

    human_message_prompt = HumanMessagePromptTemplate.from_template(
        human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    # get a chat completion from the formatted messages
    response = chat(
        chat_prompt.format_prompt(

            project_description=project_description,
            project_name=project_name,
            skills=skills
        ).to_messages()
    )
    return response.content


# Create two project experiences, if project_experience is empty, create new project_experience
def create_full_project_experience_openai(skills):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                      temperature=0)

    # project_experience (including project_name, project_description),
    system_template = ("""Create two "project_experience" using the following information. "project_experience" is list of dict, each dict having keys "project_name" and "project_description".env
output_format : 
{{                       
"project_experience":{{      
[
{{
    "project_name": "project_name_1",    
    "project_description": "project_description_1"                       
}},
{{
"project_name": "project_name_2",
"project_description": "project_description_2"
}}
]}}
}}""")

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template)

    human_template = """Skills: {skills}"""

    human_message_prompt = HumanMessagePromptTemplate.from_template(
        human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    # get a chat completion from the formatted messages
    response = chat(
        chat_prompt.format_prompt(
            skills=skills
        ).to_messages()
    )
    return response.content


def enhance_project(resume_data: ResumeModel) -> ResumeModel:
    """
    This function takes a ResumeModel instance representing the existing resume data.
    It enhances the project_experience section using the project_name and project_description in the resume data
    and returns the updated ResumeModel instance.
    """

    key_skills = set()
    for skill in resume_data.skills:
        key_skills.add(skill.lower())
    skills = ".".join(key_skills)

    # if project_experience is empty, return the resume_data
    if not resume_data.project_experience or len(resume_data.project_experience) == 0:
        # Create new project_experience
        generated_experience = json.loads(
            create_full_project_experience_openai(skills))["project_experience"]
        resume_data.project_experience = generated_experience
        return resume_data

    else:
        # Generate project_description for each project in project_experience, using current project_name and project_description. Use function create_project_description_openai
        enhanced_projects = []
        print("-------", resume_data)
        for project in resume_data.project_experience:
            # Construct the enhanced project description
            enhanced_project_description = create_project_description_openai(
                project.project_name, project.project_description, skills)
                # project["project_name"], project["project_description"], skills)    ## TODO: check if this works 

            # Update the project description in the project with the enhanced project description
            project["project_description"] = enhanced_project_description           ## TODO: check if this works

            # Update the project in the resume data with the updated project
            enhanced_projects.append(project)

        resume_data.project_experience = enhanced_projects

        return resume_data

# ---------------------------- SKILLS ------------------------------------------

def create_full_skills_openai(experience, projects):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                      temperature=0)

    system_template = ("""You are a helpful and obedient bot. Write impressive skills for a work resume using the following information. The output format is a dict with key "skills" and value as list of enhanced skills.
You should never mention the word 'Enhanced' at the beginning of these skills. 
output_format :
{{
"skills": [ 
"generated skill 1",
"generated skill 2,
...
]
}}""")

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template)

    human_template = """Experience: {experience}
Projects: {projects}"""

    human_message_prompt = HumanMessagePromptTemplate.from_template(
        human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    # get a chat completion from the formatted messages
    response = chat(
        chat_prompt.format_prompt(
            experience=experience,
            projects=projects
        ).to_messages()
    )

    return response.content

def generate_enhanced_skills_openai(skills):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                      temperature=0)

    system_template = ("""Enhance the elow listed skills using the following information. The output format is a dict with key "skills" and value as list of enhanced skills.
Do not mentione the word enhanced.
output_format :
{{
"skills": [
"enhanced skill 1",
"enhanced skill 2,
...
]
}}""")

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template)

    human_template = """Existing skills: {skills}"""

    human_message_prompt = HumanMessagePromptTemplate.from_template(
        human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    # get a chat completion from the formatted messages
    response = chat(
        chat_prompt.format_prompt(
            skills=skills
        ).to_messages()
    )

    return response.content    

def enhance_skills(resume_data: ResumeModel) -> ResumeModel:
    """Enhance or generate skills section of resume_data using skills in work_experience and project_experience"""
    # Extract the skills from the skills section


    if len(resume_data.skills) == 0:
        # Generate skills using JOB_TITLE AND JOB_SUMMARY from work_experience and project_name and project_description from project_experience

        # Extract the job titles and job summaries from the work experience
        key_roles = set()
        for exp in resume_data.work_experience:
            key_roles.add(exp.job_title.lower())
            # Here you can also extract other important keywords from job_summary
        experience = ".".join(key_roles)

        # Extract the project names and project descriptions from the project experience
        key_projects = set()
        for project in resume_data.project_experience:
            key_projects.add(project.project_name.lower())
            # Here you can also extract other important keywords from project_description
        projects = ".".join(key_projects)

        # Construct the enhanced skills
        enhanced_skills = create_full_skills_openai(
            experience, projects)
        
        enhanced_skills = json.loads(enhanced_skills)["skills"]

        # Update the skills in the resume data with the enhanced skills
        resume_data.skills = enhanced_skills

        return resume_data
    else:
        key_skills = set()
        for skill in resume_data.skills:
            key_skills.add(skill.lower())
        skills = ".".join(key_skills)
        # enhance existing skills.
        
        enhanced_skills = generate_enhanced_skills_openai(skills)

        enhanced_skills = json.loads(enhanced_skills)["skills"]

        # Update the skills in the resume data with the enhanced skills
        resume_data.skills = enhanced_skills

        return resume_data


class ResumeText(BaseModel):
    text: str

### API

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

@app.get('/set_example/')
def _set_example():
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
    resume_dict = resume_model.dict()

    # This will save the very first json file in the backup_folder
    json_file_name = utils.utils_file.convert_filepath_to_json(uploaded_file)
    # save ans as json locally
    with open(json_file_name, "w") as f:
        json.dump(resume_dict, f)


@app.get('/enhance-objective/')
def _enhance_objective():
    try:
        enhance_objective(resume_model)
        return {'status': 'success',
                'response': resume_model.dict()['objective']}
    except Exception as e:
        return {'status': 'error',
                'response': e}

@app.get('/enhance-experience/')
def _enhance_experience():
    try:
        enhance_experience(resume_model)
        work_experiences = resume_model.dict()['work_experience']
        f_work_experiences = [{
            'company': exp["company"],
            'jobTitle': exp["job_title"],
            'date': exp["duration"],
            'descriptions': exp["job_summary"].split('\n'),
        } for exp in work_experiences]
        return {'status': 'success',
                'response': f_work_experiences[0]}
    except Exception as e:
        return {'status': 'error',
                'response': e.args}

@app.get('/enhance-projects/')
def _enhance_project():
    reach = '0'
    # try:
    enhance_project(resume_model)
    reach = '1'
    projects = resume_model.dict()['project_experience']
    print(projects)
    reach = '2'
    # return {'response': projects}
    f_projects = [{
        'project': proj["project_name"],
        'date': "Add Date",
        'descriptions': proj["project_description"].split('\n'),
    } for proj in projects]
    reach = '3'
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
                'response': resume_model.dict()['skills']}
    except Exception as e:
        return {'status': 'error',
                'response': e}

@app.post('/update/')
def _update_resume(resume: Resume):
    try:
        print(resume)
        resume_dict = resume.dict()
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
    try:
        text = utils.utils_file.process_clean_text(resume_text.text)

        # USe openai to extract the data
        ans = utils.extract_resume.extract_data_new(text)
        print("\n\n-------\n\n", ans)
        print("\n\n-------\n\n", ans['education'])
        if not isinstance(ans['education'], list):
            ans['education'] = [ans['education']]
        # If any field of ans is empty, replace it with "" according to the ResumeModel
        new_resume_model = ResumeModel(**ans)
        for key in resume_model.model_dump().keys():
            setattr(resume_model, key, getattr(new_resume_model, key))

        return "Upload complete"
    except Exception as e:
        return "Error: " + str(e)


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
    return resume_model.dict()

# resume_model = ResumeModel(
        #     basic_info = BasicInfoModel(
        #         first_name=resume_dict['profile']['name'].split()[0],
        #         last_name = resume_dict['profile']['name'].split()[-1],
        #         full_name = resume_dict['profile']['name'],
        #         email = resume_dict['profile']['email'],
        #         phone_number = resume_dict['profile']['phone'],
        #         location = resume_dict['profile']['location'],
        #         portfolio_website_url = resume_dict['profile']['url'],
        #         linkedin_url = "",
        #         github_main_page_url = ""
        #     ),
        #     objective = resume_dict['profile']['summary'],
        #     work_experience = [WorkExperienceModel(
        #         job_title = work_experience['jobTitle'],
        #         company = work_experience['company'],
        #         location = "",
        #         duration = work_experience['date'],
        #         job_summary = '. '.join(work_experience['descriptions']),
        #     ) for work_experience in resume_dict['workExperiences']],
        #     education = [EducationModel(
        #         university = education['school'],
        #         education_level = education['degree'],
        #         graduation_year = education['date'].split()[-1],
        #         graduation_month = education['date'].split()[0],
        #         majors = '. '.join(education['descriptions']),
        #         GPA = education['gpa'],
        #     ) for education in resume_dict['educations']],
        #     project_experience = [ProjectExperienceModel(
        #         project_name = project['project'],
        #         project_description = '. '.join(project['descriptions'])
        #     ) for project in resume_dict['projects']],
        #     skills = resume_dict['skills']
        # )