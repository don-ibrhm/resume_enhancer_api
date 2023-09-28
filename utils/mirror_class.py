from typing import List, Optional
from pydantic import BaseModel

class ResumeProfile(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    url: Optional[str]
    summary: Optional[str]
    location: Optional[str]


class ResumeWorkExperience(BaseModel):
    company: Optional[str]
    jobTitle: Optional[str]
    date: Optional[str]
    descriptions: Optional[List[str]]


class ResumeEducation(BaseModel):
    school: Optional[str]
    degree: Optional[str]
    date: Optional[str]
    gpa: Optional[str]
    descriptions: Optional[List[str]]


class ResumeProject(BaseModel):
    project: Optional[str]
    date: Optional[str]
    descriptions: Optional[List[str]]


class FeaturedSkill(BaseModel):
    skill: Optional[str]
    rating: float


class ResumeSkills(BaseModel):
    featuredSkills: List[FeaturedSkill]
    descriptions: Optional[List[str]]


class ResumeCustom(BaseModel):
    descriptions: Optional[List[str]]

class Resume(BaseModel):
    profile: ResumeProfile
    workExperiences: List[ResumeWorkExperience]
    educations: List[ResumeEducation]
    projects: List[ResumeProject]
    skills: ResumeSkills
    custom: ResumeCustom

