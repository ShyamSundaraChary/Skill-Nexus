import re
from PyPDF2 import PdfReader
from docx import Document
import spacy
from spacy.matcher import PhraseMatcher
from datetime import datetime
import logging
from Scrapping_Jobs.settings import SKILLS_LIST
logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Please download it using: python -m spacy download en_core_web_sm")
    exit(1)

# Skills list (abbreviated for brevity, expand as needed)
skills_list =SKILLS_LIST

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp(skill) for skill in set(skills_list)]
matcher.add("SKILLS", patterns)

skill_to_role_mapping = {
    "Full Stack Developer": ["javascript", "react", "node.js", "html", "css", "sql", "mongodb", "express.js", "angular", "vue.js", "next.js", "svelte"],
    "Python Developer": ["python", "django", "flask", "pandas", "numpy", "sql", "mysql", "postgresql", "tensorflow", "pytorch", "fastapi"],
    "Java Developer": ["java", "spring boot", "hibernate", "sql", "mysql", "oracle", "rest", "microservices", "junit"],
    "Data Scientist": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "statistics", "data visualization", "seaborn", "matplotlib"],
    "DevOps Engineer": ["aws", "docker", "kubernetes", "jenkins", "terraform", "ansible", "cicd", "linux", "bash", "monitoring", "prometheus", "grafana", "sre"],
    "Frontend Developer": ["javascript", "react", "angular", "vue.js", "html", "css", "jquery", "bootstrap", "tailwind css", "svelte"],
    "Backend Developer": ["node.js", "express.js", "django", "flask", "spring boot", "laravel", "sql", "mongodb", "rest", "graphql", "grpc"],
    "Mobile Developer": ["flutter", "react native", "android", "ios", "kotlin", "swift", "xamarin"],
    "Cybersecurity Analyst": ["ethical hacking", "penetration testing", "network security", "cryptography", "wireshark", "metasploit", "nmap", "owasp", "firewalls"],
    "Game Developer": ["unity", "unreal", "opengl", "directx", "c++", "game development"],
    "Blockchain Developer": ["blockchain", "solidity", "ethereum", "smart contracts", "web3"]
}

def extract_text_from_file(file):
    """Extract text from PDF or DOCX file."""
    file_extension = file.filename.split('.')[-1].lower()
    try:
        if file_extension == 'pdf':
            reader = PdfReader(file)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif file_extension in ['docx', 'doc']:
            doc = Document(file)
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        return text.lower().strip() if text else ""
    except Exception as e:
        logger.error(f"Error processing {file_extension} file: {e}")
        return ""

def extract_personal_info(resume_text):
    name = re.search(r'[\w\s]+', resume_text.split('\n')[0]) or {"group": ["Unknown"]}
    email = re.search(r'[\w\.-]+@[\w\.-]+', resume_text)
    phone = re.search(r'\+?\d{10,12}|\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
    return {
        "name": name.group(0) if name else "Unknown",
        "email": email.group(0) if email else "Not found",
        "phone": phone.group(0) if phone else "Not found"
    }

def extract_roles(resume_text):
    roles = set()
    doc = nlp(resume_text.replace('\n', ' '))
    for ent in doc.ents:
        if ent.label_ != "ORG" and any(keyword in ent.text.lower() for keyword in ["developer", "engineer", "analyst", "manager", "scientist", "architect", "intern"]):
            roles.add(ent.text.lower().strip())
    role_patterns = re.findall(r'([a-zA-Z\s-]*(?:developer|engineer|analyst|manager|scientist|architect|intern))\b', resume_text.replace('\n', ' '), re.IGNORECASE)
    for role in role_patterns:
        roles.add(role.strip().lower())
    return list(roles)

def extract_skills(resume_text):
    """Extract skills using spaCy PhraseMatcher and regex fallback."""
    skills = set()
    doc = nlp(resume_text)
    matches = matcher(doc)
    for match_id, start, end in matches:
        skill = doc[start:end].text.lower()
        skills.add(skill)
    skill_pattern = r'\b(' + '|'.join(map(re.escape, skills_list)) + r')\b'
    additional_skills = re.findall(skill_pattern, resume_text, re.IGNORECASE)
    skills.update(skill.lower() for skill in additional_skills)
    return list(skills)

def extract_experience(resume_text):
    experience_details = []
    total_months = 0
    # Split resume into sections
    sections = resume_text.split("work experience")
    work_text = sections[1] if len(sections) > 1 else resume_text
    job_pattern = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}\s*-\s*(?:present|current|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4})'
    matches = re.finditer(job_pattern, work_text, re.IGNORECASE)
    for match in matches:
        date_range = match.group(0)
        try:
            start_str, end_str = re.split(r'-\s*', date_range)
            start = datetime.strptime(start_str.strip(), '%B %Y')
            end = datetime.now() if 'present' in end_str.lower() or 'current' in end_str.lower() else datetime.strptime(end_str.strip(), '%B %Y')
            duration_months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += max(duration_months, 0)
            years = duration_months // 12
            months = duration_months % 12
            duration = f"{years} years" if years > 0 else f"{months} months" if months > 0 else "0 months"
            experience_details.append({'start_date': start_str.strip(), 'end_date': end_str.strip(), 'duration': duration})
        except ValueError as e:
            logger.warning(f"Invalid date format in {date_range}: {e}")
            continue
    total_years = total_months / 12 if total_months > 0 else 0
    return total_years, experience_details

def extract_education(resume_text):
    education_pattern = r'(b\.(?:s|tech|sc)|m\.(?:s|tech|sc)|ph\.d|(?:bachelor|master|doctorate)\s+of)\s*([\w\s-]+?)(?:\s*(?:university|college|institute)\s*of\s*[\w\s]+)?(?:\s*\d{4}\s*-\s*\d{4})?'
    matches = re.finditer(education_pattern, resume_text, re.IGNORECASE)
    education_details = []
    for match in matches:
        degree = match.group(1).strip()
        field = match.group(2).strip() if match.group(2) else "Unknown"
        education_details.append({'degree': degree, 'field': field})
    return education_details

def categorize_experience(total_years):
    """Categorize experience level."""
    if total_years <= 1:
        return "Fresher"
    else:
        return "Experienced"

def get_best_job_roles(user_skills, top_n=3):
    role_scores = {}
    user_skills_lower = [skill.lower() for skill in user_skills]
    for role, required_skills in skill_to_role_mapping.items():
        matching_skills = 0
        for user_skill in user_skills_lower:
            for req_skill in required_skills:
                if user_skill == req_skill:  # Exact match
                    matching_skills += 1
                    break
        match_percentage = (matching_skills / max(len(required_skills), 1)) * 100
        total_score = match_percentage * 0.7 + matching_skills * 10
        role_scores[role] = total_score
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    top_roles = [role.replace(" ", "_").lower() for role, score in sorted_roles[:top_n] if score > 0]
    if len(top_roles) < 2:
        default_roles = ["software_engineer", "full_stack_developer"]
        for role in default_roles:
            if role not in top_roles:
                top_roles.append(role)
                if len(top_roles) >= top_n:
                    break
    return top_roles[:top_n]

def process_resume(file):
    """Process resume file and extract all relevant information."""
    resume_text = extract_text_from_file(file)
    if not resume_text:
        logger.error("No text extracted from resume file.")
        return None
    
    personal_info = extract_personal_info(resume_text)
    roles = extract_roles(resume_text)
    skills = extract_skills(resume_text)
    
    # Ensure we have at least some skills, even if extraction fails
    if not skills or len(skills) < 3:
        # Add some common skills as default
        default_skills = ["python", "java", "javascript", "sql", "html", "css"]
        skills.extend(default_skills)
        # Remove duplicates
        skills = list(set(skills))
        logger.warning(f"Few or no skills detected, adding default skills. Skills: {skills}")
    
    total_experience_years, experience_details = extract_experience(resume_text)
    education = extract_education(resume_text)
    experience_category = categorize_experience(total_experience_years)
    best_job_roles = get_best_job_roles(skills)
    
    logger.info(f"Extracted {len(skills)} skills and {len(best_job_roles)} job roles")
    logger.info(f"Experience category: {experience_category}")
    logger.info(f"Total experience: {total_experience_years} years")
    logger.info(f"Experience details: {experience_details}")
    logger.info(f"Education details: {education}")
    logger.info(f"Personal info: {personal_info}")
    logger.info(f"Roles: {roles}")
    logger.info(f"Skills: {skills}")
    logger.info(f"Best job roles: {best_job_roles}")
    logger.info("\n\n\n\n")  # giving gap
    return {
        "personal_info": personal_info,
        "roles": roles,
        "skills": skills,
        "total_experience_years": round(total_experience_years, 2),
        "experience_details": experience_details,
        "education": education,
        "experience_category": experience_category,
        "best_job_roles": best_job_roles
    }