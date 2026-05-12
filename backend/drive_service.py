"""
Google Drive service using a Service Account.
Handles authentication and file search via the Drive API.
"""

import os
import json
import logging
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

MIME_TYPE_LABELS = {
    "application/vnd.google-apps.document": "Google Doc",
    "application/vnd.google-apps.spreadsheet": "Google Sheet",
    "application/vnd.google-apps.presentation": "Google Slides",
    "application/vnd.google-apps.form": "Google Form",
    "application/vnd.google-apps.folder": "Folder",
    "application/pdf": "PDF",
    "image/jpeg": "JPEG Image",
    "image/png": "PNG Image",
    "image/gif": "GIF Image",
    "image/webp": "WebP Image",
    "text/plain": "Text File",
    "text/csv": "CSV File",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Spreadsheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
    "application/zip": "ZIP Archive",
}


def get_drive_service():
    """Build and return an authenticated Google Drive service."""
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if creds_json:
        try:
            creds_info = json.loads(creds_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES
        )
    else:
        creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
        if not os.path.exists(creds_file):
            raise FileNotFoundError(
                f"Service account file '{creds_file}' not found. "
                "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE env var."
            )
        credentials = service_account.Credentials.from_service_account_file(
            creds_file, scopes=SCOPES
        )

    return build("drive", "v3", credentials=credentials)


def search_files(
    query: str,
    folder_id: Optional[str] = None,
    max_results: int = 10,
) -> list[dict]:
    """
    Search Google Drive files using the Drive API `q` parameter.

    Args:
        query: Drive API query string (e.g. "name contains 'report'")
        folder_id: Restrict search to this folder (and its children).
        max_results: Maximum number of results to return.

    Returns:
        List of file metadata dicts.
    """
    service = get_drive_service()

    # Scope query to folder if provided
    if folder_id:
        folder_clause = f"'{folder_id}' in parents"
        q = f"{folder_clause} and ({query})" if query.strip() else folder_clause
    else:
        q = query

    # Always exclude trashed files
    if "trashed" not in q:
        q = f"({q}) and trashed = false"

    logger.info("Drive API query: %s", q)

    try:
        response = (
            service.files()
            .list(
                q=q,
                pageSize=min(max_results, 50),
                fields=(
                    "nextPageToken, files("
                    "id, name, mimeType, modifiedTime, createdTime, "
                    "size, webViewLink, description, parents"
                    ")"
                ),
                orderBy="modifiedTime desc",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        logger.error("Drive API error: %s", e)
        raise RuntimeError(f"Google Drive API error: {e}") from e

    files = response.get("files", [])

    # Enrich with human-readable type label
    for f in files:
        f["typeLabel"] = MIME_TYPE_LABELS.get(f.get("mimeType", ""), f.get("mimeType", "Unknown"))

    return files


def format_files_for_display(files: list[dict]) -> str:
    """Convert a list of Drive file dicts into a readable markdown string."""
    if not files:
        return "No files found matching your search criteria."

    lines = [f"Found **{len(files)}** file(s):\n"]
    for i, f in enumerate(files, 1):
        modified = f.get("modifiedTime", "")[:10] if f.get("modifiedTime") else "N/A"
        link = f.get("webViewLink", "")
        name = f["name"]
        type_label = f.get("typeLabel", "Unknown")
        size = f.get("size")
        size_str = f" · {int(size) // 1024} KB" if size else ""

        lines.append(f"{i}. **{name}**")
        lines.append(f"   - 📄 Type: {type_label}{size_str}")
        lines.append(f"   - 🕒 Modified: {modified}")
        if link:
            lines.append(f"   - 🔗 [Open in Drive]({link})")
        lines.append("")

    return "\n".join(lines)
