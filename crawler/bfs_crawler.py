# crawler/bfs_crawler.py

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
import time
import os
import json
import logging

from base_crawler import BaseCrawler
from visualization_handler import CrawlVisualizer
from interaction_handler import InteractionHandler
from utils import clean_filename, timestamp_str
from dom_actions import DOMActions
from selenium.webdriver.common.by import By
from element_tracker import ElementTracker

class BFSCrawler(BaseCrawler):
    def __init__(self, driver: WebDriver, max_depth: int = 2, user_decision_callback=None):
        super().__init__(max_depth)
        self.driver = driver
        base_dir = os.path.join(os.path.dirname(__file__), "..")
        self.screenshot_dir = os.path.join(base_dir, "screenshots")
        self.log_file = os.path.join(base_dir, "crawl_log.md")
        
        self.visualizer = CrawlVisualizer(self.log_file)
        self.interaction_handler = InteractionHandler(driver, user_decision_callback) if user_decision_callback else None
        self.dom_actions = DOMActions(driver)
        self.element_tracker = ElementTracker(base_dir)
        logging.basicConfig(level=logging.INFO)

    def _process_page(self, url: str) -> tuple[bool, dict]:
        """Process a single page during crawling."""
        success = self._visit_url(url)
        if not success:
            return False, None

        # Get all interactive elements
        interactive_elements = self.dom_actions.find_interactive_elements()
        
        # Store information about interactive elements
        page_info = {
            "links": set(self._extract_links()),
            "title": self.driver.title,
            "interactive_elements": {
                element_type: [
                    self.dom_actions.get_element_info(element)
                    for element in elements
                ]
                for element_type, elements in interactive_elements.items()
            }
        }

        return True, page_info

    def _notify_progress(self, url: str):
        """Update visualization after processing a page."""
        self.visualizer.update_progress(self.graph, self.referrers, url)

    def _visit_url(self, url: str) -> bool:
        """Visit a URL with retry logic."""
        max_retries = 3
        current_try = 0
        
        while current_try < max_retries:
            try:
                start_time = time.time()
                logging.info(f"Visiting: {url} (Attempt {current_try + 1}/{max_retries})")
                
                # Load the page
                if not self._load_page(url):
                    raise TimeoutException("Page load failed")
                
                # Take full page screenshot
                screenshot_info = self._take_full_page_screenshot(url)
                if not screenshot_info:
                    raise Exception("Failed to take screenshot")
                    
                # Calculate processing time
                processing_time = time.time() - start_time
                logging.info(f"Page processed in {processing_time:.2f} seconds")
                
                # Log page visit
                self.visualizer.log_page_visit(
                    url=url,
                    title=self.driver.title,
                    screenshot_name=screenshot_info['name'],
                    dimensions=screenshot_info['dimensions'],
                    processing_time=processing_time
                )
                
                return True
                
            except TimeoutException:
                current_try += 1
                logging.warning(f"Timeout while visiting {url}, retrying ({current_try}/{max_retries})")
                if current_try == max_retries:
                    self.visualizer.log_error(url, f"Timeout after {max_retries} attempts")
                    return False
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error visiting {url}: {str(e)}")
                self.visualizer.log_error(url, str(e))
                return False

    def _load_page(self, url: str) -> bool:
        """Load the page and wait for it to be ready."""
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(5)
            
            # Wait for dynamic content to load
            self.driver.execute_script("return document.readyState") == "complete"
            logging.info(f"Page loaded: {url}")
            
            return True
        except Exception as e:
            logging.error(f"Error loading page {url}: {str(e)}")
            return False

    def _take_full_page_screenshot(self, url: str) -> dict:
        """
        Take multiple screenshots of the page by scrolling through sections.
        Creates a directory for each page visit and saves numbered screenshots.
        Returns dict with screenshot info or None if failed.
        """
        try:
            # Create timestamp and directories
            timestamp = timestamp_str()
            page_dir_name = f"{timestamp}_{clean_filename(url)[:50]}"
            screenshots_dir = os.path.join(self.screenshot_dir, page_dir_name)
            os.makedirs(screenshots_dir, exist_ok=True)
            logging.info(f"Created directory for screenshots: {screenshots_dir}")

            # Get page dimensions and prepare viewport info
            total_height = self.driver.execute_script(
                "return Math.max(document.documentElement.scrollHeight, "
                "document.body.scrollHeight);"
            )
            total_width = self.driver.execute_script(
                "return Math.max(document.documentElement.scrollWidth, "
                "document.body.scrollWidth);"
            )
            logging.info(f"Page dimensions: {total_width}x{total_height}")
            
            original_size = self.driver.get_window_size()
            viewport_info = {
                'viewport_height': original_size['height'],
                'viewport_width': original_size['width'],
                'total_height': total_height,
                'total_width': total_width
            }

            # Collect and save element data with viewport information
            elements_data = self.element_tracker.save_page_elements(
                self.dom_actions,
                page_dir_name,
                url,
                viewport_info
            )

            # Calculate number of screenshots needed
            num_sections = (total_height + original_size['height'] - 1) // original_size['height']
            screenshots = []

            # Set window size to capture full width
            self.driver.set_window_size(total_width, original_size['height'])
            logging.info(f"Set window size to {total_width}x{original_size['height']}")

            # Take screenshots of each section
            for i in range(num_sections):
                # Calculate scroll position
                scroll_top = i * original_size['height']
                
                # Scroll to position
                self.driver.execute_script(f"window.scrollTo(0, {scroll_top});")
                time.sleep(0.5)  # Wait for any dynamic content
                logging.info(f"Scrolled to position {scroll_top}")

                # Take screenshot of current viewport
                screenshot_name = f"section_{i + 1}.png"
                screenshot_path = os.path.join(screenshots_dir, screenshot_name)
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Saved screenshot: {screenshot_path}")
                
                screenshots.append({
                    'name': screenshot_name,
                    'path': screenshot_path,
                    'scroll_position': scroll_top,
                    'viewport_height': original_size['height']
                })

                # Save viewport information
                viewport_info = {
                    'scroll_top': scroll_top,
                    'viewport_height': original_size['height'],
                    'viewport_width': original_size['width'],
                    'section_number': i + 1
                }
                info_path = os.path.join(screenshots_dir, f"section_{i + 1}_info.json")
                with open(info_path, 'w') as f:
                    json.dump(viewport_info, f, indent=2)

            # Save overall page information
            page_info = {
                'total_height': total_height,
                'total_width': total_width,
                'viewport_height': original_size['height'],
                'viewport_width': original_size['width'],
                'num_sections': num_sections,
                'timestamp': timestamp,
                'url': url,
                'screenshots': screenshots
            }
            
            with open(os.path.join(screenshots_dir, 'page_info.json'), 'w') as f:
                json.dump(page_info, f, indent=2)
            # Add elements data to page_info safely
            if elements_data and isinstance(elements_data, dict):
                elements_config = f"configs/{page_dir_name}_elements.json"
                interactive_count = sum(
                    len(elements) for elements in elements_data.get('elements', {}).values()
                )
                accessibility_count = 0  # Since we haven't implemented accessibility elements yet
                
                page_info.update({
                    'elements_config': elements_config,
                    'interactive_elements_count': interactive_count,
                    'accessibility_elements_count': accessibility_count
                })

            return {
                'name': page_dir_name,
                'path': screenshots_dir,
                'dimensions': {
                    'width': total_width,
                    'height': total_height
                },
                'sections': num_sections,
                'screenshots': screenshots,
                'elements_data': elements_data if elements_data else {}
            }

        except Exception as e:
            logging.error(f"Screenshot failed: {str(e)}", exc_info=True)  # Added exc_info for better debugging
            # Attempt to restore window size
            try:
                self.driver.set_window_size(original_size['width'], original_size['height'])
            except Exception as restore_error:
                logging.warning(f"Failed to restore window size: {restore_error}")
            return None

    def _extract_links(self) -> list:
        """Extract all anchor hrefs from the current page."""
        links = []
        a_tags = self.driver.find_elements(By.TAG_NAME, "a")
        for a in a_tags:
            href = a.get_attribute("href")
            if href and href.startswith("http"):
                links.append(href)
        return links
