from typing import List, Optional
from pydantic import BaseModel

# Redefine the BasicInfoModel
class BasicInfoModel(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    location: Optional[str]
    portfolio_website_url: Optional[str]
    linkedin_url: Optional[str]
    github_main_page_url: Optional[str]

# Redefine the WorkExperienceModel
class WorkExperienceModel(BaseModel):
    job_title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    duration: Optional[str]
    job_summary: Optional[str]

# Redefine the EducationModel
class EducationModel(BaseModel):
    university: Optional[str]
    education_level: Optional[str]
    graduation_year: Optional[str]
    graduation_month: Optional[str]
    majors: Optional[str]
    GPA: Optional[str]

# Define the ProjectExperienceModel
class ProjectExperienceModel(BaseModel):
    project_name: Optional[str]
    project_description: Optional[str]

# Redefine the ResumeModel to include the project_experience section
class ResumeModel(BaseModel):
    basic_info: BasicInfoModel
    objective: Optional[str]
    work_experience: Optional[List[WorkExperienceModel]]
    education: Optional[List[EducationModel]]
    project_experience: Optional[List[ProjectExperienceModel]]
    skills: Optional[List[str]]

# Simple model contining text attribute for getting text to api
class ResumeText(BaseModel):
    text: str
