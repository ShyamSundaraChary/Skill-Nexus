import re
from PyPDF2 import PdfReader
import spacy
from spacy.matcher import PhraseMatcher
from datetime import datetime

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Expanded skills list (consistent with your scraping scripts)
skills_list = [
    "c", "c++", "java", "python", "javascript", "typescript", "c#", "php", "go", "rust", "swift", "kotlin", "ruby",
    "html", "css", "react", "react.js", "next.js", "angular", "vue.js", "svelte", "node.js", "express.js", "django", "flask",
    "spring boot", "laravel", "asp.net", "fast api", "ruby on rails", "jquery", "bootstrap", "tailwind css",
    "sql", "mysql", "postgresql", "mongodb", "firebase", "sqlite", "redis", "cassandra", "oracle db", "dynamodb",
    "machine learning", "deep learning", "data analysis", "data visualization", "tensorflow", "pytorch", "pandas",
    "numpy", "scikit-learn", "opencv", "natural language processing (nlp)", "keras", "xgboost", "matplotlib", "seaborn",
    "aws", "google cloud", "microsoft azure", "docker", "kubernetes", "jenkins", "terraform", "git", "ci/cd", "ci/cd pipelines",
    "ansible", "puppet", "chef", "cloudformation", "serverless", "lambda", "ec2", "s3", "gcp", "gcp bigquery", "azure",
    "ethical hacking", "penetration testing", "network security", "cryptography", "firewalls", "wireshark", "metasploit",
    "burp suite", "nmap", "owasp", "secure coding",
    "linux", "shell scripting", "windows server", "kernel development", "bash", "powershell", "unix", "Ubuntu",
    "git & github", "agile", "scrum", "design patterns", "software testing", "oop", "system design", "microservices",
    "rest", "rest apis", "restful apis", "graphql", "websockets", "soap", "grpc", "api gateway",
    "unit testing", "integration testing", "selenium", "pytest", "junit", "test automation", "mocking",
    "big data", "hadoop", "spark", "kafka", "flink", "hive", "pig", "data warehousing", "database fundamentals",
    "blockchain", "solidity", "ethereum", "smart contracts", "web3",
    "game development", "unity", "unreal engine", "opengl", "directx",
    "android development", "ios development", "flutter", "react native", "xamarin",
    "embedded systems", "iot", "arduino", "raspberry pi", "rtos",
    "devops", "sre", "sre (site reliability engineering)", "monitoring", "prometheus", "grafana", "logging", "splunk",
    "computer vision", "reinforcement learning", "statistics", "probability", "linear algebra",
    "langchain", "beautiful soup", "scrapy", "asyncio", "multithreading", "concurrent programming", "sqlalchemy",
    "jira", "trello", "confluence", "bitbucket", "gitlab", "github", "svn"
]

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp(skill) for skill in skills_list]
matcher.add("SKILLS", patterns)

# Skill-to-Role Mapping
skill_to_role_mapping = {
    "Full Stack Developer": ["javascript", "react", "node.js", "html", "css", "sql", "mongodb", "express.js", "angular", "vue.js"],
    "Python Developer": ["python", "django", "flask", "pandas", "numpy", "sql", "mysql", "postgresql", "tensorflow", "pytorch"],
    "Java Developer": ["java", "spring boot", "hibernate", "sql", "mysql", "oracle db", "rest", "microservices"],
    "Data Scientist": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "statistics", "data visualization"],
    "DevOps Engineer": ["aws", "docker", "kubernetes", "jenkins", "terraform", "ansible", "ci/cd", "linux", "bash", "monitoring"],
    "Frontend Developer": ["javascript", "react", "angular", "vue.js", "html", "css", "jquery", "bootstrap", "tailwind css"],
    "Backend Developer": ["node.js", "express.js", "django", "flask", "spring boot", "laravel", "sql", "mongodb", "rest", "graphql"],
    "Mobile Developer": ["flutter", "react native", "android development", "ios development", "kotlin", "swift", "xamarin"],
    "Cybersecurity Analyst": ["ethical hacking", "penetration testing", "network security", "cryptography", "wireshark", "metasploit", "nmap", "owasp"],
    "Game Developer": ["unity", "unreal engine", "opengl", "directx", "c++", "game development"],
    "Blockchain Developer": ["blockchain", "solidity", "ethereum", "smart contracts", "web3"]
}

def get_best_job_roles(user_skills, top_n=3):
    role_scores = {}
    for role, required_skills in skill_to_role_mapping.items():
        matching_skills = set(user_skills) & set(required_skills)
        score = len(matching_skills) / len(required_skills) * 100  # Percentage of required skills matched
        role_scores[role] = score
    
    # Sort roles by score and return top N
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    return [role for role, score in sorted_roles[:top_n] if score > 0]  # Only return roles with non-zero scores

def extract_resume_text(file):
    try:
        reader = PdfReader(file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text.lower()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_roles(resume_text):
    roles = set()
    doc = nlp(resume_text)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            continue
        if any(keyword in ent.text.lower() for keyword in ["developer", "engineer", "analyst", "manager", "scientist", "architect", "intern"]):
            roles.add(ent.text.lower().strip())
    role_patterns = re.findall(r'([a-zA-Z-]+\s?(developer|engineer|analyst|manager|scientist|architect|intern))', resume_text)
    for role in role_patterns:
        roles.add(role[0].strip())
    return list(roles)

def extract_skills(resume_text):
    skills = set()
    # Method 1: spaCy PhraseMatcher
    doc = nlp(resume_text)
    matches = matcher(doc)
    for match_id, start, end in matches:
        skills.add(doc[start:end].text.lower())
    
    # Method 2: Regex fallback for skills not caught by spaCy
    for skill in skills_list:
        if re.search(rf'\b{re.escape(skill)}\b', resume_text, re.IGNORECASE):
            skills.add(skill.lower())
    
    return list(skills)

def extract_experience(resume_text):
    experience_details = []
    total_months = 0
    
    # Pattern for date ranges (e.g., "Jan 2020 - Present", "2020 - 2022")
    job_pattern = r'((?:january|february|march|april|may|june|july|august|september|october|november|december)?\s?\d{4})\s*-\s*(current|present|(?:january|february|march|april|may|june|july|august|september|october|november|december)?\s?\d{4})'
    matches = re.finditer(job_pattern, resume_text, re.IGNORECASE)
    
    for match in matches:
        start_date = match.group(1).strip()
        end_date = match.group(2).strip()
        try:
            start = datetime.strptime(start_date, '%B %Y') if len(start_date.split()) > 1 else datetime.strptime(start_date, '%Y')
            end = datetime.now() if end_date.lower() in ['current', 'present'] else (datetime.strptime(end_date, '%B %Y') if len(end_date.split()) > 1 else datetime.strptime(end_date, '%Y'))
            duration_months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += duration_months
            years = duration_months // 12
            months = duration_months % 12
            duration = f"{years} years" if years > 0 else f"{months} months"
            experience_details.append({'start_date': start_date, 'end_date': end_date, 'duration': duration})
        except ValueError:
            continue
    
    # Fallback: Look for explicit years of experience (e.g., "5 years of experience")
    years_pattern = r'(\d+)\s*(years|year|yrs|yr)s?\s*of\s*experience'
    match = re.search(years_pattern, resume_text, re.IGNORECASE)
    if match:
        total_months = max(total_months, int(match.group(1)) * 12)
    
    total_years = total_months / 12
    return total_years, experience_details

def extract_education(resume_text):
    education_pattern = r'((b\.s\.|m\.s\.|b\.tech|m\.tech|b\.sc|m\.sc|ph\.d))\s*(?:in)?\s*([\w\s]+?)(?:\s*university)?(?:\s*of\s*[\w\s]+)?(?:\s*\d{4}\s*-\s*\d{4})?'
    matches = re.finditer(education_pattern, resume_text, re.IGNORECASE)
    education_details = []
    for match in matches:
        degree = match.group(1).strip()
        field = match.group(2).strip()
        education_details.append({'degree': degree, 'field': field})
    return education_details

def categorize_experience(total_years):
    if total_years <= 1:
        return "Fresher"
    elif total_years < 5:
        return "Mid-Level"
    else:
        return "Experienced"

def process_resume(file):
    resume_text = extract_resume_text(file)
    if not resume_text:
        return None
    
    roles = extract_roles(resume_text)
    skills = extract_skills(resume_text)
    total_experience_years, experience_details = extract_experience(resume_text)
    education = extract_education(resume_text)
    experience_category = categorize_experience(total_experience_years)
    best_job_roles = get_best_job_roles(skills)
    
    return {
        "roles": roles,
        "skills": skills,
        "total_experience_years": total_experience_years,
        "experience_details": experience_details,
        "education": education,
        "experience_category": experience_category,
        "best_job_roles": best_job_roles
    }