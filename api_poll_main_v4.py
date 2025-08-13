"""
Portainer Container Stop Notifier.

Monitors Docker containers across endpoints and sends Discord notifications
when containers stop, restart, or change status.
"""

import os
import time
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Config
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
PORTAINER_API_URL = os.getenv("PORTAINER_API_URL")
PORTAINER_API_KEY = os.getenv("PORTAINER_API_KEY")
MEMORY_FILE = Path("data/container_memory.json")

MEMORY_FILE.parent.mkdir(exist_ok=True)

def api_request(url, headers, max_retries=3):
    """Make API request with rate limiting and limited retries"""
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
    except Exception:
        pass

def load_memory():
    """Load previous container states from disk"""
    if not MEMORY_FILE.exists():
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(memory):
    """Save current container states to disk"""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)
    except Exception:
        pass

def get_all_containers(headers):
    """Fetch all containers from all endpoints"""
    try:
        endpoints = api_request(f"{PORTAINER_API_URL}/endpoints", headers) or []
        return {
            ep.get('Name', f"endpoint-{ep.get('Id','unknown')}"): [
                {
                    "id": c.get('Id','')[:12],
                    "name": c.get('Names',[''])[0].lstrip('/'),
                    "status": c.get('State','unknown')
                }
                for c in api_request(
                    f"{PORTAINER_API_URL}/endpoints/{ep.get('Id')}/docker/containers/json?all=1",
                    headers
                ) or []
            ]
            for ep in endpoints if isinstance(ep, dict)
        }
    except Exception:
        return {}

def build_memory(containers_by_endpoint):
    """Build flat memory dict from containers grouped by endpoint"""
    memory = {}
    for ep_name, containers in containers_by_endpoint.items():
        for c in containers:
            memory[c['id']] = {
                "name": c['name'],
                "status": c['status'],
                "endpoint": ep_name
            }
    return memory

# --- Refactored detect_changes ---
def detect_changes(old_memory, new_containers):
    """Detect changes in container states"""
    def build_new_flat(containers):
        return {
            c['id']: {**c, 'endpoint': ep_name}
            for ep_name, cs in containers.items()
            for c in cs
        }

    def build_old_name_to_ids(memory):
        mapping = {}
        for cid, data in memory.items():
            mapping.setdefault(data['name'], set()).add(cid)
        return mapping

    def report_non_running(containers):
        changes = {}
        for ep_name, cs in containers.items():
            non_running = [
                f"⚠️ Not Running: {c['name']} ({c['id']}) - {c['status']}"
                for c in cs
                if c.get('status','').lower() != 'running'
            ]
            if non_running:
                changes[ep_name] = non_running
        return changes

    if not old_memory:
        return report_non_running(new_containers)

    changes = {}
    new_flat = build_new_flat(new_containers)
    old_name_to_ids = build_old_name_to_ids(old_memory)
    removed_ids_to_skip = set()

    # Detect new or restarted containers
    for cid, container in new_flat.items():
        old_ids = old_name_to_ids.get(container['name'], set())
        if cid not in old_memory:
            if old_ids:
                changes.setdefault(container['endpoint'], []).append(
                    f"✅ Restarted: {container['name']} ({cid}) - {container['status']}"
                )
                removed_ids_to_skip.update(old_ids)
            else:
                changes.setdefault(container['endpoint'], []).append(
                    f"🆕 New: {container['name']} ({cid}) - {container['status']}"
                )
        else:
            old_status = old_memory[cid]['status']
            if old_status != container['status']:
                changes.setdefault(container['endpoint'], []).append(
                    f"🔄 Changed: {container['name']} ({cid}) - {old_status} → {container['status']}"
                )

    # Check removed containers
    for cid, old_data in old_memory.items():
        if cid not in new_flat and cid not in removed_ids_to_skip:
            changes.setdefault(old_data.get('endpoint','unknown'), []).append(
                f"❌ Removed: {old_data['name']} ({cid})"
            )

    return changes
# --- End refactor ---

def main():
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

