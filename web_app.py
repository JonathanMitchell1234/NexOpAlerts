import json
import os
import threading
import time
import pandas as pd
from flask import Flask, render_template, request, jsonify
from job_scraper import load_config, save_config, job_scraper
import logging
from io import StringIO

app = Flask(__name__)

app.logger.disabled = True
log = logging.getLogger('werkzeug')
# log.disabled = True

# Global variables
scraper_thread = None
is_scraper_running = False
log_capture_string = StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logging.getLogger().addHandler(ch)
logging.getLogger().setLevel(logging.INFO)

def run_scraper():
    global is_scraper_running
    while is_scraper_running:
        try:
            config = load_config()
            logging.info("Starting job scraper cycle")
            logging.info(f"Configuration: {json.dumps(config, indent=2)}")
            
            if not config['search_terms']:
                logging.warning("No search terms defined in configuration. Skipping scraper cycle.")
            else:
                job_scraper(config)
            
            logging.info(f"Job scraper cycle completed. Sleeping for {config['interval_run']} minutes")
            time.sleep(config['interval_run'])
        except Exception as e:
            logging.error(f"An error occurred in the scraper cycle: {str(e)}")
            time.sleep(60)  # Wait for 1 minute before trying again

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', config=config, is_running=is_scraper_running)

@app.route('/update_config', methods=['POST'])
def update_config():
    config = load_config()
    form_data = request.form.to_dict()

    for key in config:
        if key in form_data:
            if key in ['search_terms', 'filter_companies', 'filter_words']:
                config[key] = [item.strip() for item in form_data[key].split(',') if item.strip()]
            elif key == 'interval_run':
                try:
                    config[key] = int(form_data[key])
                except ValueError:
                    return jsonify({"status": "error", "message": f"Invalid value for {key}. Must be an integer."})
            else:
                config[key] = form_data[key]

    save_config(config)
    logging.info(f"Configuration updated: {json.dumps(config, indent=2)}")
    return jsonify({"status": "success", "message": "Configuration updated successfully."})

@app.route('/start_scraper', methods=['POST'])
def start_scraper():
    global scraper_thread
    global is_scraper_running
    if not is_scraper_running:
        is_scraper_running = True
        scraper_thread = threading.Thread(target=run_scraper)
        scraper_thread.start()
        logging.info("Job scraper started")
        return jsonify({"status": "success", "message": "Job scraper started."})
    return jsonify({"status": "error", "message": "Job scraper is already running."})

@app.route('/stop_scraper', methods=['POST'])
def stop_scraper():
    global is_scraper_running
    if is_scraper_running:
        is_scraper_running = False
        logging.info("Job scraper stopped")
        return jsonify({"status": "success", "message": "Job scraper stopped."})
    return jsonify({"status": "error", "message": "Job scraper is not running."})

@app.route('/get_logs')
def get_logs():
    logs = log_capture_string.getvalue()
    return jsonify({"logs": logs})

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    log_capture_string.truncate(0)
    log_capture_string.seek(0)
    logging.info("Logs cleared by user")
    return jsonify({"status": "success", "message": "Logs cleared successfully."})

@app.route('/get_jobs')
def get_jobs():
    try:
        if os.path.exists('sent_jobs.csv'):
            # Read the CSV file
            jobs_df = pd.read_csv('sent_jobs.csv')
            
            # Select only the columns we want to display
            columns_to_display = ['title', 'company', 'location', 'date_posted', 'job_url', 'job_type', 'is_remote']
            display_df = jobs_df[columns_to_display].fillna('')
            
            # Convert to list of dictionaries for JSON response
            jobs_list = display_df.to_dict('records')
            
            # Sort by date posted (most recent first)
            jobs_list = sorted(jobs_list, key=lambda x: x['date_posted'] if x['date_posted'] else '', reverse=True)
            
            return jsonify({"status": "success", "jobs": jobs_list})
        else:
            return jsonify({"status": "error", "message": "No job data available"})
    except Exception as e:
        logging.error(f"Error fetching job data: {str(e)}")
        return jsonify({"status": "error", "message": f"Error fetching job data: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)