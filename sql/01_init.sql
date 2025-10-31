-- Create tables for patient health analytics

CREATE TABLE IF NOT EXISTS patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conditions (
    condition_id SERIAL PRIMARY KEY,
    condition_name VARCHAR(150) NOT NULL,
    description TEXT,
    severity_level VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS symptoms (
    symptom_id SERIAL PRIMARY KEY,
    symptom_name VARCHAR(150) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS patient_conditions (
    patient_condition_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(patient_id),
    condition_id INT NOT NULL REFERENCES conditions(condition_id),
    diagnosed_date DATE,
    status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS patient_symptoms (
    patient_symptom_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(patient_id),
    symptom_id INT NOT NULL REFERENCES symptoms(symptom_id),
    onset_date DATE,
    severity INT CHECK (severity >= 1 AND severity <= 10)
);

CREATE TABLE IF NOT EXISTS medications (
    medication_id SERIAL PRIMARY KEY,
    medication_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100),
    side_effects TEXT
);

CREATE TABLE IF NOT EXISTS patient_medications (
    patient_medication_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(patient_id),
    medication_id INT NOT NULL REFERENCES medications(medication_id),
    start_date DATE,
    end_date DATE
);

-- Add some sample data
INSERT INTO patients (first_name, last_name, date_of_birth, email, phone) 
VALUES 
    ('John', 'Doe', '1985-03-15', 'john@example.com', '555-0001'),
    ('Jane', 'Smith', '1990-07-22', 'jane@example.com', '555-0002');

INSERT INTO conditions (condition_name, description, severity_level)
VALUES
    ('Type 2 Diabetes', 'Chronic blood sugar condition', 'Moderate'),
    ('Hypertension', 'High blood pressure', 'Moderate');

INSERT INTO symptoms (symptom_name, description)
VALUES
    ('Fatigue', 'Persistent tiredness'),
    ('Headache', 'Recurring head pain');