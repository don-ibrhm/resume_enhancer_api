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
import json

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
encoding = tiktoken.get_encoding("cl100k_base")

########################################################################################
#                           EXTRACT DETAILS FROM RESUME - OPENAI                       #
########################################################################################

def num_tokens_from_string(_string, encoding):
    """
    Calculates the number of tokens in a given string using the provided encoding.

    Args:
        _string (str): The input string.
        encoding (str): The encoding to be used for tokenization.

    Returns:
        int: The number of tokens in the given string.
    """
    num_tokens = len(encoding.encode(_string))
    return num_tokens

def try_loading(parsed_text, chat, chat_prompt, attempts=3):
    if attempts == 0: return None
    response = chat(
        chat_prompt.format_prompt(
            resume=parsed_text,
        ).to_messages()
    )
    try:
        answer = json.loads(response.content)
        return answer
    except Exception as e:
        print("- - - Response from OpenAI wasn't in the expected format, retrying...")
        print(response.content)
        try_loading(parsed_text, chat, chat_prompt, attempts-1)
        

def extract_data_new(parsed_text):
    num_input_tokens = num_tokens_from_string(parsed_text, encoding)

    if num_input_tokens < 2800:
        model_name = "gpt-3.5-turbo-0613"
    else:
        model_name = "gpt-3.5-turbo-16k"
    chat = ChatOpenAI(model_name=model_name,
                              temperature=0)  # type: ignore

    system_template = ("""Your role is to construct a structured JSON output by extracting crucial information from a range of Resume documents in PDF format. These are candidate details from resume so make your best judgement to extract relevant information.
        The following fields must be extracted from the documents:
        basic_info (including first_name, last_name, full_name, email, phone_number, location, portfolio_website_url, linkedin_url, github_main_page_url),
        objective (including objective),
        work_experience (including job_title, company, location, duration, job_summary),
        education (including university, education_level (BS, MS, or PhD), graduation_year, graduation_month, majors, GPA),
        project_experience (including project_name, project_description),
        skills (including skills),

        OUTPUT_FORMAT:
        The output nested JSON must be a single JSON object with nested properties, one for each of the fields listed above. The output must be human-readable and easy to understand.
        Make sure to follow the exact sequence of fields in the output JSON.
        If a value for a field is not found in the document, the value for that field in the output JSON must be "". 
        """)

    system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template)

    human_template = "Resume : {resume}"

    human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

    # get a chat completion from the formatted messages
    answer = try_loading(parsed_text, chat, chat_prompt, 3)

    return answer
