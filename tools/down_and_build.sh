#!/bin/bash

# Bring down the docker containers
cd "$(dirname "$0")/.." || exit
docker-compose down

docker-compose up --remove-orphans --build "$@"
