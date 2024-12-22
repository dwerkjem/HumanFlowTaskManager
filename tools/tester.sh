#!/usr/bin/env bash

# Bring down the docker containers

cd "$(dirname "$0")/.." || exit

docker-compose down

# Build the docker images and run pytest

docker-compose up --remove-orphans --build -d && docker-compose exec app pytest

