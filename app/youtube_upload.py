"""Upload one trusted workflow artifact to the existing YouTube channel."""
import hashlib
import json
import os
import sys
from pathlib import Path

import requests

CHANNEL = "UCxOFjW_MRwbakr9364KreTQ"
YOUTUBE = "https://www.googleapis.com/youtube/v3"


def call(method, url, *, expected=(200,), **kwargs):
    try:
        response = requests.request(method, url, timeout=(15, 180), **kwargs)
    except requests.RequestException:
        raise RuntimeError("External request failed. Check the upload history before retrying.") from None
    if response.status_code not in expected:
        raise RuntimeError(f"External API rejected {method} (HTTP {response.status_code}).")
    return response


def main(directory):
    video = directory / "mente-inabalavel.mp4"
    credits = json.loads((directory / "credits.json").read_text(encoding="utf-8"))
    attribution = "\n".join(
        f"{item['title']} — {item['author']} | {item['license']} "
        f"{item['license_url']} | {item['source']} | Alterações: {item['changes']}"
        for item in credits
    )
    description = "Domine sua mente. Transforme sua vida.\n\nCréditos de imagem\n" + attribution
    if len(description.encode("utf-8")) > 5000 or not video.stat().st_size:
        raise RuntimeError("Invalid video or attribution exceeds the YouTube limit.")
    with video.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()

    repo = os.environ["GITHUB_REPOSITORY"]
    github = f"https://api.github.com/repos/{repo}/git"
    gh_headers = {"Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                  "Accept": "application/vnd.github+json"}
    prefix = f"tags/youtube-upload/{digest}"
    history = call("GET", f"{github}/matching-refs/{prefix}", headers=gh_headers).json()
    for entry in history:
        ref = entry["ref"]
        if ref.startswith(f"refs/{prefix}/uploaded/"):
            print(f"Already uploaded as {ref.rsplit('/', 1)[1]}.")
            return
    if history:
        raise RuntimeError("Upload already reserved. Reconcile the pending tag with YouTube Studio before retrying.")

    token = call("POST", "https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    channels = call("GET", f"{YOUTUBE}/channels", headers=headers,
                    params={"part": "id", "mine": "true"}).json()["items"]
    if [channel["id"] for channel in channels] != [CHANNEL]:
        raise RuntimeError("OAuth is not bound to the expected YouTube channel.")

    sha = os.environ["GITHUB_SHA"]
    def record(state):
        call("POST", f"{github}/refs", headers=gh_headers, expected=(201,),
             json={"ref": f"refs/{prefix}/{state}", "sha": sha})

    # Reserve before initiating the upload. Any ambiguous failure stays reserved
    # so a retry cannot create a second copy.
    record("pending")
    size = str(video.stat().st_size)
    start = call("POST", "https://www.googleapis.com/upload/youtube/v3/videos",
                 headers={**headers, "X-Upload-Content-Type": "video/mp4",
                          "X-Upload-Content-Length": size},
                 params={"uploadType": "resumable", "part": "snippet,status"},
                 json={"snippet": {"title": "Disciplina quando ninguém está olhando",
                                   "description": description, "categoryId": "22",
                                   "defaultLanguage": "pt-BR", "tags": [f"ams-sha256:{digest}"]},
                       "status": {"privacyStatus": "private"}})
    session = start.headers["Location"]
    if not session.startswith("https://www.googleapis.com/"):
        raise RuntimeError("Unexpected YouTube upload endpoint.")
    with video.open("rb") as source:
        result = call("PUT", session, headers={**headers, "Content-Type": "video/mp4",
                                              "Content-Length": size},
                      data=source, expected=(200, 201)).json()
    video_id = result["id"]
    record(f"uploaded/{video_id}")
    verified = call("GET", f"{YOUTUBE}/videos", headers=headers,
                    params={"part": "snippet,status", "id": video_id}).json()["items"]
    if len(verified) != 1 or verified[0]["snippet"]["channelId"] != CHANNEL or verified[0]["status"]["privacyStatus"] != "private":
        raise RuntimeError("Upload recorded but channel or privacy verification failed.")
    print(f"Verified private YouTube video: {video_id}")


if __name__ == "__main__":
    try:
        main(Path(sys.argv[1]))
    except (RuntimeError, OSError, ValueError, KeyError, IndexError) as error:
        # Avoid logging response bodies, credentials, or resumable upload URLs.
        message = str(error) if isinstance(error, RuntimeError) else "Invalid configuration, artifact or API response."
        sys.exit(message)
