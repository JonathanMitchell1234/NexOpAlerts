# Job Scraper Dashboard

## Overview

The Job Scraper Dashboard is a web application designed to automate the process of scraping job listings from various job sites, filtering them based on user-defined criteria, and sending email notifications for new job listings. The application is built using Flask for the web interface and various Python libraries for job scraping and email notifications.

## Features

-   **Job Scraping**: Scrapes job listings from multiple job sites.

-   **Filtering**: Filters job listings based on company names and keywords.

-   **Email Notifications**: Sends email notifications with new job listings.

-   **Configuration**: Allows users to update search terms, location, filter criteria, and run intervals via a web interface.

-   **Logging**: Captures and displays logs for monitoring the scraper's activity.

## Installation

1.  **Clone the repository**:

```sh

git clone https://github.com/yourusername/job-scraper-dashboard.git

cd job-scraper-dashboard

```

2.  **Set up a virtual environment**:

```sh

python3 -m venv path/to/venv

source path/to/venv/bin/activate

```

3.  **Install dependencies**:

```sh

pip install -r requirements.txt

```

4.  **Set up environment variables**:

Create a .env file in the root directory with the following content:

```properties

SENDER_EMAIL=your_email@gmail.com

SENDER_PASSWORD=your_email_password

RECIPIENT_EMAIL=recipient_email@gmail.com

```

5.  **Run the application**:

```sh

python3 web_app.py

```

## Usage

1.  **Access the Dashboard**:

-   Open your web browser and navigate to `http://localhost:5002`.

2.  **Update Configuration**:

-   Enter search terms, location, companies to filter out, words to filter out, and run interval.

-   Click "Update Configuration" to save the settings.

3.  **Control the Scraper**:

-   Click "Start Scraper" to start the job scraper.

-   Click "Stop Scraper" to stop the job scraper.

4.  **View Logs**:

-   The logs section will display real-time logs of the scraper's activity.

## Configuration

The configuration is stored in

config.json

. You can update the configuration via the web interface or manually by editing the file.

## Logging

Logs are captured and displayed in the "Scraper Logs" section of the dashboard. They provide real-time feedback on the scraper's activity, including any errors encountered.

## Contributing

1.  **Fork the repository**.

2.  **Create a new branch**:

```sh

git checkout -b feature/your-feature-name

```

3.  **Commit your changes**:

```sh

git commit -m 'Add some feature'

```

4.  **Push to the branch**:

```sh

git push origin feature/your-feature-name

```

5.  **Open a pull request**.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For any questions or suggestions, please open an issue or contact the repository owner.

---
