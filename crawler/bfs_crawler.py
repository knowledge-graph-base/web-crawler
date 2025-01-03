# crawler/bfs_crawler.py

from collections import deque
import os
import time
from datetime import datetime

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from utils import clean_filename, timestamp_str


SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "crawl_log.md")

class BFSCrawler:
    def __init__(self, driver, max_depth=2, user_decision_callback=None):
        """
        :param driver: Selenium WebDriver instance
        :param max_depth: Maximum depth for BFS
        :param user_decision_callback: Function to handle ambiguous choices (simulating AI)
        """
        self.driver = driver
        self.max_depth = max_depth
        self.user_decision_callback = user_decision_callback

        # Graph to store visited pages
        self.graph = {}  # { url: {"links": set([...]), "title": "..."} }
        self.visited = set()

    def crawl(self, start_url):
        queue = deque([(start_url, 0)])
        # Track which URLs were reached from where
        self.referrers = {}  # {url: set(referrer_urls)}
        
        while queue:
            url, depth = queue.popleft()
            if url in self.visited:
                # Log when we find a page through multiple paths
                if url in self.graph:
                    current_referrer = list(queue)[-1][0] if queue else start_url
                    if url not in self.referrers:
                        self.referrers[url] = set()
                    self.referrers[url].add(current_referrer)
                continue
                
            self.visited.add(url)

            # Go to the URL
            success = self.visit_url(url)
            if not success:
                continue

            # Extract links
            links = self.extract_links()
            # Store to graph
            page_title = self.driver.title
            self.graph[url] = {
                "links": set(links),
                "title": page_title
            }

            # BFS Enqueue
            if depth < self.max_depth:
                for link in links:
                    if link not in self.visited:
                        queue.append((link, depth + 1))

        # Generate visualization at the end of crawl
        self.log_crawl_visualization()
        return self.graph

    def visit_url(self, url):
        try:
            print(f"Visiting: {url}")  # Console feedback
            self.driver.get(url)
            self.driver.implicitly_wait(10)
            time.sleep(1)  # increase wait time to 2 seconds            

            # Take screenshot and continue as before...
            filename_part = clean_filename(url)[:50]
            screenshot_name = f"{timestamp_str()}_{filename_part}.png"
            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
            self.driver.save_screenshot(screenshot_path)
            
            # Log info to file
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n## Page: {url}\n")
                f.write(f"**Title**: {self.driver.title}\n")
                f.write(f"**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Screenshot**: `{screenshot_name}`\n")
                
            return True
            
        except TimeoutException:
            print(f"[Timeout] Unable to load {url}")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n## ❌ Failed: {url}\n")
                f.write("**Error**: Timeout while loading page\n\n---\n")
            return False
        except Exception as e:
            print(f"[Error] Failed to load {url}: {str(e)}")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n## ❌ Failed: {url}\n")
                f.write(f"**Error**: {str(e)}\n\n---\n")
            return False

    def extract_links(self):
        """Extract all anchor hrefs from the current page."""
        links = []
        a_tags = self.driver.find_elements(By.TAG_NAME, "a")
        for a in a_tags:
            href = a.get_attribute("href")
            if href and href.startswith("http"):
                links.append(href)
        return links

    def detect_interactive_elements(self):
        """Detect forms, buttons and other interactive elements on the page."""
        interactive_elements = {
            'forms': self.driver.find_elements(By.TAG_NAME, 'form'),
            'buttons': self.driver.find_elements(By.TAG_NAME, 'button'),
            'inputs': self.driver.find_elements(By.TAG_NAME, 'input')
        }
        
        return {k: v for k, v in interactive_elements.items() if v}

    def handle_interactive_elements(self):
        """Handle any interactive elements found on the page."""
        if not self.user_decision_callback:
            return

        elements = self.detect_interactive_elements()
        if not elements:
            return

        # Log found elements
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n**Interactive Elements Found:**\n")
            
        for element_type, elements_list in elements.items():
            message = f"Found {len(elements_list)} {element_type}. Interact with them?"
            decision = self.user_decision_callback(message)
            
            if decision.lower() == 'yes':
                # Log the decision
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"- Decided to interact with {element_type}\n")
                
                # Handle each element based on its type
                for element in elements_list:
                    try:
                        if element_type == 'forms':
                            self.handle_form(element)
                        elif element_type in ('buttons', 'inputs'):
                            self.handle_clickable(element)
                    except Exception as e:
                        print(f"Error handling {element_type}: {str(e)}")

    def handle_form(self, form):
        """Handle form interaction based on user input."""
        inputs = form.find_elements(By.TAG_NAME, 'input')
        for input_field in inputs:
            input_type = input_field.get_attribute('type')
            if input_type in ['text', 'email', 'password']:
                placeholder = input_field.get_attribute('placeholder') or input_field.get_attribute('name')
                value = self.user_decision_callback(f"Enter value for {placeholder}: ")
                if value.lower() != 'skip':
                    input_field.send_keys(value)

    def handle_clickable(self, element):
        """Handle clickable element interaction."""
        element_text = element.text or element.get_attribute('value') or element.get_attribute('name')
        decision = self.user_decision_callback(f"Click on '{element_text}'?")
        if decision.lower() == 'yes':
            try:
                element.click()
                time.sleep(1)  # Wait for any potential page changes
            except Exception as e:
                print(f"Failed to click element: {str(e)}")

    def log_crawl_visualization(self):
        """Generate a visual representation of the crawl in the log file."""
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            # Add a summary section
            f.write("\n## Crawl Summary\n")
            f.write(f"- Total Pages Crawled: {len(self.graph)}\n")
            f.write(f"- Max Depth: {self.max_depth}\n\n")

            # Add a tree visualization
            f.write("## Site Structure (Tree View)\n")
            f.write("```\n")
            self._write_tree_structure(f)
            f.write("```\n\n")

            # Add a Mermaid diagram
            f.write("## Site Map (Mermaid Diagram)\n")
            f.write("```mermaid\n")
            f.write("graph TD\n")
            self._write_mermaid_diagram(f)
            f.write("```\n\n")

            # Add information about pages with multiple entry points
            if hasattr(self, 'referrers'):
                multi_path_pages = {url: refs for url, refs in self.referrers.items() if len(refs) > 1}
                if multi_path_pages:
                    f.write("\n## Pages Accessible from Multiple Paths\n")
                    for url, referrers in multi_path_pages.items():
                        f.write(f"\n### {url}\n")
                        f.write("Accessible from:\n")
                        for ref in referrers:
                            f.write(f"- {ref}\n")
                    f.write("\n")

    def _write_tree_structure(self, file):
        """Write a tree-like structure of the crawled pages."""
        def _short_url(url):
            return url.replace('https://', '').replace('http://', '')[:50]

        def _write_node(url, indent=0, visited=None):
            if visited is None:
                visited = set()
            
            # Check for cyclic references
            if url in visited:
                file.write(f"{'    ' * indent}└── {_short_url(url)} (cyclic)\n")
                return
            visited.add(url)

            file.write(f"{'    ' * indent}└── {_short_url(url)}\n")
            if url in self.graph:
                for link in sorted(self.graph[url]['links'])[:5]:  # Limit to 5 children for readability
                    _write_node(link, indent + 1, visited.copy())

        # Start with the root (first URL added to the graph)
        if self.graph:
            root_url = next(iter(self.graph))
            _write_node(root_url)

    def _write_mermaid_diagram(self, file):
        """Write a Mermaid.js compatible diagram of the crawled pages."""
        def _node_id(url):
            # Create a unique, safe node ID
            return f"page_{hash(url) % 10000}"

        def _short_label(url):
            return url.replace('https://', '').replace('http://', '')[:20] + "..."

        # Prevent duplicate nodes
        written_nodes = set()
        for url in self.graph:
            node_id = _node_id(url)
            if node_id not in written_nodes:
                file.write(f'    {node_id}["{_short_label(url)}"]\n')
                written_nodes.add(node_id)

        # Prevent duplicate edges
        written_edges = set()
        for url, data in self.graph.items():
            source_id = _node_id(url)
            for link in list(data['links'])[:3]:
                target_id = _node_id(link)
                edge = f"{source_id}-->{target_id}"
                if edge not in written_edges:
                    file.write(f"    {edge}\n")
                    written_edges.add(edge)
