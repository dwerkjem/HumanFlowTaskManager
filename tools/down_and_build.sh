#!/usr/bin/env bash

# This script is used to bring down the docker containers and build the docker images

# Bring down the docker containers
cd "$(dirname "$0")/.." || exit
docker-compose down

# Build the docker images
docker-compose up --remove-orphans --build -d