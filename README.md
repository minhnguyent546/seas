# SEAS

> SEAS - Smart Enrollment Advisory System

*Currently cooking...*

## Getting started

1. **Clone this repository:**
  ```bash
  git clone https://github.com/minhnguyent546/seas.git seas
  cd seas
  ```

2. **Update the .env file:**
  ```bash
  cp .env.example .env
  ```
  Edit the `.env` file to your preferences.

3. **Start the application:**
  You can start the application via Docker compose:
  ```bash
  docker compose -f docker-compose.yaml up --build
  ```

  To run in development mode, you can use:
  ```bash
  docker compose up --build --watch
  ```
  Point your browser to http://localhost:8444/docs to see the API documentation.
