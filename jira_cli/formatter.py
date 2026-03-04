import json


def format_json(issue: dict) -> str:
    """Return issue as formatted JSON string."""
    return json.dumps(issue, indent=2, ensure_ascii=False)


def format_text(issue: dict) -> str:
    """Return issue as human-readable text."""
    lines = []
    lines.append(f"[{issue['key']}] {issue['summary']}")
    lines.append(f"  Type:       {issue.get('issue_type') or 'N/A'}")
    lines.append(f"  Status:     {issue.get('status') or 'N/A'}")
    lines.append(f"  Priority:   {issue.get('priority') or 'N/A'}")
    lines.append(f"  Assignee:   {issue.get('assignee') or 'Unassigned'}")
    lines.append(f"  Reporter:   {issue.get('reporter') or 'N/A'}")
    lines.append(f"  Resolution: {issue.get('resolution') or 'Unresolved'}")
    lines.append(f"  Created:    {issue.get('created') or 'N/A'}")
    lines.append(f"  Updated:    {issue.get('updated') or 'N/A'}")

    if issue.get("sprint"):
        lines.append(f"  Sprint:     {issue['sprint']}")

    if issue.get("labels"):
        lines.append(f"  Labels:     {', '.join(issue['labels'])}")

    if issue.get("components"):
        lines.append(f"  Components: {', '.join(issue['components'])}")

    if issue.get("description"):
        lines.append("")
        lines.append("Description:")
        lines.append(issue["description"])

    if issue.get("subtasks"):
        lines.append("")
        lines.append("Subtasks:")
        for st in issue["subtasks"]:
            lines.append(f"  [{st['key']}] {st['summary']} ({st['status']})")

    if issue.get("links"):
        lines.append("")
        lines.append("Links:")
        for link in issue["links"]:
            lines.append(f"  {link['type']} ({link['direction']}) -> {link['key']}")

    if issue.get("attachments"):
        lines.append("")
        lines.append("Attachments:")
        for att in issue["attachments"]:
            lines.append(f"  {att['filename']} (by {att['author']}, {att['created']})")

    if issue.get("comments"):
        lines.append("")
        lines.append(f"Comments ({len(issue['comments'])}):")
        for c in issue["comments"]:
            lines.append(f"  --- {c['author']} ({c['created']}) ---")
            lines.append(f"  {c['body']}")
            lines.append("")

    return "\n".join(lines)
