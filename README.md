# buy-бизнесмания

## Project Overview
This project is a web application built using Flask. It is designed to scrape market data from a specified website and provide an interface for users to access this data.

## Files

- **app.py**: The main application file that contains the Flask application setup, route definitions, and logic for handling requests and responses.

- **requirements.txt**: A file that lists the Python dependencies required for the project. It specifies the packages and their versions that need to be installed for the application to run.

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd buy-бизнесмания
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

## Usage
Once the application is running, you can access it in your web browser at `http://127.0.0.1:5050/market`.

## Environment variables
Create a `.env` file in the `BOT` folder (you can copy `.env.example`) and set at least `API_TOKEN`.

Example `.env` (BOT/.env):
```
API_TOKEN=your_telegram_token_here
MARKET_DATA_FILE=market_data.json
SENT_UNITS_FILE=sent_units.json
```

## Logging
The application logs important events and errors. Check the console output for logging information.

## License
This project is licensed under the MIT License. See the LICENSE file for details.