# Product Context

## Why This Project Exists

This project, Gemini Gateway, was created to address the need for a reliable and efficient way to interact with the Google Gemini API. It serves as a proxy and load balancer, solving common challenges faced by developers using the Gemini API, such as managing multiple API keys, handling rate limits, and ensuring high availability.

## What Problems It Solves

Gemini Gateway solves several key problems:

*   **API Key Management**: It allows for the use of multiple Gemini API keys, rotating through them to distribute the load and avoid hitting rate limits on a single key.
*   **High Availability**: By implementing key rotation and failure retries, it makes applications more resilient to single-key failures.
*   **Protocol Compatibility**: It provides a compatibility layer to access Gemini features through an OpenAI-compatible API format, allowing developers to use existing tools and libraries that support the OpenAI API.
*   **Feature Enhancement**: It extends the base Gemini API with additional features like image generation, web search, and detailed logging, all accessible through a unified interface.
*   **Simplified Configuration**: It offers a visual admin panel for real-time configuration changes without needing to restart the service.
*   **Monitoring and Debugging**: It provides status pages and detailed error logs to monitor key usage and troubleshoot issues effectively.

## How It Should Work

The application should function as a central gateway for all Gemini API requests.

1.  Clients send API requests (either in Gemini or OpenAI format) to the Gemini Gateway.
2.  The gateway authenticates the request using a predefined list of allowed tokens.
3.  It selects a valid Gemini API key from its pool using a load-balancing strategy.
4.  It forwards the request to the Gemini API, handling any necessary proxying.
5.  If a request fails, it automatically retries with the next available key.
6.  It returns the response from the Gemini API to the client, optionally optimizing streaming responses.
7.  All activities, including key status, requests, and errors, are logged and can be monitored through a web interface.
