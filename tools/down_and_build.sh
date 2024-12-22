#!/bin/bash

# filepath: /home/derek/DEV/HumanFlowTaskManager/tools/down_and_build.sh

# Bring down the docker containers
cd "$(dirname "$0")/.." || exit
docker-compose down

# Build the docker images
# find user's ip address
ip=$(ip a | grep 'inet ' | grep -v ' host lo' | awk '{print $2}' | awk -F'/' '{print $1}' | head -n 1)

# Run the Python script to clear rate limit
docker-compose up --remove-orphans --build -d

# Ensure the container is fully started before executing the command
echo "Waiting for the container to start..."
max_attempts=30
attempts=0
while [ "$(docker inspect -f '{{.State.Running}}' humanflowtaskmanager_app_1)" != "true" ]; do
  if [ $attempts -ge $max_attempts ]; then
    echo "Container failed to start after $attempts attempts."
    exit 1
  fi
  echo "Waiting for container to be running... attempt $((attempts+1))"
  sleep 2
  attempts=$((attempts+1))
done

# Execute the command to clear the rate limit

if docker ps | grep -q "humanflowtaskmanager_app_1"; then
  echo "Container is up, waiting 5s to stabilize..."
  sleep 5
  docker-compose exec app python modules/main.py clear_rate_limit $ip
else
  echo "Container is not up"
fi
