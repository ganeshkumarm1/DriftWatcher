# @steered SNARE-1 2026-09-18
from urllib.parse import urlparse, urlencode, parse_qs


class ActivityProcessor:
    """Processes raw browser events into a structured activity summary."""

    _SEARCH_PARAMS = {"q", "search", "query"}

    def _normalize_url(self, url: str) -> str:
        """Strip uninformative query params and fragments; keep search queries."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=False)
            kept = {k: v for k, v in params.items() if k in self._SEARCH_PARAMS}
            query = urlencode(kept, doseq=True) if kept else ""
            return parsed._replace(query=query, fragment="").geturl()
        except Exception:
            return url

    def _infer_page_type(self, url: str, title: str) -> str:
        """Classify a URL into a semantic page type for LLM context."""
        u = url.lower()
        if "youtube.com/watch" in u or "youtu.be/" in u:
            return "video"
        if "youtube.com" in u:
            return "video_browse"
        if any(d in u for d in ("twitter.com", "x.com", "linkedin.com",
                                 "facebook.com", "instagram.com", "reddit.com")):
            return "social"
        if "amazon.com/dp/" in u or "amazon.com/s?" in u:
            return "shopping"
        if any(d in u for d in ("news.", "ycombinator.com", "medium.com", "substack.com")):
            return "article"
        if "code.amazon.com" in u:
            return "code_internal"
        if any(d in u for d in ("github.com", "gitlab.com")):
            return "code"
        if any(d in u for d in ("taskei.amazon.com", "sim.amazon.com", "issues.amazon.com")):
            return "ticket"
        if "w.amazon.com" in u or "wiki." in u:
            return "wiki_internal"
        if any(d in u for d in ("docs.", "developer.", "stackoverflow.com")):
            return "docs"
        if "amazon.com" in u:
            return "work_internal"
        return "webpage"

    def _build_pages(self, events):
        """Aggregate events by normalized URL into page summaries."""
        pages = {}

        for e in events:
            raw_url = e.get("url")
            title = e.get("title")
            if not raw_url or not title:
                continue

            url = self._normalize_url(raw_url)
            duration_min = round(e.get("durationMs", 5000) / 60000, 2)
            duration_min = max(duration_min, 0.08)
            content = e.get("content", "")

            if url not in pages:
                pages[url] = {
                    "title": title,
                    "url": url,
                    "content": content[:400] if content else "",
                    "duration_min": 0.0,
                    "scroll_count": 0,
                    "key_count": 0,
                    "page_type": self._infer_page_type(url, title),
                }
            else:
                # Keep the longest non-empty content seen for this URL
                if content and len(content) > len(pages[url]["content"]):
                    pages[url]["content"] = content[:400]

            pages[url]["duration_min"] = round(pages[url]["duration_min"] + duration_min, 2)
            pages[url]["scroll_count"] += e.get("scrollCount", 0)
            pages[url]["key_count"] += e.get("keyCount", 0)

        sorted_pages = sorted(pages.values(), key=lambda p: p["duration_min"], reverse=True)
        return sorted_pages[:10]

    def aggregate(self, events) -> dict:
        """Aggregate events into activity summary for LLM assessment."""
        pages = self._build_pages(events)
        total_minutes = round(sum(p["duration_min"] for p in pages), 2) or 1.0

        return {
            "total_minutes": total_minutes,
            "pages": pages,
        }
