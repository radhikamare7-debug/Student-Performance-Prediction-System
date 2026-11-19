import certifi
import mysql.connector
import os
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

def get_db_config():

    try:
        secrets = st.secrets["tidb"]

        return {
            "host": secrets["host"],
            "port": int(secrets["port"]),
            "user": secrets["user"],
            "password": secrets["password"],
            "database": secrets["database"],
            "ssl_ca": os.path.join(
                BASE_DIR, secrets.get("ssl_ca", "isrgrootx1.pem")
            ),
            "ssl_verify_cert": True,
        }

    except Exception:

        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv(
                "DB_NAME", "student_performance_db"
            ),
            **(
                {
                    "ssl_ca": os.path.join(
                        BASE_DIR, os.getenv(
                            "DB_SSL_CA", "isrgrootx1.pem"
                        )
                    ),
                    "ssl_verify_cert": True,
                }
                if os.getenv("DB_HOST") else {}
            )
        }


def get_connection():
    return mysql.connector.connect(**get_db_config())


# --------------------------------------------------
# CREATE TABLES
# --------------------------------------------------

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150),
            roll_number VARCHAR(100) UNIQUE,
            department VARCHAR(150),
            study_hours FLOAT,
            attendance FLOAT,
            previous_marks FLOAT,
            assignment_marks FLOAT,
            internal_marks FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(150),
            study_hours FLOAT,
            attendance FLOAT,
            previous_marks FLOAT,
            assignment_marks FLOAT,
            internal_marks FLOAT,
            algorithm VARCHAR(100),
            prediction VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uci_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(150) NOT NULL,
            algorithm VARCHAR(100) NOT NULL,
            prediction VARCHAR(20) NOT NULL,
            input_features LONGTEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


# --------------------------------------------------
# SAVE STUDENT DETAILS
# --------------------------------------------------

def save_student(
    name, roll, department, study_hours,
    attendance, previous_marks,
    assignment_marks, internal_marks
):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO students
        (name, roll_number, department, study_hours,
         attendance, previous_marks,
         assignment_marks, internal_marks)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

        ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        department = VALUES(department),
        study_hours = VALUES(study_hours),
        attendance = VALUES(attendance),
        previous_marks = VALUES(previous_marks),
        assignment_marks = VALUES(assignment_marks),
        internal_marks = VALUES(internal_marks)
    """

    cursor.execute(query, (
        name, roll, department, study_hours,
        attendance, previous_marks,
        assignment_marks, internal_marks
    ))

    conn.commit()
    cursor.close()
    conn.close()


# --------------------------------------------------
# SAVE OLD PREDICTION
# --------------------------------------------------

def save_prediction(
    name, study_hours, attendance,
    previous_marks, assignment_marks,
    internal_marks, algorithm, prediction
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions
        (student_name, study_hours, attendance,
         previous_marks, assignment_marks,
         internal_marks, algorithm, prediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        name, study_hours, attendance,
        previous_marks, assignment_marks,
        internal_marks, algorithm, prediction
    ))

    conn.commit()
    cursor.close()
    conn.close()


# --------------------------------------------------
# SAVE UCI PREDICTION
# --------------------------------------------------

def save_uci_prediction(
    name, input_features, algorithm, prediction
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO uci_predictions
        (student_name, algorithm, prediction, input_features)
        VALUES (%s, %s, %s, %s)
    """, (
        name,
        algorithm,
        prediction,
        json.dumps(input_features, default=str)
    ))

    conn.commit()
    cursor.close()
    conn.close()


# --------------------------------------------------
# PROCESS UCI RECORD
# --------------------------------------------------

def process_uci_record(record):

    features = record.get("input_features")

    if isinstance(features, str):
        try:
            features = json.loads(features)
        except (json.JSONDecodeError, TypeError):
            features = {}

    if not isinstance(features, dict):
        features = {}

    studytime = features.get("studytime")
    record["study_hours"] = (
        f"{studytime} (Category 1-4)"
        if studytime is not None else "N/A"
    )

    absences = features.get("absences")
    record["attendance"] = (
        f"{absences} absences"
        if absences is not None else "N/A"
    )

    g1 = features.get("G1")
    g2 = features.get("G2")

    record["previous_marks"] = (
        f"G1: {g1}, G2: {g2}"
        if g1 is not None and g2 is not None
        else "N/A"
    )

    record["assignment_marks"] = "N/A"
    record["internal_marks"] = "N/A"

    return record


# --------------------------------------------------
# GET PREDICTION HISTORY
# --------------------------------------------------

def get_prediction_history():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM predictions ORDER BY id DESC"
    )
    old_records = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM uci_predictions ORDER BY id DESC"
    )
    new_records = cursor.fetchall()

    cursor.close()
    conn.close()

    for record in old_records:
        record["Record Type"] = "Old Dataset"

    for record in new_records:
        record["Record Type"] = "UCI Dataset"
        process_uci_record(record)

    all_records = old_records + new_records

    all_records.sort(
        key=lambda x: str(x.get("created_at", "")),
        reverse=True
    )

    return all_records


# --------------------------------------------------
# TEST CONNECTION
# --------------------------------------------------

if __name__ == "__main__":

    try:
        conn = get_connection()
        print("Cloud MySQL Database Connected Successfully!")
        conn.close()

        create_tables()
        print("All Database Tables Ready!")

    except Exception as error:
        print("Database Error:", error)