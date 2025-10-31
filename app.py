import psycopg2
import os

try:
    connection = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'healthpass123'),
        database=os.getenv('DB_NAME', 'patient_health_analytics'),
        port=5432
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM patients;")
    patients = cursor.fetchall()
    print("✅ Connection successful!")
    print(f"Patients in database: {patients}")
    connection.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")