"""Read photos from a Google Drive folder using a service account."""

from __future__ import annotations

import io
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Read-only is all we need: the automation never modifies your Drive.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def build_service(service_account_json: str):
    info = json.loads(service_account_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_images(service, folder_id: str) -> list[dict]:
    """Return image files in the folder, oldest first, with id/name/mimeType."""
    query = (
        f"'{folder_id}' in parents "
        "and mimeType contains 'image/' "
        "and trashed = false"
    )
    files: list[dict] = []
    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, createdTime)",
                orderBy="createdTime",
                pageToken=page_token,
                pageSize=100,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def download_image(service, file_id: str) -> bytes:
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()
