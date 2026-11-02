import time
import urllib.request
import urllib.robotparser
import urllib.error
import urllib.parse
import threading
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from backend.config import USER_AGENT, REQUEST_TIMEOUT

logger = logging.getLogger("transitnotice.fetcher")

class FetchError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class Fetcher:
    """
    Standard library HTTP fetcher adhering to strict ethical scraping:
    - robots.txt compliance (404 = allow; 5xx/403/unreadable = deny)
    - 1 req/sec per host rate limiting
    - 3 attempts with 2s/4s exponential backoff
    - 15-30s timeout
    """
    def __init__(self):
        self._robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last_request_time: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _rate_limit(self, host: str):
        with self._lock:
            last = self._last_request_time.get(host, 0.0)
            elapsed = time.time() - last
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            self._last_request_time[host] = time.time()

    def check_robots(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return True

        # Localhost/demo source endpoints are always allowed
        if parsed.netloc.startswith("127.0.0.1") or parsed.netloc.startswith("localhost"):
            return True

        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{base_url}/robots.txt"

        with self._lock:
            if base_url in self._robots_cache:
                rp = self._robots_cache[base_url]
                return rp.can_fetch(USER_AGENT, url)

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=25) as resp:
                status = resp.status
                if status == 200:
                    content = resp.read().decode("utf-8", errors="replace")
                    rp.parse(content.splitlines())
                else:
                    rp.allow_all = True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # 404 = allow
                rp.allow_all = True
            elif e.code in (401, 403, 500, 502, 503, 504):
                # 5xx / 403 = deny
                rp.disallow_all = True
            else:
                rp.allow_all = True
        except Exception:
            # Unreadable / network error on robots.txt = deny to be safe
            rp.disallow_all = True

        with self._lock:
            self._robots_cache[base_url] = rp

        return rp.can_fetch(USER_AGENT, url)

    def fetch_url(self, url: str) -> str:
        """Fetches raw text content from URL with rate limiting, robots check, and retries."""
        if not self.check_robots(url):
            raise FetchError(f"URL access disallowed by robots.txt: {url}", status_code=403)

        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc

        retries = 3
        delays = [2.0, 4.0]
        last_err = None

        for attempt in range(1, retries + 1):
            self._rate_limit(host)
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,application/xml,application/json,*/*;q=0.9"
                    }
                )
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                    if resp.status == 200:
                        raw = resp.read()
                        # Try decoding
                        charset = resp.headers.get_content_charset() or "utf-8"
                        try:
                            return raw.decode(charset)
                        except UnicodeDecodeError:
                            return raw.decode("utf-8", errors="replace")
                    else:
                        raise FetchError(f"HTTP {resp.status} fetching {url}", status_code=resp.status)

            except urllib.error.HTTPError as he:
                last_err = FetchError(f"HTTP {he.code}: {he.reason}", status_code=he.code)
                if he.code in (500, 502, 503, 504, 408):
                    logger.warning(f"Attempt {attempt}/{retries} got HTTP {he.code} for {url}")
                else:
                    raise last_err
            except Exception as ex:
                last_err = FetchError(f"Network error: {str(ex)}", status_code=None)
                logger.warning(f"Attempt {attempt}/{retries} network error for {url}: {ex}")

            if attempt < retries:
                time.sleep(delays[attempt - 1])

        raise last_err or FetchError(f"Failed to fetch {url} after {retries} attempts")

class BaseSourceAdapter(ABC):
    def __init__(self, source_key: str, label: str, agency: str, operator_type: str, base_url: str):
        self.source_key = source_key
        self.label = label
        self.agency = agency
        self.operator_type = operator_type
        self.base_url = base_url

    @abstractmethod
    def fetch_notices(self, fetcher: Fetcher) -> List[Dict[str, Any]]:
        """Parses source data into standard list of notice dictionaries."""
        pass

