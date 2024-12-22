#!/usr/bin/env bash

# Bring down the docker containers

cd "$(dirname "$0")/.." || exit

docker-compose down

# Build the docker images and run pytest

docker-compose up --remove-orphans --build -d && docker-compose exec web pytest

# echo any error messages
echo "Error messages:" && docker-compose logs | grep -i error && echo "End of error messages"