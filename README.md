# Organization Management Service

A backend service for managing organizations in a multi-tenant style architecture using **FastAPI** and **MongoDB**.

## Features

- **Master Database**: Stores organization metadata and admin credentials.
- **Dynamic Collections**: Automatically creates a new MongoDB collection for each organization (`org_<name>`).
- **Authentication**: Admin login with JWT.
- **Organization Management**: Create, Read, Update (with data sync/rename), Delete.

## Project Structure

```bash
.
├── app
│   ├── api         # API Endpoints (Auth, Organizations)
│   ├── core        # Config, Security (JWT, Hashing)
│   ├── db          # Database Connection (Motor)
│   ├── models      # Database Models
│   ├── schemas     # Pydantic Schemas
│   └── main.py     # Application Entry Point
├── design_notes.md # Architecture Diagram & Design Choices
├── requirements.txt
└── .env
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB installed and running locally (`mongodb://localhost:27017`)

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment Variables:
   A `.env` file has been created with default values:
   ```ini
   SECRET_KEY=supersecretkey
   MONGO_URL=mongodb://localhost:27017
   MONGO_DB_NAME=master_db
   ```

## Running the Application

Start the server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Documentation

Interactive API documentation (Swagger UI) is available at:
- **http://localhost:8000/docs**

## Design Notes

Please refer to [design_notes.md](design_notes.md) for the high-level architecture diagram and explanation of design choices.
