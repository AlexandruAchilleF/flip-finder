# Flip Finder - Bacău Real Estate Radar

An automated end-to-end ETL (Extract, Transform, Load) system designed to monitor the real estate market in Bacău. The project scrapes daily data from OLX, tracks price fluctuations for each apartment, and sends automated alerts, while providing an interactive cloud dashboard for analysis.

## System Architecture

The project is divided into 4 main components:

1. **Extract:** A Python scraper that queries the OLX API, navigates through pages (pagination), and extracts real estate listings.
2. **Transform:** Using Pandas, the data is cleaned, prices are standardized in Euros (applying correction filters for user errors), and neighborhoods are mapped.
3. **Load:** The data is loaded into a serverless relational database (Neon PostgreSQL), maintaining a price history.
4. **Visualize & Alert:** 
   - An interactive dashboard built with Streamlit, deployed in the cloud.
   - A Telegram Bot that sends a detailed daily report with prices that have increased or decreased.

## Technologies Used

* **Language:** Python 3.14
* **Data Manipulation:** Pandas, Requests
* **Database:** PostgreSQL (hosted on Neon.tech), Psycopg2
* **Frontend:** Streamlit, Streamlit Cloud
* **Automation (CI/CD):** GitHub Actions (Cron Jobs)
* **Notifications:** Telegram Bot API

## Key Features

* **Price History Tracking:** The database links the apartment ID to its price fluctuations over time.
* **Interactive Filters:** The dashboard allows dynamic filtering of over 700 listings by neighborhoods and price ranges.
* **Automated Execution:** The system runs automatically every morning at 08:17 via GitHub Actions.
* **Security:** Database and Telegram bot credentials are strictly managed through Environment Variables (local `.env`, GitHub Secrets in the cloud).

## Setup Instructions (Local)

To run this project:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/AlexandruAchilleF/flip-finder.git](https://github.com/AlexandruAchilleF/flip-finder.git)
   cd flip-finder

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   Create a .env file in the main folder and add the following credentials:
   ```text
   DATABASE_URL=...
   TELEGRAM_TOKEN=...
   TELEGRAM_CHAT_ID=...
   ```

4. **Run the scraper manually:**
   ```bash
   python scraper.py
   ```

5. **Start the local Dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

## GitHub Actions Configuration (Cloud)
For daily automation, make sure you have added the 3 variables from the .env file into the Settings > Secrets and variables > Actions > Repository secrets section of your GitHub repository.
