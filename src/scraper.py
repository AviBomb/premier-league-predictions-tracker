"""
YouTube Data API Scraper Module
Supports arrays of video URLs / IDs, handles pagination, and extracts edit flags.
"""
import re
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def extract_video_id(url_or_id: str) -> str:
    """Extracts the 11-character video ID from any YouTube URL format or raw ID."""
    pattern = r"(?:v=|\/live\/|\/shorts\/|\/embed\/|youtu\.be\/|^)([0-9A-Za-z_-]{11})(?:[&?]|$)"
    match = re.search(pattern, url_or_id.strip())
    if match:
        return match.group(1)
    clean = re.sub(r"[^0-9A-Za-z_-]", "", url_or_id.strip())
    if len(clean) == 11:
        return clean
    raise ValueError(f"Invalid YouTube Video ID in: '{url_or_id}'")


def scrape_youtube_comments(api_key: str, video_urls: List[str]) -> List[Dict[str, Any]]:
    """
    Fetches all top-level comments and edit metadata from a list of YouTube URLs.
    """
    youtube = build("youtube", "v3", developerKey=api_key)
    all_comments = []
    seen_ids = set()

    for url in video_urls:
        vid_id = extract_video_id(url)
        print(f"[*] Scraping YouTube comments for Video ID: {vid_id}...")
        next_token = None

        try:
            while True:
                resp = youtube.commentThreads().list(
                    part="snippet",
                    videoId=vid_id,
                    maxResults=100,
                    pageToken=next_token,
                    textFormat="plainText"
                ).execute()

                for item in resp.get("items", []):
                    top = item["snippet"]["topLevelComment"]["snippet"]
                    c_id = item["snippet"]["topLevelComment"]["id"]
                    if c_id in seen_ids:
                        continue
                    seen_ids.add(c_id)

                    pub_at = top.get("publishedAt")
                    upd_at = top.get("updatedAt")

                    all_comments.append({
                        "comment_id": c_id,
                        "video_id": vid_id,
                        "author": top.get("authorDisplayName", "Anonymous"),
                        "author_channel_url": top.get("authorChannelUrl", ""),
                        "published_at": pub_at,
                        "updated_at": upd_at,
                        "is_edited": pub_at != upd_at,
                        "like_count": top.get("likeCount", 0),
                        "text": top.get("textDisplay", "")
                    })

                next_token = resp.get("nextPageToken")
                if not next_token:
                    break
        except HttpError as e:
            print(f"[!] HTTP Error for video {vid_id}: {e}")

    print(f"[+] Total Unique Comments Scraped: {len(all_comments)}")
    return all_comments
