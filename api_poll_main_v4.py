"""
Portainer Container Stop Notifier.

Monitors Docker containers across endpoints and sends Discord notifications
when containers stop, restart, or change status.
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# Config
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
PORTAINER_API_URL = os.getenv("PORTAINER_API_URL")
PORTAINER_API_KEY = os.getenv("PORTAINER_API_KEY")
MEMORY_FILE = Path("data/container_memory.json")

MEMORY_FILE.parent.mkdir(exist_ok=True)


def api_request(url, headers, max_retries=3):
    """Make API request with retries for transient errors"""
    retries = 0
    while retries < max_retries:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 502:
                print(f"[WARN] 502 Bad Gateway - skipping {url}")
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            retries += 1
            if retries >= max_retries:
                print(f"[WARN] Request failed after {max_retries} attempts: {str(e)[:200]}")
                return None
            time.sleep(10)
    return None


def send_discord(message):
    """Send Discord message with error handling"""
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        print("[INFO] Discord notification sent")
    except requests.RequestException as e:
        print(f"[ERROR] Failed to send Discord message: {e}")


def load_memory():
    """Load previous container states from disk"""
    if not MEMORY_FILE.exists():
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("[WARN] Failed to decode memory file")
        return {}


def save_memory(memory):
    """Save current container states to disk"""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)
    except IOError as e:
        print(f"[ERROR] Failed to save memory: {e}")


def get_all_containers(headers):
    """Fetch all containers from all endpoints"""
    endpoints = api_request(f"{PORTAINER_API_URL}/endpoints", headers) or []
    containers_by_endpoint = {}
    for ep in endpoints:
        if not isinstance(ep, dict):
            continue
        ep_name = ep.get("Name", f"endpoint-{ep.get('Id', 'unknown')}")
        containers_data = api_request(
            f"{PORTAINER_API_URL}/endpoints/{ep.get('Id')}/docker/containers/json?all=1",
            headers
        ) or []
        containers_by_endpoint[ep_name] = [
            {
                "id": c.get("Id", "")[:12],
                "name": c.get("Names", [""])[0].lstrip("/"),
                "status": c.get("State", "unknown"),
            }
            for c in containers_data
        ]
    return containers_by_endpoint


def build_memory(containers_by_endpoint):
    """Build flat memory dict from containers grouped by endpoint"""
    memory = {}
    for ep_name, containers in containers_by_endpoint.items():
        for c in containers:
            memory[c["id"]] = {
                "name": c["name"],
                "status": c["status"],
                "endpoint": ep_name,
            }
    return memory


def detect_changes(old_memory, new_containers):
    """Detect changes in container states"""
    changes = {}

    # Flatten new containers
    new_flat = {
        c["id"]: {**c, "endpoint": ep_name}
        for ep_name, containers in new_containers.items()
        for c in containers
    }

    # Map old names to IDs
    old_name_to_ids = {}
    for cid, data in old_memory.items():
        old_name_to_ids.setdefault(data["name"], set()).add(cid)

    # First run: report non-running containers
    if not old_memory:
        for ep_name, containers in new_containers.items():
            non_running = [
                f"⚠️ Not Running: {c['name']} ({c['id']}) - {c['status']}"
                for c in containers
                if c.get("status", "").lower() != "running"
            ]
            if non_running:
                changes[ep_name] = non_running
        return changes

    removed_ids_to_skip = set()

    # Detect new or restarted containers
    for cid, container in new_flat.items():
        if cid not in old_memory:
            name = container["name"]
            old_ids_for_name = old_name_to_ids.get(name, set())
            if old_ids_for_name:
                changes.setdefault(container["endpoint"], []).append(
                    f"✅ Restarted: {name} ({cid}) - {container['status']}"
                )
                removed_ids_to_skip.update(old_ids_for_name)
            else:
                changes.setdefault(container["endpoint"], []).append(
                    f"🆕 New: {name} ({cid}) - {container['status']}"
                )
        else:
            old_status = old_memory[cid]["status"]
            new_status = container["status"]
            if old_status != new_status:
                changes.setdefault(container["endpoint"], []).append(
                    f"🔄 Changed: {container['name']} ({cid}) - {old_status} → {new_status}"
                )

    # Check removed containers
    for cid, old_data in old_memory.items():
        if cid not in new_flat and cid not in removed_ids_to_skip:
            changes.setdefault(old_data.get("endpoint", "unknown"), []).append(
                f"❌ Removed: {old_data['name']} ({cid})"
            )

    return changes


def main():
    """Main loop"""
    if not all([DISCORD_WEBHOOK, PORTAINER_API_URL, PORTAINER_API_KEY]):
        raise ValueError("Missing required environment variables in .env")

    headers = {"X-API-Key": PORTAINER_API_KEY}
    old_memory = load_memory()

    while True:
        containers = get_all_containers(headers)
        if containers:
            changes = detect_changes(old_memory, containers)
            for ep_name, change_list in changes.items():
                send_discord(f"**{ep_name}**\n" + "\n".join(change_list))
            new_memory = build_memory(containers)
            save_memory(new_memory)
            old_memory = new_memory
        else:
            print("[WARN] No containers data fetched this cycle.")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
