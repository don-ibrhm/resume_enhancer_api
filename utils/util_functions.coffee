def enhance_summary(resume: Resume) -> Resume:
    """
    This function takes a Resume instance representing the existing resume data.
    It enhances the objective statement using the experience and skills in the resume data
    and returns the updated Resume instance.
    """
    
    # Extract the current objective, experience, and skills from the resume data
    curr_summary = resume.profile.summary
    experiences = resume.work_experience or []
    skills = resume.skills or []
    
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
    resume.profile.summary = enhanced_objective
    
    return resume