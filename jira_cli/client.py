import sys

import requests
from requests.auth import HTTPBasicAuth


class JiraClientError(Exception):
    def __init__(self, message: str, exit_code: int = 2):
        super().__init__(message)
        self.exit_code = exit_code


def fetch_issue(base_url: str, email: str, api_token: str, ticket_id: str) -> dict:
    """Fetch a Jira issue by key and return normalized data."""
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{ticket_id}"
    params = {"expand": "renderedFields,names"}

    try:
        resp = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(email, api_token),
            headers={"Accept": "application/json"},
            timeout=30,
        )
    except requests.ConnectionError:
        raise JiraClientError(f"Could not connect to {base_url}")
    except requests.Timeout:
        raise JiraClientError("Request timed out")

    if resp.status_code == 401:
        raise JiraClientError("Authentication failed. Check your email and API token.", exit_code=2)
    if resp.status_code == 403:
        raise JiraClientError("Permission denied. Your account may lack access to this issue.", exit_code=2)
    if resp.status_code == 404:
        raise JiraClientError(f"Ticket {ticket_id} not found.", exit_code=3)
    if resp.status_code != 200:
        raise JiraClientError(f"Jira API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    return _normalize(data)


def _normalize(data: dict) -> dict:
    """Extract key fields from raw Jira API response into a flat structure."""
    fields = data.get("fields", {})

    def _user(u):
        if not u:
            return None
        return u.get("emailAddress") or u.get("displayName")

    def _sprint(fields):
        # Sprint info may be in customfield — try the common locations
        for key, val in fields.items():
            if key.startswith("customfield_") and isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and "name" in item and "state" in item:
                        return item.get("name")
            if key.startswith("customfield_") and isinstance(val, dict):
                if "name" in val and "state" in val:
                    return val.get("name")
        return None

    def _adf_to_text(node):
        """Convert Atlassian Document Format to plain text."""
        if node is None:
            return ""
        if isinstance(node, str):
            return node
        if isinstance(node, dict):
            if node.get("type") == "text":
                return node.get("text", "")
            content = node.get("content", [])
            parts = [_adf_to_text(child) for child in content]
            if node.get("type") == "paragraph":
                return "".join(parts) + "\n"
            if node.get("type") == "hardBreak":
                return "\n"
            return "".join(parts)
        if isinstance(node, list):
            return "".join(_adf_to_text(item) for item in node)
        return ""

    description_raw = fields.get("description")
    if isinstance(description_raw, dict):
        description = _adf_to_text(description_raw).strip()
    elif isinstance(description_raw, str):
        description = description_raw
    else:
        description = ""

    comments_raw = fields.get("comment", {}).get("comments", [])
    comments = []
    for c in comments_raw:
        body = c.get("body", "")
        if isinstance(body, dict):
            body = _adf_to_text(body).strip()
        comments.append({
            "author": _user(c.get("author")),
            "created": c.get("created"),
            "body": body,
        })

    subtasks = [
        {"key": s.get("key"), "summary": s.get("fields", {}).get("summary"), "status": s.get("fields", {}).get("status", {}).get("name")}
        for s in fields.get("subtasks", [])
    ]

    links = []
    for link in fields.get("issuelinks", []):
        link_type = link.get("type", {}).get("name", "")
        if "outwardIssue" in link:
            links.append({"type": link_type, "direction": "outward", "key": link["outwardIssue"].get("key")})
        if "inwardIssue" in link:
            links.append({"type": link_type, "direction": "inward", "key": link["inwardIssue"].get("key")})

    attachments = [
        {"filename": a.get("filename"), "author": _user(a.get("author")), "created": a.get("created")}
        for a in fields.get("attachment", [])
    ]

    return {
        "key": data.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name"),
        "priority": fields.get("priority", {}).get("name"),
        "assignee": _user(fields.get("assignee")),
        "reporter": _user(fields.get("reporter")),
        "description": description,
        "labels": fields.get("labels", []),
        "components": [c.get("name") for c in fields.get("components", [])],
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "resolution": fields.get("resolution", {}).get("name") if fields.get("resolution") else None,
        "issue_type": fields.get("issuetype", {}).get("name"),
        "sprint": _sprint(fields),
        "subtasks": subtasks,
        "links": links,
        "comments": comments,
        "attachments": attachments,
    }
