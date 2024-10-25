import json
import os
import threading
import time
from flask import Flask, render_template, request, jsonify
from job_scraper import load_config, save_config, job_scraper
import logging
from io import StringIO

app = Flask(__name__)

app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)