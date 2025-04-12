import re
from PyPDF2 import PdfReader
from docx import Document
import spacy
from spacy.matcher import PhraseMatcher
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Please download it using: python -m spacy download en_core_web_sm")
    exit(1)

# Skills list (abbreviated for brevity, expand as needed)
skills_list = [
     "c", "c++", "java", "python", "javascript", "typescript", "c#", "php", "go", "rust", "swift", "kotlin", "ruby",
    "html", "css", "react", "react.js", "next.js", "angular", "vue.js", "svelte", "node.js", "express.js", "django", "flask",
    "spring boot", "laravel", "asp.net", "fastapi", "ruby on rails", "jquery", "bootstrap", "tailwind css",
    "sql", "mysql", "postgresql", "mongodb", "firebase", "sqlite", "redis", "cassandra", "oracle", "dynamodb",
    "machine learning", "deep learning", "data analysis", "data visualization", "tensorflow", "pytorch", "pandas",
    "numpy", "scikit-learn", "opencv", "nlp", "keras", "xgboost", "matplotlib", "seaborn",
    "aws", "gcp", "azure", "docker", "kubernetes", "jenkins", "terraform", "git", "cicd", "ansible",
    "puppet", "chef", "cloudformation", "serverless", "lambda", "ec2", "s3", "bigquery", "ethical hacking",
    "penetration testing", "network security", "cryptography", "firewalls", "wireshark", "metasploit",
    "burp suite", "nmap", "owasp", "secure coding",
    "linux", "shell scripting", "windows server", "kernel", "bash", "powershell", "unix", "ubuntu",
    "agile", "scrum", "design patterns", "testing", "oop", "system design", "microservices",
    "rest", "restful", "graphql", "websockets", "soap", "grpc", "api",
    "unit testing", "integration testing", "selenium", "pytest", "junit", "automation",
    "big data", "hadoop", "spark", "kafka", "flink", "hive", "pig", "data warehousing",
    "blockchain", "solidity", "ethereum", "smart contracts", "web3",
    "game development", "unity", "unreal", "opengl", "directx",
    "android", "ios", "flutter", "react native", "xamarin",
    "embedded", "iot", "arduino", "raspberry pi", "rtos",
    "devops", "sre", "monitoring", "prometheus", "grafana", "logging", "splunk",
    "computer vision", "reinforcement learning", "statistics", "probability", "linear algebra",
    "langchain", "beautifulsoup", "scrapy", "asyncio", "multithreading", "sqlalchemy",
    "jira", "trello", "confluence", "bitbucket", "gitlab", "svn"

]

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
    """Extract personal details (name, email, phone) from resume text."""
    name = re.search(r'[\w\s]+', resume_text.split('\n')[0]) or {"group": ["Unknown"]}
    email = re.search(r'[\w\.-]+@[\w\.-]+', resume_text)
    phone = re.search(r'\+?\d{10,12}|\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
    return {
        "name": name.group(0) if name else "Unknown",
        "email": email.group(0) if email else "Not found",
        "phone": phone.group(0) if phone else "Not found"
    }

def extract_roles(resume_text):
    """Extract potential job roles from resume text."""
    roles = set()
    doc = nlp(resume_text)
    for ent in doc.ents:
        if ent.label_ != "ORG" and any(keyword in ent.text.lower() for keyword in ["developer", "engineer", "analyst", "manager", "scientist", "architect", "intern"]):
            roles.add(ent.text.lower().strip())
    role_patterns = re.findall(r'([a-zA-Z\s-]+\s?(developer|engineer|analyst|manager|scientist|architect|intern))', resume_text, re.IGNORECASE)
    for role in role_patterns:
        roles.add(role[0].strip())
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
    """Extract experience duration and details from resume text."""
    experience_details = []
    total_months = 0
    
    # Corrected job pattern with balanced parentheses
    job_pattern = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?\s?\d{4}\s*-\s*(?:present|current|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?\s?\d{4})'
    matches = re.finditer(job_pattern, resume_text, re.IGNORECASE)
    
    for match in matches:
        date_range = match.group(0)
        try:
            start_str, end_str = re.split(r'-\s*', date_range)
            start = datetime.strptime(start_str.strip(), '%B %Y') if any(month in start_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']) else datetime.strptime(start_str.strip(), '%Y')
            end = datetime.now() if 'present' in end_str.lower() or 'current' in end_str.lower() else (datetime.strptime(end_str.strip(), '%B %Y') if any(month in end_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']) else datetime.strptime(end_str.strip(), '%Y'))
            duration_months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += max(duration_months, 0)
            years = duration_months // 12
            months = duration_months % 12
            duration = f"{years} years" if years > 0 else f"{months} months" if months > 0 else "0 months"
            experience_details.append({'start_date': start_str, 'end_date': end_str, 'duration': duration})
        except ValueError as e:
            logger.warning(f"Invalid date format in {date_range}: {e}")
            continue
    
    years_pattern = r'(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)s?\s*of\s*experience'
    match = re.search(years_pattern, resume_text, re.IGNORECASE)
    if match:
        years = float(match.group(1))
        total_months = max(total_months, int(years * 12))
    
    total_years = total_months / 12 if total_months > 0 else 0
    return total_years, experience_details

def extract_education(resume_text):
    """Extract education details from resume text."""
    education_pattern = r'(b\.(?:s|tech|sc)|m\.(?:s|tech|sc)|ph\.d|(?:bachelor|master|doctorate)\s+of)\s*(?:in\s*)?([\w\s-]+?)(?:\s*(?:university|college|institute)\s*of\s*[\w\s]+)?(?:\s*\d{4}\s*-\s*\d{4})?'
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
    elif 1 < total_years <= 5:
        return "Mid-Level"
    else:
        return "Experienced"

def get_best_job_roles(user_skills, top_n=3):
    """Calculate the best job roles based on skill match percentage."""
    role_scores = {}
    for role, required_skills in skill_to_role_mapping.items():
        matching_skills = set(user_skills) & set(required_skills)
        score = (len(matching_skills) / max(len(required_skills), 1)) * 100
        role_scores[role] = score
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    return [role for role, score in sorted_roles[:top_n] if score > 0]

def process_resume(file):
    """Process resume file and extract all relevant information."""
    resume_text = extract_text_from_file(file)
    if not resume_text:
        logger.error("No text extracted from resume file.")
        return None
    
    personal_info = extract_personal_info(resume_text)
    roles = extract_roles(resume_text)
    skills = extract_skills(resume_text)
    total_experience_years, experience_details = extract_experience(resume_text)
    education = extract_education(resume_text)
    experience_category = categorize_experience(total_experience_years)
    best_job_roles = get_best_job_roles(skills)
    
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