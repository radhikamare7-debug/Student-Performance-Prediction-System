import streamlit as st
import pandas as pd
import joblib
import json
import os

from db import (
    save_student,
    get_prediction_history,
    save_uci_prediction,
    create_tables
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Student Performance Prediction",
    page_icon="🎓",
    layout="wide"
)

DATASET_PATH = "dataset/uci_student_performance.csv"
MODEL_PATH = "models"


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

@st.cache_resource
def initialize_database():
    create_tables()
    return True


try:
    initialize_database()
except Exception as error:
    st.warning(f"Database initialization failed: {error}")
    
#-------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

@st.cache_data
def load_dataset():
    return pd.read_csv(DATASET_PATH)


df = load_dataset()

X = df.drop(columns=["G3", "G1", "G2"])

# --------------------------------------------------
# LOAD MODELS
# --------------------------------------------------

@st.cache_resource
def load_models():

    models = {
        "Logistic Regression": joblib.load(
            os.path.join(MODEL_PATH, "logistic_regression.pkl")
        ),

        "Decision Tree": joblib.load(
            os.path.join(MODEL_PATH, "decision_tree.pkl")
        ),

        "Random Forest": joblib.load(
            os.path.join(MODEL_PATH, "random_forest.pkl")
        )
    }

    return models


models = load_models()

with open(
    os.path.join(MODEL_PATH, "model_results.json"),
    "r"
) as file:
    results = json.load(file)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🎓 Student Performance Prediction System")

st.caption(
    "Real UCI Dataset | Machine Learning | "
    "Logistic Regression | Decision Tree | Random Forest"
)

# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "Home Dashboard",
        "Student Details",
        "Performance Prediction",
        "Algorithm Comparison",
        "Prediction History"
    ]
)

# --------------------------------------------------
# HOME DASHBOARD
# --------------------------------------------------

if page == "Home Dashboard":

    st.header("📊 Home Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Dataset Records", len(df))
    col2.metric("Total Features", len(X.columns))
    col3.metric("ML Algorithms", 3)
    col4.metric("Prediction Classes", 2)

    st.subheader("Dataset Information")

    st.write("Dataset Source: UCI Student Performance Dataset")
    st.write("Total Student Records:", len(df))
    st.write("Input Features:", len(X.columns))
    st.write("Target Column: G3 (Final Grade)")

    # PASS / FAIL DISTRIBUTION

    st.subheader("Pass / Fail Distribution")

    result_counts = (
        df["G3"]
        .apply(lambda value: "Pass" if value >= 10 else "Fail")
        .value_counts()
    )

    st.bar_chart(result_counts)

    # DATASET PREVIEW

    st.subheader("Dataset Preview")

    st.dataframe(
        df.head(20),
        width="stretch"
    )

    # AVAILABLE ALGORITHMS

    st.subheader("Available Algorithms")

    st.write("1. Logistic Regression")
    st.write("2. Decision Tree (Entropy)")
    st.write("3. Random Forest")

    st.info(
        "Pass = Final Grade >= 10 | Fail = Final Grade < 10"
    )


# --------------------------------------------------
# STUDENT DETAILS
# --------------------------------------------------

elif page == "Student Details":

    st.header("👨‍🎓 Student Details")

    st.info(
        "This form saves student profile information "
        "in the existing MySQL students table."
    )

    with st.form("student_form"):

        name = st.text_input("Student Name")

        roll = st.text_input("Roll Number")

        department = st.selectbox(
            "Department",
            [
                "Computer Engineering",
                "IT",
                "Mechanical",
                "Civil",
                "Other"
            ]
        )

        study_hours = st.number_input(
            "Daily Study Hours",
            min_value=0.0,
            max_value=24.0,
            value=4.0
        )

        attendance = st.slider(
            "Attendance (%)", 0, 100, 75
        )

        previous_marks = st.slider(
            "Previous Marks", 0, 100, 60
        )

        assignment_marks = st.slider(
            "Assignment Marks", 0, 100, 60
        )

        internal_marks = st.slider(
            "Internal Marks", 0, 100, 60
        )

        submitted = st.form_submit_button(
            "Save Student Details"
        )

    if submitted:

        if name.strip() and roll.strip():

            try:

                save_student(
                    name,
                    roll,
                    department,
                    study_hours,
                    attendance,
                    previous_marks,
                    assignment_marks,
                    internal_marks
                )

                st.success(
                    "Student Details Saved Successfully!"
                )

            except Exception as error:

                st.error(f"Database Error: {error}")

        else:

            st.warning(
                "Please enter Student Name and Roll Number."
            )


# --------------------------------------------------
# PERFORMANCE PREDICTION
# --------------------------------------------------

elif page == "Performance Prediction":

    st.header("🔮 Real Dataset Performance Prediction")

    st.write(
        "Enter the student's academic and personal details "
        "to predict Pass or Fail."
    )

    st.info(
        "The model uses 30 input features from the UCI dataset. "
        "G1, G2 and G3 are excluded from prediction inputs."
    )

    with st.form("real_prediction_form"):

        student_name = st.text_input("Student Name")

        st.subheader("Student Information")

        input_values = {}

        col1, col2 = st.columns(2)

        for index, feature in enumerate(X.columns):

            target_col = col1 if index % 2 == 0 else col2

            with target_col:

                if pd.api.types.is_numeric_dtype(X[feature]):

                    min_value = int(X[feature].min())
                    max_value = int(X[feature].max())

                    default_value = int(X[feature].median())

                    input_values[feature] = st.number_input(
                        feature.replace("_", " ").title(),
                        min_value=min_value,
                        max_value=max_value,
                        value=default_value,
                        step=1,
                        key=f"input_{feature}"
                    )

                else:

                    options = sorted(
                        X[feature].dropna().unique().tolist()
                    )

                    mode_value = X[feature].mode()[0]

                    default_index = (
                        options.index(mode_value)
                        if mode_value in options
                        else 0
                    )

                    input_values[feature] = st.selectbox(
                        feature.replace("_", " ").title(),
                        options,
                        index=default_index,
                        key=f"input_{feature}"
                    )

        algorithm = st.selectbox(
            "Select Machine Learning Algorithm",
            [
                "Logistic Regression",
                "Decision Tree",
                "Random Forest"
            ]
        )

        submitted = st.form_submit_button(
            "Predict Student Result"
        )

    # PROCESS PREDICTION

    if submitted:

        if not student_name.strip():

            st.warning("Please enter Student Name.")

        else:

            input_df = pd.DataFrame(
                [input_values],
                columns=X.columns
            )

            model = models[algorithm]

            prediction = int(model.predict(input_df)[0])

            result = "Pass" if prediction == 1 else "Fail"

            # SAVE PREDICTION IN MYSQL

            try:

                save_uci_prediction(
                    student_name,
                    input_values,
                    algorithm,
                    result
                )

                st.success(
                    "Prediction saved successfully in MySQL!"
                )

            except Exception as error:

                st.error(
                    f"Database Save Error: {error}"
                )

            # DISPLAY RESULT

            st.subheader("Prediction Result")

            if result == "Pass":

                st.success("Predicted Result: PASS 🎉")

            else:

                st.warning("Predicted Result: FAIL")

            st.write("Student Name:", student_name)
            st.write("Algorithm:", algorithm)
            st.write("Predicted Class:", result)

            # DISPLAY PROBABILITIES

            if hasattr(model, "predict_proba"):

                probabilities = model.predict_proba(
                    input_df
                )[0]

                probability_df = pd.DataFrame({
                    "Class": ["Fail", "Pass"],
                    "Probability (%)": [
                        round(float(probabilities[0]) * 100, 2),
                        round(float(probabilities[1]) * 100, 2)
                    ]
                })

                st.subheader("Model Class Probabilities")

                st.dataframe(
                    probability_df,
                    width="stretch"
                )

            st.warning(
                "This is a model prediction based on the UCI dataset. "
                "It is not a guaranteed academic result."
            )


# --------------------------------------------------
# ALGORITHM COMPARISON
# --------------------------------------------------

elif page == "Algorithm Comparison":

    st.header("📈 Algorithm Comparison")

    comparison = pd.DataFrame(results).T

    st.subheader("Model Evaluation Results")

    display_columns = [
        "accuracy",
        "precision",
        "recall",
        "f1_score"
    ]

    display_df = comparison[display_columns].copy()

    display_df.columns = [
        "Accuracy (%)",
        "Precision (%)",
        "Recall (%)",
        "F1 Score (%)"
    ]

    st.dataframe(
        display_df,
        width="stretch"
    )

    st.subheader("Accuracy Comparison")

    accuracy_df = comparison[["accuracy"]].copy()

    accuracy_df.columns = ["Accuracy (%)"]

    st.bar_chart(accuracy_df)

    best_algorithm = comparison["accuracy"].idxmax()

    st.success(
        f"Best Performing Algorithm: {best_algorithm} "
        f"({comparison.loc[best_algorithm, 'accuracy']}%)"
    )

    st.subheader("Confusion Matrix")

    selected_algorithm = st.selectbox(
        "Select Algorithm",
        list(results.keys())
    )

    matrix = results[selected_algorithm]["confusion_matrix"]

    matrix_df = pd.DataFrame(
        matrix,
        index=["Actual Fail", "Actual Pass"],
        columns=["Predicted Fail", "Predicted Pass"]
    )

    st.dataframe(matrix_df, width="stretch")

    st.caption(
        "Results are calculated on the 130-record test set "
        "using an 80:20 train-test split."
    )

    st.warning(
        "These scores are from one test split and should not "
        "be interpreted as guaranteed real-world performance."
    )


# --------------------------------------------------
# PREDICTION HISTORY
# --------------------------------------------------

elif page == "Prediction History":

    st.header("📜 Prediction History")

    st.write("View all previously saved student predictions.")

    try:

        history = get_prediction_history()

        if history:

            history_df = pd.DataFrame(history)

            column_mapping = {
                "student_name": "Student Name",
                "algorithm": "Algorithm",
                "prediction": "Prediction",
                "input_features": "Input Features",
                "created_at": "Created At",
                "record_type": "Record Type"
            }

            history_df = history_df.rename(
                columns=column_mapping
            )

            # PASS AND FAIL STATISTICS

            prediction_col = next(
                (
                    c for c in history_df.columns
                    if c.lower() == "prediction"
                ),
                None
            )

            if prediction_col is None:

                st.error("Prediction column not found.")

            else:

                pass_count = (
                    history_df[prediction_col]
                    .astype(str).str.lower() == "pass"
                ).sum()

                fail_count = (
                    history_df[prediction_col]
                    .astype(str).str.lower() == "fail"
                ).sum()

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Total Predictions",
                    len(history_df)
                )

                col2.metric(
                    "Pass Count",
                    int(pass_count)
                )

                col3.metric(
                    "Fail Count",
                    int(fail_count)
                )

                st.divider()

                # UCI AND OLD DATASET HISTORY

                record_col = next(
                    (
                        c for c in history_df.columns
                        if c.lower() == "record type"
                    ),
                    None
                )

                if record_col:

                    st.subheader("🎓 UCI Dataset Predictions")

                    uci_df = history_df[
                        history_df[record_col] == "UCI Dataset"
                    ]

                    if not uci_df.empty:
    
                        display_columns = [
                            "Student Name",
                            "Algorithm",
                            "Prediction",
                            "Created At",
                            "study_hours",
                            "attendance",
                            "previous_marks",
                            "assignment_marks",
                            "internal_marks"
                        ]

                        available_columns = [
                            col for col in display_columns
                            if col in uci_df.columns
                        ]

                        st.dataframe(
                            uci_df[available_columns],
                            width="stretch",
                            hide_index=True
                        )

                    else:

                        st.info("No UCI predictions available.")

                    st.subheader("📚 Old Dataset Predictions")

                    old_df = history_df[
                        history_df[record_col] == "Old Dataset"
                    ]

                    if not old_df.empty:

                        st.dataframe(
                            old_df,
                            width="stretch",
                            hide_index=True
                        )

                    else:

                        st.info("No old predictions available.")

                else:

                    st.dataframe(
                        history_df,
                        width="stretch",
                        hide_index=True
                    )

                # PREDICTION DETAILS

                feature_col = next(
                    (
                        c for c in history_df.columns
                        if c.lower() == "input features"
                    ),
                    None
                )

                name_col = next(
                    (
                        c for c in history_df.columns
                        if c.lower() == "student name"
                    ),
                    None
                )

                algorithm_col = next(
                    (
                        c for c in history_df.columns
                        if c.lower() == "algorithm"
                    ),
                    None
                )

                if feature_col and name_col and algorithm_col:

                    st.divider()

                    st.subheader("🔍 UCI Prediction Details")

                    uci_details = (
                        history_df[
                            history_df[record_col] == "UCI Dataset"
                        ]
                        if record_col
                        else pd.DataFrame()
                    )

                    if not uci_details.empty:

                        selected_index = st.selectbox(
                            "Select Prediction",
                            uci_details.index,
                            format_func=lambda i: (
                                f"{uci_details.loc[i, name_col]} - "
                                f"{uci_details.loc[i, algorithm_col]}"
                            )
                        )

                        features = uci_details.loc[
                            selected_index,
                            feature_col
                        ]

                        if isinstance(features, str):

                            try:
                                features = json.loads(features)

                            except json.JSONDecodeError:
                                features = {}

                        if isinstance(features, dict):

                            st.json(features)

        else:

            st.info("No prediction history found.")

    except Exception as error:

        st.error(
            f"Unable to load prediction history: {error}"
        )