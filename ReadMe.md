# AI-Powered Excel Mock Interviewer - PoC

This is a Proof-of-Concept for an AI-powered agent that conducts a technical screening interview for Microsoft Excel skills. This system is designed to be modular, intelligent, and provide a realistic interview experience.

## Overview & Key Features

This application simulates a real interview by asking a candidate a series of questions and providing a detailed performance report with constructive feedback.

-   **Intelligent Interview Pacing:** The interview length is fixed (e.g., 8 questions) but the questions are **randomly sampled** from a larger knowledge base. This ensures fairness, prevents cheating, and provides a unique experience for each candidate.
-   **Decoupled Knowledge Base:** All interview questions, along with their topics, difficulties, and evaluation rubrics, are stored in an external `interview_questions.json` file. This separates the interview content from the application logic, making it easy to maintain and scale.
-   **AI-Powered Evaluation:** Each answer is evaluated in real-time by an LLM against an expert-defined rubric, providing a score and justification.
-   **Comprehensive Final Report:** At the end of the session, a full performance summary is generated, outlining strengths, areas for improvement, and a final recommendation.

## Technology Stack

-   **Framework:** Streamlit
-   **Language:** Python
-   **AI/LLM:** Google Gemini API
-   **Knowledge Base:** A structured `interview_questions.json` file.
-   **Deployment:** Streamlit Community Cloud

## How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/johankaibutsu/ai-interviewer-excel.git
    cd ai-interviewer-excel
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up your API Key:**
    Edit the file `.streamlit/secrets.toml` and add your key:
    ```toml
    GOOGLE_API_KEY = "AIza..."
    ```
4.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

## Working Demo
