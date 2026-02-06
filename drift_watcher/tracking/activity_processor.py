import json
import hashlib
from pathlib import Path
from collections import defaultdict
from ..llm.reasoner import LLMReasoner


class ActivityProcessor:
    """Processes and classifies user activity from events."""
    
    def __init__(self, cache_file="activity_cache.json", reasoner=None):
        self.cache_file = Path(cache_file)
        self.cache_file.touch(exist_ok=True)
        self.reasoner = reasoner or LLMReasoner()
        self._cache = self._load_cache()
    
    def _load_cache(self):
        """Load classification cache."""
        try:
            return json.loads(self.cache_file.read_text())
        except Exception:
            return {}
    
    def _save_cache(self):
        """Save classification cache."""
        self.cache_file.write_text(json.dumps(self._cache, indent=2))
    
    def _fingerprint(self, slice_):
        """Generate fingerprint for activity slice."""
        # Include content in fingerprint for better caching
        key = f"{slice_['title']}|{slice_['url']}|{slice_.get('content', '')[:100]}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _build_slices(self, events):
        """Convert events to activity slices."""
        slices = []
        
        for e in events:
            url = e.get("url")
            title = e.get("title")
            content = e.get("content", "")
            
            if not url or not title:
                continue
            
            duration_min = round(e.get("durationMs", 5000) / 60000, 2)
            
            slices.append({
                "title": title,
                "url": url,
                "content": content[:300] if content else "",  # First 300 chars
                "duration_minutes": max(duration_min, 0.08),
                "scroll_count": e.get("scrollCount", 0),
                "key_count": e.get("keyCount", 0)
            })
        
        return slices
    
    def _classify_slices(self, slices):
        """Classify activity slices with caching."""
        results = []
        cache_updated = False
        
        for slice_ in slices:
            fp = self._fingerprint(slice_)
            
            if fp in self._cache:
                results.append({**slice_, "category": self._cache[fp]})
                continue
            
            category = self.reasoner.classify_activity(slice_)
            self._cache[fp] = category
            cache_updated = True
            results.append({**slice_, "category": category})
        
        if cache_updated:
            self._save_cache()
        
        return results
    
    def _extract_titles(self, events, max_titles=3):
        """Extract safe, non-generic titles from events."""
        titles = []
        GENERIC = {"YouTube", "Home", "New Tab", ""}
        
        for e in events:
            title = e.get("title")
            if not title:
                continue
            
            title = title.strip()
            
            if len(title) > 80:
                title = title[:77] + "..."
            
            titles.append(title)
        
        unique_titles = list(dict.fromkeys(titles))
        filtered = [t for t in unique_titles if t not in GENERIC]
        
        return filtered[-max_titles:]
    
    def aggregate(self, events):
        """Aggregate events into activity summary."""
        slices = self._build_slices(events)
        classified = self._classify_slices(slices)
        
        totals = defaultdict(float)
        total_time = 0.0
        
        for s in classified:
            totals[s["category"]] += s["duration_minutes"]
            total_time += s["duration_minutes"]
        
        total_time = total_time or 1.0
        
        breakdown = {
            k: round((v / total_time) * 100, 1)
            for k, v in totals.items()
        }
        
        # Extract sample content from top pages
        sample_content = []
        for s in classified[:3]:  # Top 3 pages
            if s.get("content"):
                sample_content.append(s["content"])
        
        return {
            "total_minutes": round(total_time, 2),
            "breakdown": breakdown,
            "sample_titles": self._extract_titles(events),
            "sample_content": sample_content
        }
