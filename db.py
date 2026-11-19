import mysql.connector
import os
import json
from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv(
            "DB_NAME",
            "student_performance_db"
        )
    )


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

    values = (
        name, roll, department, study_hours,
        attendance, previous_marks,
        assignment_marks, internal_marks
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()


# --------------------------------------------------
# OLD PREDICTION SAVE
# --------------------------------------------------

def save_prediction(
    name, study_hours, attendance,
    previous_marks, assignment_marks,
    internal_marks, algorithm, prediction
):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO predictions
        (student_name, study_hours, attendance,
         previous_marks, assignment_marks,
         internal_marks, algorithm, prediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        name, study_hours, attendance,
        previous_marks, assignment_marks,
        internal_marks, algorithm, prediction
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()


# --------------------------------------------------
# CREATE UCI PREDICTIONS TABLE
# --------------------------------------------------

def create_uci_prediction_table():

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        CREATE TABLE IF NOT EXISTS uci_predictions (

            id INT AUTO_INCREMENT PRIMARY KEY,

            student_name VARCHAR(150) NOT NULL,

            algorithm VARCHAR(100) NOT NULL,

            prediction VARCHAR(20) NOT NULL,

            input_features LONGTEXT,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
    """

    cursor.execute(query)

    cursor.close()
    conn.close()


# --------------------------------------------------
# SAVE UCI PREDICTION
# --------------------------------------------------

def save_uci_prediction(
    name, input_features,
    algorithm, prediction
):

    create_uci_prediction_table()

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO uci_predictions
        (student_name, algorithm, prediction, input_features)

        VALUES (%s, %s, %s, %s)
    """

    values = (
        name,
        algorithm,
        prediction,
        json.dumps(input_features, default=str)
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

# --------------------------------------------------
# PROCESS UCI FEATURES
# --------------------------------------------------

def process_uci_record(record):

    features = record.get("input_features")

    # Convert JSON string into dictionary
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except (json.JSONDecodeError, TypeError):
            features = {}

    if not isinstance(features, dict):
        features = {}

    # Student Study Time
    studytime = features.get("studytime")

    record["study_hours"] = (
        f"{studytime} (Category 1-4)"
        if studytime is not None else "N/A"
    )

    # Attendance / Absences
    absences = features.get("absences")

    record["attendance"] = (
        f"{absences} absences"
        if absences is not None else "N/A"
    )

    # Previous Marks
    g1 = features.get("G1")
    g2 = features.get("G2")

    if g1 is not None and g2 is not None:
        record["previous_marks"] = f"G1: {g1}, G2: {g2}"
    else:
        record["previous_marks"] = "N/A"

    # Assignment Marks
    record["assignment_marks"] = "N/A"

    # Internal Marks
    record["internal_marks"] = "N/A"

    return record


# --------------------------------------------------
# GET OLD + NEW PREDICTION HISTORY
# --------------------------------------------------

def get_prediction_history():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Old prediction records
    cursor.execute(
        "SELECT * FROM predictions ORDER BY id DESC"
    )
    old_records = cursor.fetchall()

    # UCI prediction records
    cursor.execute(
        "SELECT * FROM uci_predictions ORDER BY id DESC"
    )
    new_records = cursor.fetchall()

    cursor.close()
    conn.close()

    # Add record type
    for record in old_records:
        record["Record Type"] = "Old Dataset"

    for record in new_records:
        record["Record Type"] = "UCI Dataset"
        process_uci_record(record)

    # Combine records
    all_records = old_records + new_records

    all_records.sort(
        key=lambda x: str(x.get("created_at", "")),
        reverse=True
    )

    return all_records


# --------------------------------------------------
# TEST DATABASE CONNECTION
# --------------------------------------------------

if __name__ == "__main__":

    try:
        conn = get_connection()
        print("MySQL Database Connected Successfully!")
        conn.close()

        create_uci_prediction_table()
        print("UCI Predictions Table Ready!")

    except mysql.connector.Error as error:
        print("Database Error:", error)