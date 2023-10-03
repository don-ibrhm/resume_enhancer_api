### --- --- --- IMPORTS & SETUP
import utils.extract_resume
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
import json
    

# ---------------------------- OBJECTIVE ------------------------------------------
def create_objective_openai(current_objective, experience, skills):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                              temperature=0)

    system_template = ("""Create what could be a resume's objective, using the following information. 
    Let the objective be 3-5 sentences. Do not mention the word objective.""")

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

# ---------------------------- WORK EXPERIENCE ------------------------------------------

def create_job_summary_openai(current_job, skills):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                              temperature=0)

    system_template = ("""Create a 2-3 line work experience summary using the following information:""")

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



# ---------------------------- SKILLS ------------------------------------------

def create_full_skills_openai(experience, projects):
    model_name = "gpt-3.5-turbo-0613"

    chat = ChatOpenAI(model_name=model_name,
                      temperature=0)

    system_template = (
        """Create skills that could help a person get more engaging jobs. 
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

