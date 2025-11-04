from flask import jsonify, request
from datetime import datetime
import pandas as pd
from . import analytics_bp
from app.utils import get_db_connection

# ===== PATIENT ROUTES =====
@analytics_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "API is running ✓"}), 200

@analytics_bp.route('/patients/count', methods=['GET'])
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

@analytics_bp.route('/patients', methods=['GET'])
def get_patients():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT patient_id, first_name, last_name, date_of_birth, email FROM patients;"
        cursor.execute(query)
        patients = cursor.fetchall()
        
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

# ===== SAVE PATIENTS TO DATABASE =====
@analytics_bp.route('/patients/save-bulk', methods=['POST'])
def save_bulk_patients():
    """Save bulk patients from export to database"""
    try:
        data = request.get_json()
        patients = data.get('patients', [])
        
        if not patients:
            return jsonify({"error": "No patients provided"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        saved_count = 0
        for patient in patients:
            try:
                query = """
                INSERT INTO patients (first_name, last_name, date_of_birth, email)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """
                cursor.execute(query, (
                    patient.get('first_name', ''),
                    patient.get('last_name', ''),
                    patient.get('date_of_birth'),
                    patient.get('email', '')
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
            except Exception as e:
                print(f"Error saving patient {patient.get('first_name')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": f"Successfully saved {saved_count} patients to database",
            "count": saved_count,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== CONDITIONS ROUTES =====
@analytics_bp.route('/conditions', methods=['GET'])
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

@analytics_bp.route('/analytics/patient-conditions', methods=['GET'])
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
            "description": "Shows how many patients have each condition",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_bp.route('/saved-epic-observations', methods=['GET'])
def get_saved_epic_observations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            po.observation_id,
            po.test_name,
            po.value,
            po.unit,
            po.observation_date,
            p.first_name,
            p.last_name,
            po.fhir_patient_id
        FROM patient_observations po
        LEFT JOIN patients p ON po.patient_id = p.patient_id
        ORDER BY po.observation_date DESC
        LIMIT 50
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        observations = [
            {
                "id": r[0],
                "test_name": r[1],
                "value": r[2],
                "unit": r[3],
                "date": str(r[4]) if r[4] else None,
                "patient_name": f"{r[5]} {r[6]}" if r[5] else "Unknown",
                "fhir_id": r[7]
            }
            for r in results
        ]
        
        conn.close()
        
        return jsonify({
            "data": observations,
            "count": len(observations),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
