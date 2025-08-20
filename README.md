Got it! Here's the updated README with all your requested changes:

---

# Portainer Container Stop Notifier

A simple Python script running in Docker that listens for Docker container **status changes** like stop, exited, or restarted across your Docker host and sends webhook notifications (e.g., Discord, Slack).

---

## Features

* Listens to all container status changes such as stop, exited, or restarted
* Sends customizable webhook notifications
* Supports multiple agents by running on the Docker host or per node
* Configurable via environment variables
* Lightweight Alpine-based Docker image

---

## Setup

1. Clone this repository

```bash
git clone https://github.com/yourusername/portainer-notif.git
cd portainer-notif
```

2. Copy the example environment file, update your details, and rename it to `.env`:

```bash
cp example.env .env
# Then edit .env with your webhook URL and other settings
```

3. Update your Docker Compose file to use the latest tag of the version you want, then start the container:

```bash
docker compose up -d
```

*No rebuild necessary unless you change the code or Dockerfile.*

4. Since this is designed to work with Portainer, it is best to check logs inside Portainer’s UI to verify the container is running and see real-time logs.

---

## How it works

* The container runs a Python script that connects to the Docker daemon through the Docker socket or Portainer API.
* It listens for all container status changes such as stop, exited, or restarted.
* When a container changes status, it sends a notification to the configured webhook URL with relevant details including container name, ID, and optionally node name.

---

## Environment Variables

- `WEBHOOK_URL` — **Required.** The full URL to your webhook endpoint (Discord, Slack, etc.).
- `PORTAINER_URL` — URL to your Portainer API (default example: `https://portainer:9000/api`).
- `PORTAINER_USERNAME` — Portainer login username (if using username/password auth).
- `PORTAINER_PASSWORD` — Portainer login password.
- `PORTAINER_API_KEY` — API key for Portainer authentication (alternative to username/password).

- `HOSTNAME` — *Optional.* Friendly node name to identify your server in notifications (e.g., `d4rkcyber`).
- `DISCORD_WEBHOOK` — Alternative webhook URL for Discord notifications, compare with compose file (if different from `WEBHOOK_URL`).
- `PORTAINER_API_URL` — Alternative Portainer API URL environment variable (optional override).
- `LOG_LEVEL` — Log verbosity level (default: `info`, options include `debug`, `warn`, `error`).


*(Additional environment variables may be added in future versions.)*

---

## Version History

| Version | Description                                                                                     |
| ------- | ----------------------------------------------------------------------------------------------- |
| 1.0.0   | Initial release: Listens for stopped containers and sends container ID to Discord webhook.      |
| 1.1.0   | On start, checks all containers with state != "running" and sends node name and container info. |
| 1.2.0   | Added optional `NODE_NAME` env var to customize node name in webhook payload delivery.          |
| 3.0.1   | Updated code to handle ENDPOINT failures more gracefully with notifications.                    |

---

## Build Status

![Build Status](https://img.shields.io/github/actions/workflow/status/yourusername/portainer-notif/ci.yml?branch=main)

---

ENV_FILE:
WEBHOOK_URL=
PORTAINER_URL=https://portainer:9000/api
PORTAINER_USERNAME=
PORTAINER_PASSWORD=
PORTAINER_API_KEY="portainer_api_key"
HOSTNAME=d4rkcyber
DISCORD_WEBHOOK=
PORTAINER_API_URL=
LOG_LEVEL=info
