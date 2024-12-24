#!/bin/bash

# filepath: /home/derek/DEV/HumanFlowTaskManager/tools/down_and_build.sh

# Bring down the docker containers
cd "$(dirname "$0")/.." || exit
docker-compose down

# Build the docker images
# find user's ip address

# Run the Python script to clear rate limit
docker-compose up --remove-orphans --build 

