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
        resume_data.project_experience = generated_experience if not isinstance(generated_experience, tuple) else generated_experience[0]
        return resume_data

    else:
        # Generate project_description for each project in project_experience, using current project_name and project_description. Use function create_project_description_openai
        enhanced_projects = []
        # print("-------|", resume_data.project_experience)
        if isinstance(resume_data.project_experience, tuple):
            print("it was a tuple... somehow...\n\n\n")
            resume_data.project_experience = resume_data.project_experience[0]
        for project in resume_data.project_experience:
            print("---||", project)
            # Construct the enhanced project description
            enhanced_project_description = create_project_description_openai(
                project.project_name, project.project_description, skills)
                # project["project_name"], project["project_description"], skills)    ## TODO: check if this works 

            # Update the project description in the project with the enhanced project description
            project.project_description = enhanced_project_description           ## TODO: check if this works

            # Update the project in the resume data with the updated project
            enhanced_projects.append(project)

        resume_data.project_experience = enhanced_projects

        return resume_data

# ---------------------------- SKILLS ------------------------------------------

def create_full_skills_openai(experience, projects):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                      temperature=0)

    system_template = (
        """May Allah bless you for your work. Please write impressive skills for a work resume that could immediately impress and please a potential employer.
        Please analyze and use the following information about the person's work experiences and the project's he's completed. 
        The required output format is a dict with the key 'skills', whose values are a list of those skills you generate.
        Please do not be repetitive in wording, and may Allah guide you to what's best. 
        output_format :
        {{
        "skills": [ 
        "Generated skill",
        "Another generated skill",
        ... # and so on inshaAllah
        ]
        }}""")

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template)

    human_template = """Work experiences: {experience}
                        Project history: {projects}"""

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

    system_template = (
        """Enhance and generate a few more skills that could help a person get more engaging jobs. 
        The output format should be a dict with the key "skills", and values provided in a list containing the skills you've generated.
        Please do not start each skill with the same word, we were having issues with 'enhanced' being mentioned at the start, which we don't want.
        output_format:
        {{
        "skills": [
        "enhanced skill goes here",
        "another enhanced skill",
        ... # and so on
        ]
        }}"""
    )

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template)

    human_template = """Skills to reference and enhance: {skills}"""

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
        experience = ". ".join(key_roles)

        # Extract the project names and project descriptions from the project experience
        key_projects = set()
        for project in resume_data.project_experience:
            key_projects.add(project.project_name.lower())
            # Here you can also extract other important keywords from project_description
        projects = ". ".join(key_projects)

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