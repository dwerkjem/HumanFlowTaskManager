# Human Flow Task Manager

## Description

This is a project to track your day-to-day tasks and manage them in a simple way.

## Features

- Task management
- Time tracking
- Progress visualization
- Task prioritization
- Add Accountability Partners
- Add Task Dependencies
- Add Task Notes

## Installation

1. Clone the repository
2. Rename the file `credentials.json.example` to `credentials.json` and fill in the necessary information
    - `credentials.json` has a key of group which is an integer value. The higher the number, the less privileged the user is. 0 is Admin, 1 is viewer.
3. Rename the file `.env.example` to `.env` and fill in the necessary information
    - `APP_PORT_HOST` is the port number the app will run on
    - `APP_PORT_CONTAINER` is the port number the app will run on in the container
    - `GF_SECURITY_ADMIN_PASSWORD` is the password for the Grafana admin user
    - `GRAFANA_PORT_HOST` is the port number Grafana will run on
    - `GRAFANA_PORT_CONTAINER` is the port number Grafana will run on in the container
    - `LOKI_PORT_HOST` is the port number Loki will run on
    - `LOKI_PORT_CONTAINER` is the port number Loki will run on in the container
    - `SECRET_KEY` is the secret key for the Flask app THIS IS VERY IMPORTANT TO CHANGE
    - `MONGO_INITDB_ROOT_USERNAME` is the root username for the MongoDB database
    - `MONGO_INITDB_ROOT_PASSWORD` is the root password for the MongoDB database
4. Run `docker-compose up --build -d` to build the images and run the containers
5. Access the app at `http://localhost:8000`