#!/bin/bash

# add a cronjob like:
# 0 5 * * Sun /home/access/Infrastructure-Re/scripts/renew_certbot.bash

docker compose down frontend
docker compose down backend
docker compose up certbot
docker compose up backend -d
docker compose up frontend -d

