import psycopg2
import os

def get_db_connection():
    """Get database connection"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'healthpass123'),
        database=os.getenv('DB_NAME', 'patient_health_analytics'),
        port=5432
    )
    return conn