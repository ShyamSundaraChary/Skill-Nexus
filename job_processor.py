from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import logging
import math
from collections import defaultdict
import time
from config import Config
logger = logging.getLogger(__name__)

# Load the embedding model once at module level
model = SentenceTransformer('all-MiniLM-L6-v2')

def match_jobs_with_resume(resume_text, jobs):
    """Match jobs with resume using embedding-based cosine similarity with equal source distribution."""
    start_time = time.time()
    if not jobs:
        logger.warning("No jobs provided for matching")
        return []

    # Compute resume embedding
    embed_start = time.time()
    try:
        resume_embedding = model.encode(resume_text)
    except Exception as e:
        logger.error(f"Failed to compute resume embedding: {e}")
        return []
    logger.info(f"Resume embedding computed in {time.time() - embed_start:.2f} seconds")

    # Compute similarity scores and group by source
    sim_start = time.time()
    jobs_by_source = defaultdict(list)
    for job in jobs:
        if job.get('embedding'):
            try:
                job_embedding = np.array(json.loads(job['embedding']))
                similarity = cosine_similarity(resume_embedding.reshape(1, -1), 
                                             job_embedding.reshape(1, -1))[0][0]
                jobs_by_source[job['source']].append({
                    'job': job,
                    'similarity_score': similarity * 100
                })
            except Exception as e:
                logger.error(f"Error computing similarity for job {job.get('id', 'unknown')}: {e}")
                
# Select top jobs per source
    total_jobs = 40
    sources = list(jobs_by_source.keys())
    jobs_per_source = math.ceil(total_jobs / len(sources)) if sources else 0
    final_jobs=[]
    for source in sources:
        jobs_by_source[source].sort(key=lambda x: x['similarity_score'], reverse=True)
        final_jobs.extend(jobs_by_source[source][:jobs_per_source])
                
    return final_jobs