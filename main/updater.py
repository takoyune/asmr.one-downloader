import os
import sys
import json
import zipfile
import tempfile
import urllib.request
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from packaging import version
from rich.console import Console

from main.constants import APP_VERSION, GITHUB_REPO, console

class GitHubUpdater:
    """Handles GitHub release checks and automatic updates."""

    def __init__(self, repo: str = GITHUB_REPO):
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    def fetch_latest_release(self) -> Optional[Dict[str, Any]]:
        """Fetch latest release metadata from GitHub API."""
        try:
            req = urllib.request.Request(
                self.api_url,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            logging.error(f"Failed to check GitHub releases: {e}")
        return None

    def check_for_updates(self, current_ver: str = APP_VERSION) -> Tuple[bool, str, str, str]:
        """
        Check if a newer version is available on GitHub.
        Returns: (has_update, latest_version_tag, release_notes, zipball_url)
        """
        data = self.fetch_latest_release()
        if not data:
            return False, current_ver, "", ""

        latest_tag = data.get("tag_name", "").strip()
        release_notes = data.get("body", "No release notes provided.")
        zip_url = data.get("zipball_url", f"https://github.com/{self.repo}/archive/refs/tags/{latest_tag}.zip")

        if not latest_tag:
            return False, current_ver, "", ""

        clean_current = current_ver.lstrip('v')
        clean_latest = latest_tag.lstrip('v')

        try:
            has_update = version.parse(clean_latest) > version.parse(clean_current)
        except Exception:
            has_update = (clean_latest != clean_current)

        return has_update, latest_tag, release_notes, zip_url

    def perform_self_update(self, zip_url: str, target_dir: Path = Path(".")) -> bool:
        """Download and extract update archive safely, preserving user data."""
        try:
            console.print("[cyan]Downloading update package from GitHub...[/cyan]")
            req = urllib.request.Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    tmp_file.write(resp.read())
                tmp_zip_path = Path(tmp_file.name)

            console.print("[cyan]Extracting update files...[/cyan]")
            protected_files = {"config.json", "history.db", "singularity.log"}
            
            with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                top_folder = zip_ref.namelist()[0].split('/')[0]
                
                for member in zip_ref.infolist():
                    filename = member.filename
                    if filename.startswith(top_folder + '/'):
                        relative_path = filename[len(top_folder) + 1:]
                        if not relative_path or relative_path in protected_files:
                            continue

                        dest_path = target_dir / relative_path
                        if member.is_dir():
                            dest_path.mkdir(parents=True, exist_ok=True)
                        else:
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            with zip_ref.open(member) as source, open(dest_path, "wb") as target:
                                target.write(source.read())

            try:
                os.remove(tmp_zip_path)
            except OSError:
                pass

            console.print("[bold green]✅ Self-update successfully applied! Please restart the application.[/bold green]")
            return True

        except Exception as e:
            console.print(f"[bold red]❌ Update failed: {e}[/bold red]")
            logging.error(f"Self-update error: {e}", exc_info=True)
            return False
