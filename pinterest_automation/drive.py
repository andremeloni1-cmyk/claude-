"""Read photos from a Google Drive folder using a service account."""

from __future__ import annotations

import base64
import binascii
import io
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Read-only is all we need: the automation never modifies your Drive.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _parse_service_account(value: str) -> dict:
    """Accept the service account either as raw JSON or base64-encoded JSON.

    Raw JSON is easy to corrupt when pasting into a secret (the long
    private_key line in particular), so a base64 blob is also accepted as a
    paste-safe alternative.
    """
    text = value.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        decoded = base64.b64decode(text, validate=True).decode("utf-8")
        return json.loads(decoded)
    except (binascii.Error, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not valid. Paste either the exact "
            "contents of the service account .json file, or a base64-encoded "
            "version of that file."
        ) from exc


def build_service(service_account_json: str):
    info = _parse_service_account(service_account_json)
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
