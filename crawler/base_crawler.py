from collections import deque
from typing import Set, Dict, Optional, List

class BaseCrawler:
    def __init__(self, max_depth: int = 2):
        self.max_depth = max_depth
        self.graph = {}  # { url: {"links": set([...]), "title": "..."} }
        self.visited = set()
        self.referrers = {}  # {url: set(referrer_urls)}

    def crawl(self, start_url: str) -> Dict:
        """Core BFS crawling logic"""
        queue = deque([(start_url, 0)])
        
        while queue:
            url, depth = queue.popleft()
            if url in self.visited:
                self._update_referrers(url, queue, start_url)
                continue
                
            self.visited.add(url)
            
            # Visit URL and get page data
            success, page_data = self._process_page(url)
            if not success:
                continue

            # Update graph with page data
            self.graph[url] = page_data
            
            # Notify observers of progress
            self._notify_progress(url)

            # BFS Enqueue
            if depth < self.max_depth:
                for link in page_data["links"]:
                    if link not in self.visited:
                        queue.append((link, depth + 1))

        return self.graph

    def _update_referrers(self, url: str, queue: deque, start_url: str) -> None:
        """Track multiple paths to the same page"""
        if url in self.graph:
            current_referrer = list(queue)[-1][0] if queue else start_url
            if url not in self.referrers:
                self.referrers[url] = set()
            self.referrers[url].add(current_referrer)

    def _process_page(self, url: str) -> tuple[bool, Optional[Dict]]:
        """
        Process a single page. To be implemented by subclasses.
        Returns (success, page_data)
        """
        raise NotImplementedError

    def _notify_progress(self, url: str) -> None:
        """
        Notify observers of crawling progress. To be implemented by subclasses.
        """
        raise NotImplementedError 