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
