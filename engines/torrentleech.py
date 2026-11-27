# VERSION: 2.0
# AUTHORS: github.com/444995 (updated 2026)

import gzip
import http.cookiejar as cookielib
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from math import ceil
from urllib.error import HTTPError, URLError

from novaprinter import prettyPrinter

# ==============================================================================
# USER SETTINGS
# ==============================================================================

# OPTION A (Recommended - works with 2FA and Cloudflare):
# Paste the full Cookie header and exact User-Agent from your browser.
# If COOKIE is set, USERNAME/PASSWORD login is skipped.
COOKIE = ""
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) "
    "Gecko/20100101 Firefox/133.0"
)

# Optional: add any extra custom headers here, e.g. {"Accept-Language": "en-US,en;q=0.9"}
EXTRA_HEADERS = {}

# OPTION B (Credential login - only used if COOKIE is left empty):
USERNAME = "REPLACE_ME"
PASSWORD = "REPLACE_ME"
ALT_2FA_TOKEN = ""  # Optional: your TorrentLeech Alt 2FA Token from Profile settings

# General settings
CACHE_LOGIN_COOKIES = True
COOKIES_FILE_NAME = "torrentleech.cookies"
MAX_PAGES = 5  # Prevents rate-limiting on broad searches (50 results per page)
REQUEST_TIMEOUT = 15

# ==============================================================================


class torrentleech:
    url = "https://www.torrentleech.org"
    name = "TorrentLeech"
    supported_categories = {
        "all": "0",
        "anime": "34",
        "movies": "8,9,11,37,43,14,12,13,47,15,29",
        "tv": "26,32,27",
        "music": "31,16",
        "games": "17,42,18,19,40,20,21,39,49,22,28,30,48",
        "software": "23,24,25,33",
        "books": "45,46",
    }
    cookies_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        COOKIES_FILE_NAME,
    )

    def __init__(self):
        self.login_url = f"{self.url}/user/account/login/"
        self.torrents_per_page = 50
        self.cookiejar = cookielib.LWPCookieJar()
        self.opener = self._create_opener()
        self._authenticated = False

    def _create_opener(self):
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookiejar)
        )
        headers = {
            "User-Agent": USER_AGENT.strip(),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Referer": f"{self.url}/torrents/browse",
            "X-Requested-With": "XMLHttpRequest",
        }

        if COOKIE.strip():
            headers["Cookie"] = COOKIE.strip()

        if EXTRA_HEADERS:
            headers.update(EXTRA_HEADERS)

        opener.addheaders = list(headers.items())
        return opener

    def _decompress(self, raw_data, encoding):
        if not encoding:
            return raw_data
        encoding = encoding.lower()
        if "gzip" in encoding:
            return gzip.decompress(raw_data)
        if "deflate" in encoding:
            try:
                return zlib.decompress(raw_data)
            except zlib.error:
                return zlib.decompress(raw_data, -zlib.MAX_WBITS)
        return raw_data

    def _make_request(self, url, data=None):
        try:
            encoded_data = urllib.parse.urlencode(data).encode("utf-8") if data else None
            with self.opener.open(url, encoded_data, timeout=REQUEST_TIMEOUT) as response:
                raw = response.read()
                return self._decompress(raw, response.info().get("Content-Encoding"))
        except HTTPError as e:
            print(f"[TorrentLeech] HTTP error {e.code} for {url}: {e.reason}", file=sys.stderr)
            return None
        except URLError as e:
            print(f"[TorrentLeech] Connection error for {url}: {e.reason}", file=sys.stderr)
            return None

    def _ensure_authenticated(self):
        if self._authenticated:
            return True

        # Option A: Browser cookie header provided directly
        if COOKIE.strip():
            self._authenticated = True
            return True

        # Option B: Cached cookie file or credential login
        if CACHE_LOGIN_COOKIES and os.path.exists(self.cookies_file_path):
            try:
                self.cookiejar.load(
                    self.cookies_file_path, ignore_discard=True, ignore_expires=True
                )
                if self._is_logged_in():
                    self._authenticated = True
                    return True
            except Exception as e:
                print(f"[TorrentLeech] Could not load cached cookies: {e}", file=sys.stderr)

        data = {
            "username": USERNAME,
            "password": PASSWORD,
            "remember_me": "on",
        }
        if ALT_2FA_TOKEN.strip():
            data["alt2FAToken"] = ALT_2FA_TOKEN.strip()

        self._make_request(self.login_url, data)

        if not self._is_logged_in():
            print(
                "[TorrentLeech] Login failed. Check credentials, set ALT_2FA_TOKEN, "
                "or paste your browser COOKIE + USER_AGENT.",
                file=sys.stderr,
            )
            return False

        if CACHE_LOGIN_COOKIES:
            try:
                self.cookiejar.save(
                    self.cookies_file_path, ignore_discard=True, ignore_expires=True
                )
            except Exception as e:
                print(f"[TorrentLeech] Could not save cookies: {e}", file=sys.stderr)

        self._authenticated = True
        return True

    def _is_logged_in(self):
        return any(cookie.name in ("tlpass", "tluid") for cookie in self.cookiejar)

    def download_torrent(self, info):
        if not self._ensure_authenticated():
            return

        torrent_file = self._make_request(info)
        if not torrent_file:
            return

        # Guard against saving an HTML login/Cloudflare error page as a .torrent file
        if torrent_file.lstrip().startswith(b"<"):
            print(
                "[TorrentLeech] Received HTML instead of a .torrent file. "
                "Your cookie/session may have expired.",
                file=sys.stderr,
            )
            return

        with tempfile.NamedTemporaryFile(suffix=".torrent", delete=False) as file:
            file.write(torrent_file)
        print(f"{file.name} {info}")

    def search(self, what, cat="all"):
        if not self._ensure_authenticated():
            return

        category_str = self.supported_categories.get(cat, "0")
        search_url = self._establish_search_url(what, category_str)

        first_page = self._fetch_json(f"{search_url}/page/1")
        if not first_page:
            return

        for torrent in first_page.get("torrentList", []):
            self._print_torrent(torrent)

        num_torrents = first_page.get("numFound", 0)
        total_pages = min(ceil(num_torrents / self.torrents_per_page), MAX_PAGES)

        for page in range(2, total_pages + 1):
            page_data = self._fetch_json(f"{search_url}/page/{page}")
            if not page_data:
                break
            for torrent in page_data.get("torrentList", []):
                self._print_torrent(torrent)

    def _establish_search_url(self, what, category_str):
        # Decode first so qBittorrent's pre-encoded query isn't double-encoded
        encoded_query = urllib.parse.quote(urllib.parse.unquote(what), safe="")
        base_url = f"{self.url}/torrents/browse/list"
        if category_str != "0":
            return f"{base_url}/categories/{category_str}/query/{encoded_query}"
        return f"{base_url}/query/{encoded_query}"

    def _fetch_json(self, url):
        response = self._make_request(url)
        if not response:
            return None
        try:
            return json.loads(response.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            print(
                "[TorrentLeech] Invalid JSON response (likely expired cookie, "
                "2FA login prompt, or Cloudflare block).",
                file=sys.stderr,
            )
            return None

    def _parse_pub_date(self, timestamp_str):
        if not timestamp_str:
            return -1
        try:
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            return int(dt.replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            return -1

    def _print_torrent(self, torrent):
        fid = torrent.get("fid", "")
        filename = urllib.parse.quote(torrent.get("filename", ""))
        prettyPrinter({
            "link": f"{self.url}/download/{fid}/{filename}",
            "name": torrent.get("name", "Unknown"),
            "size": f"{torrent.get('size', -1)} B",
            "seeds": str(torrent.get("seeders", -1)),
            "leech": str(torrent.get("leechers", -1)),
            "engine_url": self.url,
            "desc_link": f"{self.url}/torrent/{fid}",
            "pub_date": self._parse_pub_date(torrent.get("addedTimestamp")),
        })


if __name__ == "__main__":
    engine = torrentleech()
    engine.search("ubuntu")