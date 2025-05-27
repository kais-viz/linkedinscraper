import requests
import json
import sys
import pymysql
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import time as tm
from itertools import groupby
from datetime import datetime, timedelta, time
import pandas as pd
from urllib.parse import quote
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


def load_config(file_name):
    # Load the config file
    with open(file_name) as f:
        return json.load(f)


def get_with_retry(url, config, retries=3, delay=1):
    # Get the URL with retries and delay
    for i in range(retries):
        try:
            if len(config["proxies"]) > 0:
                r = requests.get(
                    url, headers=config["headers"], proxies=config["proxies"], timeout=5
                )
            else:
                r = requests.get(url, headers=config["headers"], timeout=5)
                # save to file for debugging
                output_file = open("linkedin_jobs_output.txt", "w")
                output_file.write(r.text)
                output_file.close()
            return BeautifulSoup(r.content, "html.parser")
        except requests.exceptions.Timeout:
            print(f"Timeout occurred for URL: {url}, retrying in {delay}s...")
            tm.sleep(delay)
        except Exception as e:
            print(f"An error occurred while retrieving the URL: {url}, error: {e}")
    return None


def transform(soup):
    # Parsing the job card info (title, company, location, date, job_url) from the beautiful soup object
    joblist = []
    try:
        divs = soup.find_all("div", class_="base-search-card__info")
    except:
        print("Empty page, no jobs found")
        return joblist
    for item in divs:
        title = item.find("h3").text.strip()
        company = item.find("a", class_="hidden-nested-link")
        location = item.find("span", class_="job-search-card__location")
        parent_div = item.parent
        entity_urn = parent_div["data-entity-urn"]
        job_posting_id = entity_urn.split(":")[-1]
        job_url = "https://www.linkedin.com/jobs/view/" + job_posting_id + "/"

        date_tag_new = item.find("time", class_="job-search-card__listdate--new")
        date_tag = item.find("time", class_="job-search-card__listdate")
        date = (
            date_tag["datetime"]
            if date_tag
            else date_tag_new["datetime"] if date_tag_new else ""
        )
        job_description = ""
        job = {
            "title": title,
            "company": company.text.strip().replace("\n", " ") if company else "",
            "location": location.text.strip() if location else "",
            "date": date,
            "job_url": job_url,
            "job_description": job_description,
            "applied": 0,
            "hidden": 0,
            "interview": 0,
            "rejected": 0,
        }
        joblist.append(job)
    return joblist


import html2markdown

def transform_job(soup):
    # Extract job description
    div = soup.find("div", class_="description__text description__text--rich")
    job_description = ""
    if div:
        # Remove unwanted elements
        for element in div.find_all(["span"]):
            element.decompose()
            
        # Remove "Show less" and "Show more" links
        for a in div.find_all("a"):
            if "Show less" in a.text or "Show more" in a.text:
                a.decompose()
            
        # Get the HTML content
        html_content = str(div)
        
        # Convert HTML to Markdown to preserve formatting
        markdown_content = html2markdown.convert(html_content)
        
        # Clean up the markdown
        markdown_content = markdown_content.replace("::marker", "-")
        markdown_content = markdown_content.strip()
        
        job_description = markdown_content
    else:
        job_description = "Could not find Job Description"
    
    # Extract job criteria (seniority level, employment type, etc.)
    job_criteria = {}
    criteria_list = soup.find("ul", class_="description__job-criteria-list")
    
    if criteria_list:
        for item in criteria_list.find_all("li", class_="description__job-criteria-item"):
            header = item.find("h3", class_="description__job-criteria-subheader")
            text = item.find("span", class_="description__job-criteria-text")
            
            if header and text:
                key = header.text.strip().lower().replace(' ', '_')
                value = text.text.strip()
                job_criteria[key] = value
    
    return {
        "description": job_description,
        "criteria": job_criteria
    }


def safe_detect(text):
    try:
        return detect(text)
    except LangDetectException:
        return "en"


def remove_irrelevant_jobs(joblist, config):
    # Filter out jobs based on description, title, and language. Set up in config.json.
    new_joblist = [
        job
        for job in joblist
        if not any(
            word.lower() in job["job_description"].lower()
            for word in config["desc_words"]
        )
    ]
    new_joblist = (
        [
            job
            for job in new_joblist
            if not any(
                word.lower() in job["title"].lower() for word in config["title_exclude"]
            )
        ]
        if len(config["title_exclude"]) > 0
        else new_joblist
    )
    new_joblist = (
        [
            job
            for job in new_joblist
            if any(
                word.lower() in job["title"].lower() for word in config["title_include"]
            )
        ]
        if len(config["title_include"]) > 0
        else new_joblist
    )
    new_joblist = (
        [
            job
            for job in new_joblist
            if safe_detect(job["job_description"]) in config["languages"]
        ]
        if len(config["languages"]) > 0
        else new_joblist
    )
    new_joblist = (
        [
            job
            for job in new_joblist
            if not any(
                word.lower() in job["company"].lower()
                for word in config["company_exclude"]
            )
        ]
        if len(config["company_exclude"]) > 0
        else new_joblist
    )
    
    # Filter out jobs based on seniority level
    new_joblist = (
        [
            job
            for job in new_joblist
            if "seniority_level" not in job or not any(
                level.lower() in job["seniority_level"].lower()
                for level in config["seniority_exclude"]
            )
        ]
        if "seniority_exclude" in config and len(config["seniority_exclude"]) > 0
        else new_joblist
    )

    return new_joblist


def remove_duplicates(joblist, config):
    # Remove duplicate jobs in the joblist. Duplicate is defined as having the same title and company.
    joblist.sort(key=lambda x: (x["title"], x["company"]))
    joblist = [
        next(g) for k, g in groupby(joblist, key=lambda x: (x["title"], x["company"]))
    ]
    return joblist


def convert_date_format(date_string):
    """
    Converts a date string to a date object.

    Args:
        date_string (str): The date in string format.

    Returns:
        date: The converted date object, or None if conversion failed.
    """
    date_format = "%Y-%m-%d"
    try:
        job_date = datetime.strptime(date_string, date_format).date()
        return job_date
    except ValueError:
        print(f"Error: The date for job {date_string} - is not in the correct format.")
        return None


def create_connection(config):
    # Create a database connection to a MySQL database
    conn = None
    try:
        if config.get("db_type", "sqlite") == "mysql":
            # MySQL connection
            conn = pymysql.connect(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                database=config["database"],
            )
        else:
            # Fallback to SQLite for backward compatibility
            import sqlite3

            conn = sqlite3.connect(config["db_path"])
    except Exception as e:
        print(f"Error connecting to database: {e}")

    return conn


def create_table(conn, df, table_name):
    # Create a new table with the data from the DataFrame
    config = load_config("config.json")

    if config.get("db_type", "sqlite") == "mysql":
        # MySQL data type mapping
        type_mapping = {
            "int64": "INT",
            "float64": "FLOAT",
            "datetime64[ns]": "DATETIME",
            "object": "TEXT",
            "bool": "TINYINT",
        }

        # Prepare a string with column names and their types
        columns_with_types = ", ".join(
            f"`{column}` {type_mapping[str(df.dtypes[column])]}"
            for column in df.columns
        )

        # Prepare SQL query to create a new table
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                date TEXT,
                job_url TEXT,
                job_description TEXT,
                applied INT DEFAULT 0,
                hidden INT DEFAULT 0,
                interview INT DEFAULT 0,
                rejected INT DEFAULT 0,
                seniority_level TEXT,
                employment_type TEXT,
                job_function TEXT,
                industries TEXT,
                date_loaded TEXT
            );
        """

        # Execute SQL query
        cursor = conn.cursor()
        cursor.execute(create_table_sql)

        # Commit the transaction
        conn.commit()

        # Insert DataFrame records one by one
        placeholders = ", ".join(["%s" for _ in df.columns])
        insert_sql = f"""
            INSERT INTO `{table_name}` ({', '.join(f'`{column}`' for column in df.columns)})
            VALUES ({placeholders})
        """

        for record in df.to_dict(orient="records"):
            cursor.execute(insert_sql, list(record.values()))

        # Commit the transaction
        conn.commit()
    else:
        # SQLite implementation (original code)
        type_mapping = {
            "int64": "INTEGER",
            "float64": "REAL",
            "datetime64[ns]": "TIMESTAMP",
            "object": "TEXT",
            "bool": "INTEGER",
        }

        columns_with_types = ", ".join(
            f'"{column}" {type_mapping[str(df.dtypes[column])]}'
            for column in df.columns
        )

        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {columns_with_types}
            );
        """

        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()

        insert_sql = f"""
            INSERT INTO "{table_name}" ({', '.join(f'"{column}"' for column in df.columns)})
            VALUES ({', '.join(['?' for _ in df.columns])})
        """
        for record in df.to_dict(orient="records"):
            cursor.execute(insert_sql, list(record.values()))

        conn.commit()

    print(f"Created the {table_name} table and added {len(df)} records")


def update_table(conn, df, table_name):
    # Update the existing table with new records.
    config = load_config("config.json")

    if config.get("db_type", "sqlite") == "mysql":
        # For MySQL, create a SQLAlchemy engine for pandas
        engine = create_engine(
            f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}",
            pool_recycle=3600,
        )
        
        # First, check if the table has all required columns
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        existing_columns = [column[0] for column in cursor.fetchall()]
        
        # Check for required columns
        required_columns = ['title', 'company', 'date', 'job_url', 'job_description']
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        # Add any missing columns
        for col in missing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN `{col}` TEXT")
            print(f"Added missing column {col} to {table_name} table")
        
        if missing_columns:
            conn.commit()
        
        # Now proceed with the update
        df_existing = pd.read_sql(f"SELECT * FROM {table_name}", engine)

        # Create a dataframe with unique records in df that are not in df_existing
        if not df_existing.empty and 'title' in df_existing.columns and 'company' in df_existing.columns and 'date' in df_existing.columns:
            df_new_records = pd.concat([df, df_existing, df_existing]).drop_duplicates(
                ["title", "company", "date"], keep=False
            )
        else:
            # If the table is empty or missing key columns, all records are new
            df_new_records = df

        # If there are new records, append them to the existing table
        if len(df_new_records) > 0:
            df_new_records.to_sql(table_name, engine, if_exists="append", index=False)
            print(f"Added {len(df_new_records)} new records to the {table_name} table")
        else:
            print(f"No new records to add to the {table_name} table")
    else:
        # Original SQLite implementation
        df_existing = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        df_new_records = pd.concat([df, df_existing, df_existing]).drop_duplicates(
            ["title", "company", "date"], keep=False
        )

        if len(df_new_records) > 0:
            df_new_records.to_sql(table_name, conn, if_exists="append", index=False)
            print(f"Added {len(df_new_records)} new records to the {table_name} table")
        else:
            print(f"No new records to add to the {table_name} table")


def table_exists(conn, table_name):
    # Check if the table already exists in the database
    config = load_config("config.json")

    cur = conn.cursor()
    if config.get("db_type", "sqlite") == "mysql":
        cur.execute(
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{config['database']}' AND table_name = '{table_name}'"
        )
    else:
        cur.execute(
            f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        )

    if cur.fetchone()[0] == 1:
        # Table exists, now check if it has the required structure
        if config.get("db_type", "sqlite") == "mysql":
            try:
                cur.execute(f"SELECT title, company, date FROM {table_name} LIMIT 1")
                cur.fetchone()  # Just to execute the query and see if it works
            except Exception as e:
                print(f"Table {table_name} exists but has incorrect structure: {e}")
                # Drop the table so it can be recreated with correct structure
                cur.execute(f"DROP TABLE {table_name}")
                conn.commit()
                return False
        return True
    return False


def job_exists(df, job):
    # Check if the job already exists in the dataframe
    if df.empty:
        return False
    # return ((df['title'] == job['title']) & (df['company'] == job['company']) & (df['date'] == job['date'])).any()
    # The job exists if there's already a job in the database that has the same URL
    return (df["job_url"] == job["job_url"]).any() | (
        (
            (df["title"] == job["title"])
            & (df["company"] == job["company"])
            & (df["date"] == job["date"])
        ).any()
    )


def get_jobcards(config):
    # Function to get the job cards from the search results page
    all_jobs = []
    for k in range(0, config["rounds"]):
        for query in config["search_queries"]:
            keywords = quote(query["keywords"])  # URL encode the keywords
            location = quote(query["location"])  # URL encode the location
            for i in range(0, config["pages_to_scrape"]):
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&f_TPR=&f_WT={query['f_WT']}&geoId=&f_TPR={config['timespan']}&start={25*i}"
                soup = get_with_retry(url, config)
                jobs = transform(soup)
                all_jobs = all_jobs + jobs
                print("Finished scraping page: ", url)
    print("Total job cards scraped: ", len(all_jobs))
    all_jobs = remove_duplicates(all_jobs, config)
    print("Total job cards after removing duplicates: ", len(all_jobs))
    all_jobs = remove_irrelevant_jobs(all_jobs, config)
    print("Total job cards after removing irrelevant jobs: ", len(all_jobs))
    return all_jobs


def find_new_jobs(all_jobs, conn, config):
    # From all_jobs, find the jobs that are not already in the database. Function checks both the jobs and filtered_jobs tables.
    jobs_tablename = config["jobs_tablename"]
    filtered_jobs_tablename = config["filtered_jobs_tablename"]
    jobs_db = pd.DataFrame()
    filtered_jobs_db = pd.DataFrame()
    if conn is not None:
        if table_exists(conn, jobs_tablename):
            query = f"SELECT * FROM {jobs_tablename}"
            jobs_db = pd.read_sql_query(query, conn)
        if table_exists(conn, filtered_jobs_tablename):
            query = f"SELECT * FROM {filtered_jobs_tablename}"
            filtered_jobs_db = pd.read_sql_query(query, conn)

    new_joblist = [
        job
        for job in all_jobs
        if not job_exists(jobs_db, job) and not job_exists(filtered_jobs_db, job)
    ]
    return new_joblist


def main(config_file):
    start_time = tm.perf_counter()
    job_list = []

    config = load_config(config_file)
    jobs_tablename = config[
        "jobs_tablename"
    ]  # name of the table to store the "approved" jobs
    filtered_jobs_tablename = config[
        "filtered_jobs_tablename"
    ]  # name of the table to store the jobs that have been filtered out based on description keywords (so that in future they are not scraped again)
    # Scrape search results page and get job cards. This step might take a while based on the number of pages and search queries.
    all_jobs = get_jobcards(config)
    conn = create_connection(config)
    # filtering out jobs that are already in the database
    all_jobs = find_new_jobs(all_jobs, conn, config)
    print("Total new jobs found after comparing to the database: ", len(all_jobs))

    if len(all_jobs) > 0:

        for job in all_jobs:
            job_date = convert_date_format(job["date"])
            job_date = datetime.combine(job_date, time())
            # if job is older than a week, skip it
            if job_date < datetime.now() - timedelta(days=config["days_to_scrape"]):
                continue
            print(
                "Found new job: ", job["title"], "at ", job["company"], job["job_url"]
            )
            desc_soup = get_with_retry(job["job_url"], config)
            job_data = transform_job(desc_soup)
            
            # Add job description
            job["job_description"] = job_data["description"]
            
            # Add job criteria if available
            criteria = job_data["criteria"]
            if "seniority_level" in criteria:
                job["seniority_level"] = criteria["seniority_level"]
            if "employment_type" in criteria:
                job["employment_type"] = criteria["employment_type"]
            if "job_function" in criteria:
                job["job_function"] = criteria["job_function"]
            if "industries" in criteria:
                job["industries"] = criteria["industries"]
            
            language = safe_detect(job["job_description"])
            if language not in config["languages"]:
                print("Job description language not supported: ", language)
                # continue
            job_list.append(job)
        # Final check - removing jobs based on job description keywords words from the config file
        jobs_to_add = remove_irrelevant_jobs(job_list, config)
        print("Total jobs to add: ", len(jobs_to_add))
        # Create a list for jobs removed based on job description keywords - they will be added to the filtered_jobs table
        filtered_list = [job for job in job_list if job not in jobs_to_add]
        df = pd.DataFrame(jobs_to_add)
        df_filtered = pd.DataFrame(filtered_list)
        df["date_loaded"] = datetime.now()
        df_filtered["date_loaded"] = datetime.now()
        df["date_loaded"] = df["date_loaded"].astype(str)
        df_filtered["date_loaded"] = df_filtered["date_loaded"].astype(str)

        if conn is not None:
            # Update or Create the database table for the job list
            if table_exists(conn, jobs_tablename):
                update_table(conn, df, jobs_tablename)
            else:
                create_table(conn, df, jobs_tablename)

            # Update or Create the database table for the filtered out jobs
            if table_exists(conn, filtered_jobs_tablename):
                update_table(conn, df_filtered, filtered_jobs_tablename)
            else:
                create_table(conn, df_filtered, filtered_jobs_tablename)
        else:
            print("Error! cannot create the database connection.")

        df.to_csv("linkedin_jobs.csv", index=False, encoding="utf-8")
        df_filtered.to_csv("linkedin_jobs_filtered.csv", index=False, encoding="utf-8")
    else:
        print("No jobs found")

    end_time = tm.perf_counter()
    print(f"Scraping finished in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    config_file = "config.json"  # default config file
    if len(sys.argv) == 2:
        config_file = sys.argv[1]

    main(config_file)
