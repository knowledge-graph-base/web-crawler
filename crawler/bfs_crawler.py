# crawler/bfs_crawler.py

from collections import deque
import os
import time

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
        while queue:
            url, depth = queue.popleft()
            if url in self.visited:
                continue
            self.visited.add(url)

            # Go to the URL
            success = self.visit_url(url)
            if not success:
                continue

            # Handle any interactive elements before extracting links
            self.handle_interactive_elements()

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

        return self.graph

    def visit_url(self, url):
        try:
            self.driver.get(url)
            time.sleep(1)  # let the page load

            # Take screenshot
            filename_part = clean_filename(url)[:50]  # limit length
            screenshot_name = f"{timestamp_str()}_{filename_part}.png"
            screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
            self.driver.save_screenshot(screenshot_path)
            
            # Log info to file
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"## Visited: {url}\n")
                f.write(f"**Title**: {self.driver.title}\n\n")
                f.write(f"**Screenshot**: `{screenshot_name}`\n\n")
            
            return True
        except TimeoutException:
            print(f"[Timeout] Unable to load {url}")
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
