#!/bin/bash
# https://www.homeautomationguy.io/home-assistant-tips/keeping-your-home-assistant-container-up-to-date/

apt update
apt full-upgrade -y
apt autoremove -y

cd /opt/
docker compose pull
docker compose up -d
docker image prune -af
docker volume prune -f
