import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".jira-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load config from file, then override with env vars."""
    config = {"base_url": "", "email": "", "api_token": ""}

    # Load from config file
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config.update(json.load(f))

    # Env vars override config file
    if url := os.environ.get("JIRA_BASE_URL"):
        config["base_url"] = url
    if email := os.environ.get("JIRA_EMAIL"):
        config["email"] = email
    if token := os.environ.get("JIRA_API_TOKEN"):
        config["api_token"] = token

    return config


def save_config(base_url: str, email: str, api_token: str) -> None:
    """Save credentials to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {"base_url": base_url.rstrip("/"), "email": email, "api_token": api_token}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    CONFIG_FILE.chmod(0o600)


def validate_config(config: dict) -> str | None:
    """Return an error message if config is incomplete, else None."""
    missing = [k for k in ("base_url", "email", "api_token") if not config.get(k)]
    if missing:
        return (
            f"Missing config: {', '.join(missing)}. "
            "Run 'jira-cli setup' or set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN env vars."
        )
    return None
