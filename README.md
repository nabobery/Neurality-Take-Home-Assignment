# RAG Chatbot Project

This project implements a Retrieval-Augmented Generation (RAG) chatbot. It consists of a backend built with Django and a frontend built with React.

## Project Structure

The project is organized as follows:

- `backend/`: Contains the Django backend application.
  - `core/`: Core Django project settings and configurations.
  - `chat/`: Django app for handling chat functionalities.
    - `services/`: Contains the core logic for document processing, embedding, and question answering.
- `frontend/`: Contains the React frontend application.
  - `components/`: React components for the user interface.
- `docker-compose.yml`: Defines the services for running the application using Docker.

## Prerequisites

Before running the application, ensure you have the following installed:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Running the Application

1. **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd rag-chatbot
    ```

2. **Build and start the services using Docker Compose:**

    ```bash
    docker-compose up --build
    ```

    This command will:

    - Build the Docker images for the backend and frontend.
    - Start the containers for the backend and frontend.

3. **Access the application:**

    - The frontend will be accessible at `http://localhost:3000`.
    - The backend will be accessible at `http://localhost:8000`.

## Development

### Backend

- Navigate to the `backend` directory:

  ```bash
  cd backend
  ```

- To run the backend locally without Docker:
  1. Create a virtual environment:

     ```bash
     python -m venv venv
     source venv/bin/activate # On Windows use `venv\Scripts\activate`
     ```

  2. Install dependencies:

     ```bash
     pip install -r requirements.txt
     ```

  3. Apply migrations:

     ```bash
     python manage.py migrate
     ```

  4. Run the development server:

     ```bash
     python manage.py runserver
     ```

- Make changes to the code in the `chat` app, specifically in the `services` directory for the core logic.

### Frontend

- Navigate to the `frontend` directory:

  ```bash
  cd frontend
  ```

- To run the frontend locally without Docker:
  1. Install dependencies:

     ```bash
     npm install
     ```

  2. Start the development server:

     ```bash
     npm start
     ```

- Make changes to the code in the `src` directory, specifically in the `components` directory for the UI and `services` for API calls.

## Key Components

- **Document Upload:** Allows users to upload documents that will be processed by the backend.
- **Chat Interface:** Provides a user interface for interacting with the chatbot.
- **Document Processor:** Handles the processing of uploaded documents.
- **Embedding Service:** Generates embeddings for the documents.
- **QA Service:** Uses the embeddings to answer user questions.

## Notes

- The `docker-compose.yml` file defines the necessary configurations for running the application using Docker.
- The `requirements.txt` file in the `backend` directory lists the Python dependencies for the backend.
- The `package.json` file in the `frontend` directory lists the JavaScript dependencies for the frontend.

## Further Development

- Implement more advanced document processing techniques.
- Improve the accuracy of the question-answering system.
- Add more features to the user interface.
