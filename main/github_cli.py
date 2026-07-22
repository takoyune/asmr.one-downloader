import json
import urllib.request
import logging
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from main.constants import GITHUB_REPO, console

class GitHubCLIHelper:
    """Utility helper for inspecting GitHub repository releases, issues, and status."""

    def __init__(self, repo: str = GITHUB_REPO):
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"

    def _api_get(self, endpoint: str) -> Optional[Any]:
        url = f"{self.api_base}/{endpoint}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            logging.error(f"GitHub API request failed for {endpoint}: {e}")
        return None

    def display_latest_release_notes(self) -> None:
        """Fetch and print latest release notes."""
        console.print("[cyan]Fetching latest release notes from GitHub...[/cyan]")
        data = self._api_get("releases/latest")
        if not data:
            console.print("[yellow]Could not fetch release notes from GitHub.[/yellow]")
            return

        tag = data.get("tag_name", "Unknown")
        name = data.get("name", tag)
        body = data.get("body", "No description provided.")
        published_at = data.get("published_at", "")[:10]

        content = f"[bold magenta]Release {name}[/bold magenta] ({published_at})\n\n{body}"
        console.print(Panel(content, title=f"🐙 GitHub Release — {tag}", border_style="cyan"))

    def display_open_issues(self) -> None:
        """Fetch and print top open issues."""
        console.print("[cyan]Fetching open issues from GitHub...[/cyan]")
        issues = self._api_get("issues?state=open&per_page=5")
        if not issues:
            console.print("[green]No open issues found or unable to fetch issues.[/green]")
            return

        table = Table(title="🐙 Recent GitHub Issues", box=None)
        table.add_column("#", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Author", style="green")
        table.add_column("Comments", justify="right", style="yellow")

        for issue in issues:
            if "pull_request" in issue:
                continue
            table.add_row(
                f"#{issue.get('number')}",
                issue.get('title', '')[:45],
                issue.get('user', {}).get('login', 'Unknown'),
                str(issue.get('comments', 0))
            )

        console.print(table)
