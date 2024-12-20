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
3. Add environment variables in a `.env` file in the root directory with the following variables:
    - `GOOGLE_CLIENT_ID` - Google Client ID for OAuth
    - `GOOGLE_CLIENT_SECRET` - Google Client Secret for OAuth
    - `FLASK_SECRET_KEY` - Flask secret key for session management and CSRF protection (can be any random string) `head -c 32 /dev/urandom | base64` on Unix systems
4. Run `python main.py`
