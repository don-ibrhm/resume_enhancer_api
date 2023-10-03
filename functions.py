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

from aishop import *
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
        print('----------- Enahnced skills:', enhanced_skills)
        
        try:
            enhanced_skills = json.loads(enhanced_skills)["skills"]
        except:
            enhanced_skills = enhanced_skills.replace('\n',',')
            print('------nes:', enhanced_skills)
            enhanced_skills = json.loads(f"[{enhanced_skills}]")["skills"]

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

        try:
            enhanced_skills = json.loads(enhanced_skills)["skills"]
        except:
            enhanced_skills = enhanced_skills.replace('\n',',')
            print('------nes:', enhanced_skills)
            enhanced_skills = json.loads(f"[{enhanced_skills}]")["skills"]

        # Update the skills in the resume data with the enhanced skills
        resume_data.skills = enhanced_skills

        return resume_data