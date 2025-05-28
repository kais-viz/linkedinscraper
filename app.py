# flake8: noqa e501
from flask import Flask, render_template, jsonify, request
import pandas as pd
import sqlite3
import pymysql
import json
import openai
from pdfminer.high_level import extract_text
from flask_cors import CORS
from sqlalchemy import create_engine


def load_config(file_name):
    # Load the config file
    with open(file_name) as f:
        return json.load(f)


config = load_config("config.json")
app = Flask(__name__)
CORS(app)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def read_pdf(file_path):
    try:
        text = extract_text(file_path)
        return text
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None


# db = load_config('config.json')['db_path']
# try:
#     api_key = load_config('config.json')['OpenAI_API_KEY']
#     print("API key found")
# except:
#     print("No OpenAI API key found. Please add one to config.json")

# try:
#     gpt_model = load_config('config.json')['OpenAI_Model']
#     print("Model found")
# except:
#     print("No OpenAI Model found or it's incorrectly specified in the config. Please add one to config.json")


@app.route("/")
def home():
    jobs = read_jobs_from_db()
    return render_template("jobs.html", jobs=jobs)


@app.route("/job/<int:job_id>")
def job(job_id):
    jobs = read_jobs_from_db()
    return render_template("./templates/job_description.html", job=jobs[job_id])


@app.route("/get_all_jobs")
def get_all_jobs():
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        engine = create_engine(
            f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}",
            pool_recycle=3600,
        )
        query = "SELECT * FROM jobs"
        df = pd.read_sql_query(query, engine)
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        query = "SELECT * FROM jobs"
        df = pd.read_sql_query(query, conn)

    # df = df.sort_values(by="id", ascending=False)
    df = df.sort_values(by=["date", "id"], ascending=[False, False])
    df.reset_index(drop=True, inplace=True)
    jobs = df.to_dict("records")
    return jsonify(jobs)


@app.route("/job_details/<int:job_id>")
def job_details(job_id):
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            cursorclass=pymysql.cursors.DictCursor,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        conn.close()
        if job is not None:
            return jsonify(job)
        else:
            return jsonify({"error": "Job not found"}), 404
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job_tuple = cursor.fetchone()
        conn.close()
        if job_tuple is not None:
            # Get the column names from the cursor description
            column_names = [column[0] for column in cursor.description]
            # Create a dictionary mapping column names to row values
            job = dict(zip(column_names, job_tuple))
            return jsonify(job)
        else:
            return jsonify({"error": "Job not found"}), 404


@app.route("/hide_job/<int:job_id>", methods=["POST"])
def hide_job(job_id):
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET hidden = 1 WHERE id = %s", (job_id,))
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET hidden = 1 WHERE id = ?", (job_id,))

    conn.commit()
    conn.close()
    return jsonify({"success": "Job marked as hidden"}), 200


@app.route("/mark_applied/<int:job_id>", methods=["POST"])
def mark_applied(job_id):
    print("Applied clicked!")
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()
        query = "UPDATE jobs SET applied = 1 WHERE id = %s"
        print(f"Executing query: {query} with job_id: {job_id}")  # Log the query
        cursor.execute(query, (job_id,))
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        query = "UPDATE jobs SET applied = 1 WHERE id = ?"
        print(f"Executing query: {query} with job_id: {job_id}")  # Log the query
        cursor.execute(query, (job_id,))

    conn.commit()
    conn.close()
    return jsonify({"success": "Job marked as applied"}), 200


@app.route("/mark_interview/<int:job_id>", methods=["POST"])
def mark_interview(job_id):
    print("Interview clicked!")
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()
        query = "UPDATE jobs SET interview = 1 WHERE id = %s"
        print(f"Executing query: {query} with job_id: {job_id}")
        cursor.execute(query, (job_id,))
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        query = "UPDATE jobs SET interview = 1 WHERE id = ?"
        print(f"Executing query: {query} with job_id: {job_id}")
        cursor.execute(query, (job_id,))

    conn.commit()
    conn.close()
    return jsonify({"success": "Job marked as interview"}), 200


@app.route("/mark_rejected/<int:job_id>", methods=["POST"])
def mark_rejected(job_id):
    print("Rejected clicked!")
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()
        query = "UPDATE jobs SET rejected = 1 WHERE id = %s"
        print(f"Executing query: {query} with job_id: {job_id}")
        cursor.execute(query, (job_id,))
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        query = "UPDATE jobs SET rejected = 1 WHERE id = ?"
        print(f"Executing query: {query} with job_id: {job_id}")
        cursor.execute(query, (job_id,))

    conn.commit()
    conn.close()
    return jsonify({"success": "Job marked as rejected"}), 200


@app.route("/toggle_star/<int:job_id>", methods=["POST"])
def toggle_star(job_id):
    print("Star toggled!")
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()
        
        # First get current starred status
        cursor.execute("SELECT starred FROM jobs WHERE id = %s", (job_id,))
        result = cursor.fetchone()
        current_status = result[0] if result and result[0] is not None else 0
        
        # Toggle the status
        new_status = 0 if current_status == 1 else 1
        
        query = "UPDATE jobs SET starred = %s WHERE id = %s"
        print(f"Executing query: {query} with job_id: {job_id} and starred: {new_status}")
        cursor.execute(query, (new_status, job_id))
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        
        # First get current starred status
        cursor.execute("SELECT starred FROM jobs WHERE id = ?", (job_id,))
        result = cursor.fetchone()
        current_status = result[0] if result and result[0] is not None else 0
        
        # Toggle the status
        new_status = 0 if current_status == 1 else 1
        
        query = "UPDATE jobs SET starred = ? WHERE id = ?"
        print(f"Executing query: {query} with job_id: {job_id} and starred: {new_status}")
        cursor.execute(query, (new_status, job_id))

    conn.commit()
    conn.close()
    return jsonify({"success": "Job star toggled", "starred": new_status}), 200


@app.route("/get_notes/<int:job_id>")
def get_notes(job_id):
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()
        cursor.execute("SELECT notes FROM jobs WHERE id = %s", (job_id,))
        notes = cursor.fetchone()
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        cursor.execute("SELECT notes FROM jobs WHERE id = ?", (job_id,))
        notes = cursor.fetchone()

    conn.close()
    if notes is not None:
        return jsonify({"notes": notes[0] if notes[0] else ""})
    else:
        return jsonify({"notes": ""}), 200


@app.route("/get_resume/<int:job_id>", methods=["POST"])
def get_resume(job_id):
    print("Resume clicked!")
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            cursorclass=pymysql.cursors.DictCursor,
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_description, title, company FROM jobs WHERE id = %s", (job_id,)
        )
        job = cursor.fetchone()
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_description, title, company FROM jobs WHERE id = ?", (job_id,)
        )
        job_tuple = cursor.fetchone()
        if job_tuple is not None:
            # Get the column names from the cursor description
            column_names = [column[0] for column in cursor.description]
            # Create a dictionary mapping column names to row values
            job = dict(zip(column_names, job_tuple))
    resume = read_pdf(config["resume_path"])

    # Check if OpenAI API key is empty
    if not config["OpenAI_API_KEY"]:
        print("Error: OpenAI API key is empty.")
        return jsonify({"error": "OpenAI API key is empty."}), 400

    openai.api_key = config["OpenAI_API_KEY"]
    consideration = ""
    user_prompt = (
        "You are a career coach with a client that is applying for a job as a "
        + job["title"]
        + " at "
        + job["company"]
        + ". They have a resume that you need to review and suggest how to tailor it for the job. "
        "Approach this task in the following steps: \n 1. Highlight three to five most important responsibilities for this role based on the job description. "
        "\n2. Based on these most important responsibilities from the job description, please tailor the resume for this role. Do not make information up. "
        "Respond with the final resume only. \n\n Here is the job description: "
        + job["job_description"]
        + "\n\n Here is the resume: "
        + resume
    )
    if consideration:
        user_prompt += "\nConsider incorporating that " + consideration

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        response = completion.choices[0].message.content
    except Exception as e:
        print(f"Error connecting to OpenAI: {e}")
        return jsonify({"error": f"Error connecting to OpenAI: {e}"}), 500

    if config.get("db_type", "sqlite") == "mysql":
        query = "UPDATE jobs SET resume = %s WHERE id = %s"
        print(f"Executing query: {query} with job_id: {job_id} and resume: {response}")
        cursor.execute(query, (response, job_id))
    else:
        query = "UPDATE jobs SET resume = ? WHERE id = ?"
        print(f"Executing query: {query} with job_id: {job_id} and resume: {response}")
        cursor.execute(query, (response, job_id))
    conn.commit()
    conn.close()
    return jsonify({"resume": response}), 200


@app.route("/save_notes/<int:job_id>", methods=["POST"])
def save_notes(job_id):
    print("Saving notes!")
    
    # Get the notes from the request
    data = request.get_json()
    notes = data.get('notes', '')
    
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()
        query = "UPDATE jobs SET notes = %s WHERE id = %s"
        print(f"Executing query: {query} with job_id: {job_id} and notes: {notes}")
        cursor.execute(query, (notes, job_id))
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()
        query = "UPDATE jobs SET notes = ? WHERE id = ?"
        print(f"Executing query: {query} with job_id: {job_id} and notes: {notes}")
        cursor.execute(query, (notes, job_id))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "notes": notes}), 200


def read_jobs_from_db():
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection using SQLAlchemy for pandas
        engine = create_engine(
            f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}",
            pool_recycle=3600,
        )
        query = "SELECT * FROM jobs WHERE hidden = 0"
        df = pd.read_sql_query(query, engine)
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        query = "SELECT * FROM jobs WHERE hidden = 0"
        df = pd.read_sql_query(query, conn)

    # df = df.sort_values(by="id", ascending=False)
    df = df.sort_values(by=["date", "id"], ascending=[False, False])
    # df.reset_index(drop=True, inplace=True)
    return df.to_dict("records")


def verify_db_schema():
    if config.get("db_type", "sqlite") == "mysql":
        # MySQL connection
        conn = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
        )
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute(
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{config['database']}' AND table_name = 'jobs'"
        )
        if cursor.fetchone()[0] == 1:
            # Check if columns exist
            cursor.execute("SHOW COLUMNS FROM jobs LIKE 'notes'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE jobs ADD COLUMN notes TEXT")
                print("Added notes column to jobs table")

            cursor.execute("SHOW COLUMNS FROM jobs LIKE 'resume'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE jobs ADD COLUMN resume TEXT")
                print("Added resume column to jobs table")

            cursor.execute("SHOW COLUMNS FROM jobs LIKE 'seniority_level'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE jobs ADD COLUMN seniority_level TEXT")
                print("Added seniority_level column to jobs table")

            cursor.execute("SHOW COLUMNS FROM jobs LIKE 'employment_type'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE jobs ADD COLUMN employment_type TEXT")
                print("Added employment_type column to jobs table")

            cursor.execute("SHOW COLUMNS FROM jobs LIKE 'job_function'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE jobs ADD COLUMN job_function TEXT")
                print("Added job_function column to jobs table")

            cursor.execute("SHOW COLUMNS FROM jobs LIKE 'industries'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE jobs ADD COLUMN industries TEXT")
                print("Added industries column to jobs table")
    else:
        # SQLite connection
        conn = sqlite3.connect(config["db_path"])
        cursor = conn.cursor()

        # Get the table information
        cursor.execute("PRAGMA table_info(jobs)")
        table_info = cursor.fetchall()

        # Check if the "notes" column exists
        if "notes" not in [column[1] for column in table_info]:
            # If it doesn't exist, add it
            cursor.execute("ALTER TABLE jobs ADD COLUMN notes TEXT")
            print("Added notes column to jobs table")

        if "resume" not in [column[1] for column in table_info]:
            # If it doesn't exist, add it
            cursor.execute("ALTER TABLE jobs ADD COLUMN resume TEXT")
            print("Added resume column to jobs table")

        if "seniority_level" not in [column[1] for column in table_info]:
            # If it doesn't exist, add it
            cursor.execute("ALTER TABLE jobs ADD COLUMN seniority_level TEXT")
            print("Added seniority_level column to jobs table")

        if "employment_type" not in [column[1] for column in table_info]:
            # If it doesn't exist, add it
            cursor.execute("ALTER TABLE jobs ADD COLUMN employment_type TEXT")
            print("Added employment_type column to jobs table")

        if "job_function" not in [column[1] for column in table_info]:
            # If it doesn't exist, add it
            cursor.execute("ALTER TABLE jobs ADD COLUMN job_function TEXT")
            print("Added job_function column to jobs table")

        if "industries" not in [column[1] for column in table_info]:
            # If it doesn't exist, add it
            cursor.execute("ALTER TABLE jobs ADD COLUMN industries TEXT")
            print("Added industries column to jobs table")

    conn.close()


if __name__ == "__main__":
    verify_db_schema()  # Verify the DB schema before running the app
    app.run(debug=True, host="0.0.0.0", port=5001)
