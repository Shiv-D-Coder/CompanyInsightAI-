# CompanyInsightAI

## Overview

CompanyInsightAI is a web application that analyzes news sentiment for a given company, providing a comprehensive summary, sentiment distribution, topic analysis, and comparative analysis. It leverages news scraping, sentiment analysis, and large language models to deliver insightful information.

## Links

-   **GitHub Repository:** [https://github.com/Shiv-D-Coder/CompanyInsightAI-](https://github.com/Shiv-D-Coder/CompanyInsightAI-)
-   **Deployed Application:** [https://companyinsightai.streamlit.app/](https://companyinsightai.streamlit.app/)
-   **Hugging Face Spaces:** [https://huggingface.co/spaces/Shiv-D-Coder/CompanyInsightAI](https://huggingface.co/spaces/Shiv-D-Coder/CompanyInsightAI)

## Features

*   **News Scraping:** Fetches the latest news articles from Google News based on the company name.
*   **Sentiment Analysis:** Analyzes the sentiment of each news article (Positive, Negative, Neutral).
*   **Topic Extraction:** Identifies the main topics discussed in the articles.
*   **Comparative Analysis:** Compares different aspects of news coverage.
*   **Comprehensive Summary:** Generates a summary of the news articles, highlighting overall sentiment and key topics, using the Groq API (with local fallback).
*   **Audio Summary:** Provides an audio summary of the news in multiple languages.
*   **Multilingual Support:** Supports multiple languages for the summary and audio output.
*   **API Key Integration:** Allows users to use their own Groq API key for summarization.

## Technologies Used

*   **Frontend:** Streamlit
*   **Backend:** FastAPI
*   **News Scraping:** BeautifulSoup
*   **Sentiment Analysis:** TextBlob, VADER
*   **Text-to-Speech:** gTTS
*   **Large Language Model:** Groq API (Mixtral-8x7B)
*   **Other:** Python, `python-dotenv`

## Setup and Installation

1.  **Clone the repository:**

    ```
    git clone https://github.com/Shiv-D-Coder/CompanyInsightAI-.git
    cd CompanyInsightAI-
    ```

2.  **Create a virtual environment (recommended):**

    ```
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the dependencies:**

    ```
    pip install -r requirements.txt
    ```

4.  **Environment Variables:**

    *   Create a `.env` file in the root directory.
    *   Add your Groq API key (optional, but recommended for better summarization):

        ```
        GROQ_API_KEY=YOUR_GROQ_API_KEY
        ```

    *   If you don't have a Groq API key, the application will use a local summarization fallback.

5.  **Running the application:**

    *   **Backend (API):**

        ```
        cd CompanyInsightAI- #Make sure you are on the root directory
        uvicorn api:app --reload
        ```

        *   This will start the FastAPI backend server.

    *   **Frontend (Streamlit):**

        ```
        cd CompanyInsightAI- #Make sure you are on the root directory
        streamlit run app.py
        ```

        *   This will open the Streamlit application in your web browser.

## Usage

1.  **Enter a company name** in the text input field.
2.  **Configure settings** in the sidebar, such as:

    *   Summary Length (Short, Medium, Long)
    *   Language (English, Hindi, Spanish, French, German, Chinese)
    *   Groq API Key (optional)

3.  Click the "Analyze" button.
4.  The application will display:

    *   An audio summary of the news.
    *   A text summary of the news.
    *   Sentiment distribution (Positive, Negative, Neutral).
    *   Topic distribution.
    *   A list of the analyzed articles with summaries, sources, and sentiment.
    *   Comparative analysis of news coverage.

## File Structure

CompanyInsightAI/
├── api.py # FastAPI backend application

├── app.py # Streamlit frontend application

├── utils.py # Utility functions for scraping, sentiment analysis, etc.

├── requirements.txt # Python dependencies

├── .env # Environment variables (API keys)

├── README.md # Documentation

└── venv/ # Virtual environment (optional)

text

## API Endpoints (api.py)

*   `/`:  Welcome message.
*   `/analyze`:  Analyzes news sentiment for a given company.  Takes a JSON payload with the following structure:

    ```
    {
      "company": "Tesla",
      "language": "en",
      "summary_length": 400
    }
    ```

    Returns a JSON response with the analysis results.

## Environment Variables

*   `GROQ_API_KEY`:  (Optional) API key for the Groq API. If not set, a local summarization fallback is used.

## Dependencies

The project uses the following main dependencies:

*   `fastapi`: For creating the API.
*   `streamlit`: For creating the web application.
*   `requests`: For making HTTP requests.
*   `beautifulsoup4`: For web scraping.
*   `textblob`: For sentiment analysis.
*   `vaderSentiment`: For sentiment analysis.
*   `gTTS`: For text-to-speech conversion.
*   `python-dotenv`: For loading environment variables from a `.env` file.

## Contributing

Contributions are welcome! Please feel free to submit pull requests to improve the project.

## Author

Shiv Patel - [https://github.com/Shiv-D-Coder](https://github.com/Shiv-D-Coder)
