from flask import render_template
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'healthpass123'),
        database=os.getenv('DB_NAME', 'patient_health_analytics'),
        port=5432
    )
    return conn

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "API is running ✅"}), 200

@app.route('/', methods=['GET'])
def dashboard():
    return render_template('index.html')
# Get total patient count
@app.route('/api/patients/count', methods=['GET'])
def patient_count():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM patients;"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "data": count,
            "query": query,
            "description": "Returns the total number of patients in the database",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all patients
@app.route('/api/patients', methods=['GET'])
def get_patients():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT patient_id, first_name, last_name, date_of_birth, email FROM patients;"
        cursor.execute(query)
        patients = cursor.fetchall()
        
        # Convert to list of dicts
        patient_list = [
            {
                "id": p[0],
                "first_name": p[1],
                "last_name": p[2],
                "date_of_birth": str(p[3]),
                "email": p[4]
            }
            for p in patients
        ]
        
        conn.close()
        
        return jsonify({
            "data": patient_list,
            "query": query,
            "description": "Returns all patients with their basic information",
            "count": len(patient_list),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all conditions
@app.route('/api/conditions', methods=['GET'])
def get_conditions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT condition_id, condition_name, description, severity_level FROM conditions;"
        cursor.execute(query)
        conditions = cursor.fetchall()
        
        condition_list = [
            {
                "id": c[0],
                "name": c[1],
                "description": c[2],
                "severity": c[3]
            }
            for c in conditions
        ]
        
        conn.close()
        
        return jsonify({
            "data": condition_list,
            "query": query,
            "description": "Returns all medical conditions in the database",
            "count": len(condition_list),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get patient conditions (analytics)
@app.route('/api/analytics/patient-conditions', methods=['GET'])
def patient_conditions_analytics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT c.condition_name, COUNT(pc.patient_id) as patient_count
        FROM conditions c
        LEFT JOIN patient_conditions pc ON c.condition_id = pc.condition_id
        GROUP BY c.condition_id, c.condition_name
        ORDER BY patient_count DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        analytics = [
            {
                "condition": r[0],
                "patient_count": r[1]
            }
            for r in results
        ]
        
        conn.close()
        
        return jsonify({
            "data": analytics,
            "query": query.strip(),
            "description": "Shows how many patients have each condition (grouped by condition name, ordered by frequency)",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)