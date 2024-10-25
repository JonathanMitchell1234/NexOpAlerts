import csv
import os
import pandas as pd
from jobspy import scrape_jobs
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import schedule
import time
from itertools import cycle
from dotenv import load_dotenv
import re
import json
import argparse
import logging
from tqdm import tqdm

# Load the environmental variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Email configuration
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# Configuration file
CONFIG_FILE = 'config.json'

# Default configuration
DEFAULT_CONFIG = {
    "search_terms": [],
    "location": "",
    "filter_companies": [],
    "filter_words": [],
    "interval_run": 180,
    "proxies": [
        "172.173.132.85:80",
        "98.181.137.80:4145",
        "208.65.90.21:4145",
        "74.119.147.209:4145",
        "208.102.51.6:58208",
        "199.229.254.129:4145"
    ]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def send_email(new_jobs, search_term):
    subject = f"New Job Listings Found for {search_term}!"
    body = f"{len(new_jobs)} new jobs were found for the search term '{search_term}'."
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    filename = 'new_jobs.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Title', 'Company', 'Location', 'Date Posted', 'Job URL'])
        for _, job in new_jobs.iterrows():
            writer.writerow([
                job['title'],
                job['company'],
                job['location'],
                job['date_posted'],
                job['job_url']
            ])

    attachment = open(filename, 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {filename}")
    msg.attach(part)

    text = msg.as_string()

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)
        server.quit()
        logger.info(f"Email sent successfully for search term: {search_term}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

def filter_new_jobs(new_jobs, filter_companies, filter_words):
    unique_columns = ['title', 'company', 'job_url']

    def job_filter(row):
        title = str(row['title']).lower() if pd.notna(row['title']) else ""
        company = str(row['company']).lower() if pd.notna(row['company']) else ""
        title_words = set(re.findall(r'\b\w+\b', title))
        return not any(word in title_words for word in filter_words) and company not in [c.lower() for c in filter_companies]

    new_jobs = new_jobs[new_jobs.apply(job_filter, axis=1)]

    if os.path.exists('sent_jobs.csv'):
        sent_jobs = pd.read_csv('sent_jobs.csv')
        for col in unique_columns:
            if col not in new_jobs.columns or col not in sent_jobs.columns:
                logger.warning(f"Column '{col}' not found. Skipping filtering.")
                return new_jobs

        new_jobs.loc[:, 'job_url'] = new_jobs['job_url'].astype(str)
        sent_jobs['job_url'] = sent_jobs['job_url'].astype(str)

        new_jobs_set = set(new_jobs[unique_columns].apply(tuple, axis=1))
        sent_jobs_set = set(sent_jobs[unique_columns].apply(tuple, axis=1))
        new_jobs_tuples = new_jobs_set - sent_jobs_set

        filtered_jobs = new_jobs[new_jobs[unique_columns].apply(tuple, axis=1).isin(new_jobs_tuples)]
    else:
        filtered_jobs = new_jobs

    pd.concat([pd.read_csv('sent_jobs.csv') if os.path.exists('sent_jobs.csv') else pd.DataFrame(),
               filtered_jobs]).drop_duplicates(subset=unique_columns, keep='last').to_csv('sent_jobs.csv', index=False)

    logger.info(f"Filtered {len(new_jobs) - len(filtered_jobs)} duplicate or unwanted jobs")
    return filtered_jobs

def scrape_with_retry(search_term, location, proxy, proxy_type):
    retries = 5
    for attempt in range(retries):
        try:
            logger.info(f"Attempting scrape with proxy: {proxy} ({proxy_type})")
            jobs = scrape_jobs(
                site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor"],
                search_term=search_term,
                location=location,
                results_wanted=100,
                hours_old=72,
                country_indeed='USA',
                linkedin_fetch_description=True,
                proxy=proxy,
                proxy_type=proxy_type
            )
            logger.info(f"Successfully scraped {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.error(f"Error during scraping with proxy {proxy}: {e}. Retrying in 60 seconds...")
            time.sleep(60)
    raise Exception("Max retries exceeded")

def job_scraper(config):
    logger.info("Starting job scraper")
    proxy_cycle = cycle(config['proxies'])
    for search_term in config['search_terms']:
        logger.info(f"Processing search term: {search_term}")
        proxy = next(proxy_cycle)
        proxy_type = "SOCKS5" if ":4145" in proxy else "HTTP"

        try:
            jobs = scrape_with_retry(search_term, config['location'], proxy, proxy_type)
            logger.info(f"Found {len(jobs)} jobs for {search_term}")

            new_jobs = filter_new_jobs(jobs, config['filter_companies'], config['filter_words'])

            if not new_jobs.empty:
                send_email(new_jobs, search_term)
                logger.info(f"Sent email with {len(new_jobs)} new jobs for {search_term}")
            else:
                logger.info(f"No new jobs found for {search_term}")
        except Exception as e:
            logger.error(f"An error occurred while processing {search_term}: {e}")
    
    logger.info("Job scraper cycle completed")

def update_config():
    config = load_config()
    print("Current configuration:")
    print(json.dumps(config, indent=2))
    
    search_terms = input("Enter search terms (comma-separated): ").split(',')
    location = input("Enter location: ")
    filter_companies = input("Enter companies to filter out (comma-separated): ").split(',')
    filter_words = input("Enter words to filter out (comma-separated): ").split(',')
    interval_run = int(input("Enter interval run time in minutes: "))
    
    config.update({
        "search_terms": search_terms,
        "location": location,
        "filter_companies": filter_companies,
        "filter_words": filter_words,
        "interval_run": interval_run
    })
    
    save_config(config)
    print("Configuration updated successfully.")

def main():
    parser = argparse.ArgumentParser(description="Job Scraper")
    parser.add_argument("--config", action="store_true", help="Update configuration")
    parser.add_argument("--run", action="store_true", help="Run the job scraper")
    args = parser.parse_args()

    if args.config:
        update_config()
    elif args.run:
        config = load_config()
        job_scraper(config)
        schedule.every(config['interval_run']).minutes.do(job_scraper, config)
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()