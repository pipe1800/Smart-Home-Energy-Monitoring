### **Project Overview**

The Smart Home Energy Monitoring platform is a comprehensive tool for tracking and analyzing energy consumption patterns. It features **Wat**, a conversational AI energy advisor, that provides users with insights and forecasting to help them better understand and optimize their energy usage.

-----

### **Architecture**

The platform is built on a microservices architecture, with Docker containers for each service. The system is composed of the following services:

  * **Frontend**: A React application with Tailwind CSS that serves as the user interface.
  * **Auth Service**: A FastAPI-based authentication service that handles user registration and login.
  * **Telemetry Service**: A FastAPI service responsible for collecting and managing energy consumption data from devices.
  * **AI Service**: A FastAPI service that integrates with OpenRouter to provide AI-powered energy insights and forecasting.
  * **Database**: A PostgreSQL database for storing user data, device information, and telemetry data.

-----

### **Tech Stack**

  * **Frontend**: React, Tailwind CSS
  * **Backend**: FastAPI, Python
  * **Database**: PostgreSQL
  * **AI**: OpenRouter, Claude
  * **Authentication**: JWT (JSON Web Tokens)
  * **Containerization**: Docker, Docker Compose

-----

### **API Documentation**

The API documentation for the backend services is available on SwaggerHub. You can access it through the following link:

[https://app.swaggerhub.com/apis-docs/shem-a49/SHEM/1](https://app.swaggerhub.com/apis-docs/shem-a49/SHEM/1)

-----

### **Getting Started**

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/pipe1800/Smart-Home-Energy-Monitoring-with-Conversational-AI.git
    cd Smart-Home-Energy-Monitoring-with-Conversational-AI
    ```

2.  **Configure Environment Variables**:
    The project uses environment variables for configuration. You'll need to modify the `.env.example` file to be named `.env` as I have provided the openrouter API key there to make the testing easier.

3.  **Run the setup script**:

    ```bash
    ./setup.sh
    ```

    This script builds the Docker containers, starts all services, and opens the application in your browser.

-----

### **Stopping the Application**

To stop all running services, use the following command:

```bash
./stop.sh
```

-----

### **Testing**

The project includes unit and integration tests for the backend services.

**Test Coverage**:

  * **Auth Service**: Password hashing, JWT token management, user registration, login authentication, and rate limiting.
  * **Telemetry Service**: Schedule validation, device management, telemetry data recording, and device ownership verification.

**Running Tests**:

  * To run all backend tests:
    ```bash
    cd backend && ./run_tests.sh
    ```
  * To run specific test suites:
    ```bash
    # Unit tests
    python3 -m pytest auth-service/tests/test_auth.py telemetry-service/tests/test_telemetry.py -v

    # Integration tests
    python3 -m pytest auth-service/tests/test_auth_integration.py telemetry-service/tests/test_telemetry_integration.py -v
    ```
