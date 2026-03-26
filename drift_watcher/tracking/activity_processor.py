from collections import defaultdict


class ActivityProcessor:
    """Processes raw browser events into a structured activity summary."""

    def _build_pages(self, events):
        """Aggregate events by URL into page summaries with total time."""
        pages = {}

        for e in events:
            url = e.get("url")
            title = e.get("title")
            if not url or not title:
                continue

            duration_min = round(e.get("durationMs", 5000) / 60000, 2)
            duration_min = max(duration_min, 0.08)
            content = e.get("content", "")

            if url not in pages:
                pages[url] = {
                    "title": title,
                    "url": url,
                    "content": content[:300] if content else "",
                    "duration_min": 0.0,
                }
            pages[url]["duration_min"] = round(pages[url]["duration_min"] + duration_min, 2)

        # Sort by time spent descending, return top 10
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
