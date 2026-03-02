"""
Auto-updater for checkm8.

Checks GitHub releases for new versions and notifies the user.
"""

import threading
import urllib.request
import json
from typing import Optional, Tuple, Callable
from config.constants import APP_VERSION


class UpdateChecker:
    """Checks for updates from GitHub releases."""

    # GitHub API endpoint for latest release
    # User should set their own repo URL
    GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"

    def __init__(self, owner: str, repo: str):
        """
        Initialize update checker.

        Args:
            owner: GitHub username
            repo: Repository name
        """
        self._owner = owner
        self._repo = repo
        self._api_url = self.GITHUB_API.format(owner=owner, repo=repo)
        self._checking = False

    def check_for_updates(
        self,
        callback: Callable[[bool, Optional[dict]], None],
        timeout: int = 10
    ):
        """
        Check for updates in background thread.

        Args:
            callback: Called with (update_available, release_info) when done
            timeout: Network timeout in seconds
        """
        if self._checking:
            return

        def _check():
            self._checking = True
            try:
                # Fetch latest release info from GitHub API
                req = urllib.request.Request(
                    self._api_url,
                    headers={'User-Agent': 'checkm8-updater'}
                )

                with urllib.request.urlopen(req, timeout=timeout) as response:
                    data = json.loads(response.read().decode('utf-8'))

                # Parse release info
                latest_version = data.get('tag_name', '').lstrip('v')
                release_url = data.get('html_url', '')
                release_notes = data.get('body', '')
                assets = data.get('assets', [])

                # Compare versions
                update_available = self._is_newer_version(latest_version, APP_VERSION)

                if update_available:
                    release_info = {
                        'version': latest_version,
                        'url': release_url,
                        'notes': release_notes,
                        'assets': [
                            {
                                'name': asset['name'],
                                'url': asset['browser_download_url'],
                                'size': asset['size']
                            }
                            for asset in assets
                        ]
                    }
                    callback(True, release_info)
                else:
                    callback(False, None)

            except Exception as e:
                # Network error or API issue - silently fail
                # Don't bother user with update check failures
                print(f"Update check failed: {e}")
                callback(False, None)
            finally:
                self._checking = False

        # Run in background thread
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """
        Compare version strings using semantic versioning.

        Args:
            latest: Latest version string (e.g., "1.0.1")
            current: Current version string (e.g., "1.0.0")

        Returns:
            True if latest > current
        """
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]

            # Pad with zeros if different lengths
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))

            # Compare each part
            for l, c in zip(latest_parts, current_parts):
                if l > c:
                    return True
                elif l < c:
                    return False

            return False  # Versions are equal

        except (ValueError, AttributeError):
            # Invalid version format
            return False


def check_for_updates_async(
    owner: str,
    repo: str,
    callback: Callable[[bool, Optional[dict]], None]
):
    """
    Convenience function to check for updates asynchronously.

    Args:
        owner: GitHub username
        repo: Repository name
        callback: Called with (update_available, release_info) when done
    """
    checker = UpdateChecker(owner, repo)
    checker.check_for_updates(callback)
