import sys

import click

from jira_cli.client import JiraClientError, fetch_issue
from jira_cli.config import load_config, save_config, validate_config
from jira_cli.formatter import format_json, format_text


@click.group()
def cli():
    """Jira CLI — fetch Jira tickets by ID."""
    pass


@cli.command()
@click.option("--base-url", default=None, help="Jira base URL (e.g. https://mycompany.atlassian.net)")
@click.option("--email", default=None, help="Jira account email")
@click.option("--token", default=None, help="Jira API token")
def setup(base_url, email, token):
    """Configure Jira credentials. Prompts interactively if options are omitted."""
    if not base_url:
        base_url = click.prompt("Jira Base URL", type=str)
    if not email:
        email = click.prompt("Email", type=str)
    if not token:
        token = click.prompt("API Token", type=str, hide_input=True)

    save_config(base_url, email, token)
    click.echo("Config saved to ~/.jira-cli/config.json", err=True)


@cli.command()
@click.argument("ticket_id")
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="json", help="Output format (default: json)")
def get(ticket_id, fmt):
    """Fetch a Jira ticket by ID (e.g. RPR-81)."""
    config = load_config()
    error = validate_config(config)
    if error:
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)

    try:
        issue = fetch_issue(config["base_url"], config["email"], config["api_token"], ticket_id)
    except JiraClientError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(e.exit_code)

    if fmt == "json":
        click.echo(format_json(issue))
    else:
        click.echo(format_text(issue))


if __name__ == "__main__":
    cli()
