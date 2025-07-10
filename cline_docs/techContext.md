# Technical Context

## Technologies Used

*   **Backend Framework**: Python with FastAPI
*   **Web Server**: Uvicorn
*   **Database**: Supports both MySQL and SQLite.
*   **Containerization**: Docker
*   **Frontend**: HTML, CSS, JavaScript (for the status and configuration pages)

## Development Setup

1.  **Prerequisites**:
    *   Python 3.9+
    *   `pip` for package management

2.  **Installation**:
    *   Clone the repository.
    *   Install dependencies from `requirements.txt`:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Configuration**:
    *   Create a `.env` file in the project root.
    *   Populate the `.env` file with necessary configurations, such as database credentials, API keys, and other settings as detailed in the `README.md`.

4.  **Running the Application**:
    *   **Development**: Use `uvicorn` to run the application with auto-reload.
        ```bash
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```
    *   **Production (Docker)**:
        *   Build the Docker image: `docker build -t gemini-gateway .`
        *   Run the container: `docker run -d -p 8000:8000 --env-file .env gemini-gateway`

## Technical Constraints

*   The application is designed to be stateless to facilitate horizontal scaling, with the exception of the database.
*   The primary dependency is the Google Gemini API. Any changes or outages in the Gemini API will directly impact this application.
*   The application relies on external services for image hosting (`smms`, `picgo`, `cloudflare_imgbed`) if image generation is used. The availability of these services is a constraint.
*   The application's performance is dependent on the network latency to the Gemini API and the configured proxy servers.
