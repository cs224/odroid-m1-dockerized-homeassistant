
SHELL := /bin/bash

service_restart:
	systemctl daemon-reload && systemctl restart homeassistant

run_compose_up:
	docker compose --env-file ./dc.env -f ./docker-compose.yml up

run_compose_down:
	docker compose --env-file ./dc.env -f ./docker-compose.yml down

run_compose_down_and_delete:
	docker compose --env-file ./dc.env -f ./docker-compose.yml down -v --remove-orphans # --rmi all

check-for-container-updates:
	docker run -it --rm --name watchtower -v /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower --run-once

run_compose_logs:
	docker compose logs --follow
