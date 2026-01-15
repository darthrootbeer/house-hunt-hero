## House Hunt Hero
Early-market real estate discovery that finds listings before Zillow/Redfin and alerts you fast.

### What it does
- Pulls listings from multiple public sources
- Normalizes them into one clean format
- Checks if they already exist on Zillow/Redfin
- Scores them against your house profile
- Sends alerts by email and Pushover

### Setup (plain language)
1. Install Python 3.11 or newer.
2. Copy the example configs into your own files.
3. Add your email and Pushover keys as environment variables.
4. Install dependencies with `python -m pip install -r requirements.txt`.
5. Run the scheduler locally or via GitHub Actions.

### Config files
- `configs/house_profile.json` your buying criteria (current)
- `house_profile.example.yaml` legacy example format
- `configs/sources.example.yaml` which sources to check
- `configs/alerts.example.yaml` how to send alerts
- `configs/runtime.example.yaml` schedule + storage

### Running locally
You can run a local test loop to confirm alerts work before automation.
`python scripts/run.py`

### Automation
GitHub Actions (GitHub’s built-in scheduler) can run every 5–15 minutes without a server.

### State and dedupe
State is stored in `state/state.db` (SQLite) to avoid duplicate alerts.
