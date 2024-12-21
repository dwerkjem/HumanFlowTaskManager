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
2. Run `pip install -r requirements.txt`
3. Rename `env.example.` to `.env` and fill in the necessary information
    - `AUTH0_CLIENT_ID` - Auth0 client ID [Auth0](https://auth0.com/)
    - `AUTH0_CLIENT_SECRET` - Auth0 client secret [Auth0](https://auth0.com/)
    - `AUTH0_DOMAIN` - Auth0 domain [Auth0](https://auth0.com/)
    - `FLASK_SECRET` - Flask secret key (e.g. `head -c 24 /dev/urandom | xxd -p`)
    - `HOST` - Host (e.g. localhost or www.example.com)
    - `PORT` - Port (e.g. 3052)
4. Rename `config/example.config.ini` to `config/config.ini` and fill in the necessary information
    - `authorized_admin_emails` - Comma separated list of emails that are authorized to add data to the database (e.g. {email@mail.com}, {example@default.com})
    - `authorized_viewer_emails` - Comma separated list of emails that are authorized to view data in the database (e.g. {email@mail.com}, {example@default.com})
5. Run `python main.py`