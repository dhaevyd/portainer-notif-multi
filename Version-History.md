## Version History for Portainer Multi-Node Notification Assistant

### :1.1.0

* Initial implementation of Portainer container status polling script.
* Basic `.env` integration for `WEBHOOK_URL`, `PORTAINER_URL`, `PORTAINER_USERNAME`, and `PORTAINER_PASSWORD`.
* Sends container status changes to Discord webhook.
* Polling interval fixed at 30 seconds.

### :polling

* Added **friendly node name** support (`HOSTNAME`) to help identify which server sends notifications.
* Cosmetic: Improved log messages with `[INFO]` prefixes for clarity.
* Added better container status formatting in Discord messages.

### :polling-latest

* Functional: Introduced `PORTAINER_API_KEY` authentication option alongside username/password.
* Cosmetic: Log output now includes Portainer endpoint name in status updates.
* Added **optional** `DISCORD_WEBHOOK`, `PORTAINER_API_URL`, and `LOG_LEVEL` environment variables to `.env` template.
* Improved `.env` documentation and added `example.env` generation.

### :1.3.0

* Functional: Removed username/password login flow; switched exclusively to API Key for authentication.
* Functional: Replaced event-based container status updates with polling every configurable interval (`POLL_INTERVAL`).
* Functional: Added persistent container state memory stored on disk for detecting changes between polls.
* Functional: Enhanced detection for new, removed, and status-changed containers.
* Cosmetic: Added graceful shutdown on SIGINT and SIGTERM signals.
* Cosmetic: Added clearer info and error log messages with prefixes.
* Structural: Removed multi-threaded event listeners in favour of a simpler single-thread polling loop.
* Added timeout and error handling for API calls.

### :1.4.0

* Functional: Added robust API request wrapper with retry/backoff on rate limits (429) and other failures.
* Functional: Aggregated container data by Portainer endpoint for better notification grouping.
* Functional: Improved detection and notification logic with grouped messages per endpoint.
* Cosmetic: Added more informative logging on fetch successes and failures.
* Cosmetic: Added indentation to saved memory JSON for readability.
* Structural: Refactored to a modular style with helper functions (`api_request`, `send_discord`, etc.).
* Functional: Initial notification includes all non-running containers per endpoint on startup.
* Added environment variable validation on startup.

### :2.0.1

* Functional: Added detection of container restarts by comparing container names and IDs.
* Functional: Updated change detection logic to track restarts, new containers, status changes, and removals distinctly.
* Functional: On initial run, sends notifications only for non-running containers; subsequent runs send only detected changes.
* Cosmetic: Added more detailed informational logs during memory loading and saving.
* Cosmetic: Improved error handling and messages during memory file read/write.
* Structural: Maintained modular functions with clear separation of concerns.
* Functional: Preserved endpoint grouping for changes and notifications.
* Improved robustness when handling container state memory and change detection.

### :2.1.1

* Functional: Added handling for HTTP 502 Bad Gateway responses by skipping the failing request gracefully.
* Functional: Simplified `api_request` retry logic by removing exponential backoff and returning `None` on failure instead of raising exceptions.
* Functional: Suppressed exceptions in Discord notification sending for quieter error handling.
* Functional: Made memory load/save more fault-tolerant by ignoring read/write errors silently.
* Functional: Simplified container fetching logic with list/dict comprehensions, default fallbacks, and safer `.get()` calls.
* Functional: Improved restart detection by mapping container names to multiple old IDs.
* Functional: Initial run now sends notifications only for non-running containers; all other changes are detected on subsequent runs.
* Cosmetic: Removed most logging except warnings and essential info to reduce noise.
* Structural: Maintained memory-based change detection and endpoint grouping for notifications.
* Improved overall robustness and error tolerance for real-world network/API failures.

### :3.0.1

* Functional: Added endpoint health monitoring to track the availability status of each Portainer endpoint/agent node.
* Functional: Implemented real-time notifications for endpoint connectivity changes (🔴 DOWN, 🟢 RECOVERED, ❌ REMOVED).
* Functional: Enhanced container fetching to return both container data and endpoint health status in a single operation.
* Functional: Added persistent endpoint health tracking with the endpoint_health.json file to maintain state between restarts.
* Functional: Prevented false "container removed" notifications when endpoints become unreachable by filtering out containers from unhealthy endpoints.
* Functional: Modified detect_changes() to accept endpoint health data and exclude containers on down nodes from removal detection.
* Functional: Added the detect_endpoint_changes() function to compare previous and current endpoint health states.
* Functional: Enhanced error handling in get_all_containers() to gracefully mark endpoints as unhealthy when API calls fail.
* Structural: Separated endpoint health persistence from container state persistence for cleaner data management.
* Cosmetic: Added distinct emoji indicators for endpoint status changes (🔴/🟢) versus container changes (🆕/✅/🔄/❌).
* Improved monitoring reliability by distinguishing between actual container removal and temporary endpoint unavailability.
---
