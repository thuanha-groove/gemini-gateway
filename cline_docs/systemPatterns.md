# System Patterns

## Key Technical Decisions

*   **FastAPI for the Backend**: Chosen for its high performance, asynchronous support, and automatic API documentation generation, which is ideal for building an API gateway.
*   **Modular Architecture**: The project is structured into modules (`config`, `core`, `database`, `router`, `service`, etc.) to separate concerns and improve maintainability.
*   **Environment Variable Configuration**: Using a `.env` file for configuration allows for easy setup and modification of settings without changing the code. This is a standard practice for modern applications.
*   **Database Abstraction**: The use of SQLAlchemy (implied by the models and connection logic) allows for supporting multiple database backends (MySQL, SQLite) with minimal code changes.
*   **Middleware for Core Functionality**: Middleware is used for handling cross-cutting concerns like authentication, request logging, and smart routing.

## Architecture Patterns

*   **Proxy Pattern**: The core of the application is a proxy that forwards requests to the Gemini API.
*   **Load Balancer Pattern**: The application distributes requests across multiple Gemini API keys to balance the load.
*   **Singleton Pattern**: The `KeyManager` and other service classes are likely implemented as singletons (or managed by FastAPI's dependency injection system to act like singletons) to maintain a consistent state across the application.
*   **Scheduled Tasks**: A scheduler is used to periodically check the status of disabled API keys and re-enable them if they have recovered.
*   **Dependency Injection**: FastAPI's dependency injection system is used to manage dependencies between different parts of the application, such as providing database sessions and service instances to the route handlers.
