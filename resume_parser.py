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
skills_list = SKILLS_LIST

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp(skill) for skill in set(skills_list)]
matcher.add("SKILLS", patterns)

skill_to_role_mapping = {
   "Full Stack Developer": ["javascript", "react", "node.js", "html", "css", "sql", "mongodb", "express.js", "angular", "vue.js", "next.js", "svelte", "rest apis", "graphql", "websockets", "docker"],
   "Python Developer": ["python", "django", "flask", "pandas", "numpy", "sql", "mysql", "postgresql", "fastapi", "tensorflow", "pytorch", "matplotlib", "git", "restful apis", "celery", "redis"],
   "Java Developer": ["java", "spring boot", "hibernate", "sql", "mysql", "oracle", "rest", "microservices", "junit", "maven", "gradle", "kafka", "docker"],
   "Data Scientist": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "statistics", "data visualization", "seaborn", "matplotlib", "sql", "nlp", "spark"],
   "DevOps Engineer": ["aws", "docker", "kubernetes", "jenkins", "terraform", "ansible", "cicd", "linux", "bash", "monitoring", "prometheus", "grafana", "gitops", "helm", "argocd"],
   "Frontend Developer": ["javascript", "react", "angular", "vue.js", "html", "css", "jquery", "bootstrap", "tailwind css", "svelte", "redux", "typescript", "webpack", "vite", "figma"],
   "Backend Developer": ["node.js", "express.js", "django", "flask", "spring boot", "laravel", "sql", "mongodb", "rest", "graphql", "grpc", "redis", "jwt", "kafka"],
   "Software Engineer": ["software development", "agile", "scrum", "git", "version control", "design patterns", "oop", "data structures & algorithms", "code review", "testing", "rest apis"],
   "AI/ML Engineer": [ "python", "tensorflow", "pytorch", "ml algorithms", "mlops", "scikit-learn", "data preprocessing", "model deployment", "onnx", "huggingface", "automl"],
   "Data Engineer": ["python", "spark", "hadoop", "kafka", "airflow", "sql", "etl pipelines", "aws glue", "bigquery", "snowflake", "data lakes"],
   "Data Scientist": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "statistics", "data visualization", "seaborn", "matplotlib", "sql", "nlp"],
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
        "best_job_roles": best_job_roles,
        "resume_text": resume_text  # Added for embedding computation
}
