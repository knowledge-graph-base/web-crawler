import os
import json
import time
import logging
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from .utils import clean_filename, timestamp_str
from .dom_actions import DOMActions
from .repository.json_repository import JsonRepository


class ScreenshotHandler:
    def __init__(self, driver: WebDriver, base_dir: str):
        self.driver = driver
        self.screenshot_dir = os.path.join(base_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.dom_actions = DOMActions(driver)
        self.repository = JsonRepository(base_dir)
        
    def take_full_page_screenshot(self, url: str) -> dict:
        """
        Takes sectional screenshots of a page by scrolling through it.
        Returns a dictionary containing screenshot metadata and paths.
        """
        try:
            # Create timestamp and directories
            timestamp = timestamp_str()
            page_dir_name = f"{timestamp}_{clean_filename(url)[:50]}"
            screenshots_dir = os.path.join(self.screenshot_dir, page_dir_name)
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # First scroll through the page to ensure all content is loaded
            # This also helps with finding all interactive elements
            self._scroll_through_page()
            
            # Get page dimensions
            total_height = self.driver.execute_script(
                "return Math.max(document.documentElement.scrollHeight, "
                "document.body.scrollHeight);"
            )
            total_width = self.driver.execute_script(
                "return Math.max(document.documentElement.scrollWidth, "
                "document.body.scrollWidth);"
            )
            
            original_size = self.driver.get_window_size()
            viewport_info = {
                'viewport_height': original_size['height'],
                'viewport_width': original_size['width'],
                'total_height': total_height,
                'total_width': total_width
            }

            # Calculate number of screenshots needed
            num_sections = (total_height + original_size['height'] - 1) // original_size['height']
            screenshots = []

            # Set window size to capture full width
            self.driver.set_window_size(total_width, original_size['height'])

            # Get all interactive elements (first check repository)
            all_elements_dict = self.repository.get_elements(url)
            if not all_elements_dict:
                # If not in repository, find them and save
                all_elements_dict = self.dom_actions.find_interactive_elements()
                self.repository.save_elements(url, all_elements_dict)
            
            all_elements = self._convert_interactive_elements(all_elements_dict)

            # Take screenshots of each section and collect elements
            for i in range(num_sections):
                screenshot_info = self._take_section_screenshot(
                    i, screenshots_dir, original_size['height']
                )
                screenshots.append(screenshot_info)
                
                # Filter elements for current viewport
                viewport_elements = self._filter_viewport_elements(
                    all_elements, 
                    screenshot_info['scroll_position'], 
                    original_size['height']
                )
                
                # Save viewport information and elements for this section
                self._save_section_info(
                    screenshots_dir, i, original_size, screenshot_info['scroll_position'],
                    viewport_elements
                )

            # Save overall page information
            page_info = self._create_page_info(
                url, timestamp, total_height, total_width, 
                original_size, num_sections, screenshots,
                all_elements
            )
            
            self._save_page_info(screenshots_dir, page_info)

            # Restore window size
            self._restore_window_size(original_size)

            return {
                'name': page_dir_name,
                'path': screenshots_dir,
                'dimensions': {
                    'width': total_width,
                    'height': total_height
                },
                'sections': num_sections,
                'screenshots': screenshots,
                'interactive_elements': all_elements
            }

        except Exception as e:
            logging.error(f"Screenshot failed: {str(e)}", exc_info=True)
            self._restore_window_size(original_size)
            return None

    def _convert_interactive_elements(self, elements_dict: dict) -> list:
        """Convert InteractiveElement objects to serializable dictionaries."""
        all_elements = []
        for element_type, elements in elements_dict.items():
            for element in elements:
                try:
                    # Calculate element's top and bottom positions
                    element_top = element.location.y
                    element_bottom = element_top + element.location.height
                    
                    # Calculate which sections this element appears in
                    viewport_height = self.driver.get_window_size()['height']
                    start_section = max(1, int(element_top // viewport_height) + 1)
                    end_section = max(1, int(element_bottom // viewport_height) + 1)
                    
                    all_elements.append({
                        'element_id': element.element_id,
                        'element_type': element_type,
                        'tag_name': element.tag_name,
                        'text': element.text,
                        'location': {
                            'x': element.location.x,
                            'y': element.location.y,
                            'width': element.location.width,
                            'height': element.location.height
                        },
                        'attributes': element.attributes,
                        'is_enabled': element.is_enabled,
                        'is_displayed': element.is_displayed,
                        'has_input_field': element.has_input_field,
                        'screenshot_section': {
                            'start_section': start_section,
                            'end_section': end_section,
                            'spans_sections': start_section != end_section
                        }
                    })
                except Exception as e:
                    logging.warning(f"Failed to convert element: {e}")
                    continue
        return all_elements

    def _filter_viewport_elements(self, all_elements: list, scroll_top: int, viewport_height: int) -> list:
        """Filter elements that are visible in the current viewport."""
        viewport_elements = []
        for element in all_elements:
            element_top = element['location']['y']
            element_bottom = element_top + element['location']['height']
            
            # Check if element is visible in this viewport section
            if (scroll_top <= element_bottom and 
                element_top < scroll_top + viewport_height):
                viewport_elements.append(element)
        return viewport_elements

    def _save_section_info(self, screenshots_dir: str, section_num: int, 
                          window_size: dict, scroll_top: int, viewport_elements: list):
        """Saves metadata for a single section."""
        viewport_info = {
            'scroll_top': scroll_top,
            'viewport_height': window_size['height'],
            'viewport_width': window_size['width'],
            'section_number': section_num + 1,
            'interactive_elements': viewport_elements
        }
        info_path = os.path.join(screenshots_dir, f"section_{section_num + 1}_info.json")
        with open(info_path, 'w') as f:
            json.dump(viewport_info, f, indent=2)

    def _create_page_info(self, url: str, timestamp: str, total_height: int, 
                         total_width: int, window_size: dict, num_sections: int, 
                         screenshots: list, interactive_elements: list) -> dict:
        """Creates the overall page information dictionary."""
        return {
            'total_height': total_height,
            'total_width': total_width,
            'viewport_height': window_size['height'],
            'viewport_width': window_size['width'],
            'num_sections': num_sections,
            'timestamp': timestamp,
            'url': url,
            'screenshots': screenshots,
            'interactive_elements': interactive_elements
        }

    def _take_section_screenshot(self, section_num: int, screenshots_dir: str, viewport_height: int) -> dict:
        """Takes a screenshot of a single section of the page."""
        scroll_top = section_num * viewport_height
        
        # Scroll to position
        self.driver.execute_script(f"window.scrollTo(0, {scroll_top});")
        time.sleep(0.5)  # Wait for any dynamic content
        
        # Take screenshot
        screenshot_name = f"section_{section_num + 1}.png"
        screenshot_path = os.path.join(screenshots_dir, screenshot_name)
        self.driver.save_screenshot(screenshot_path)
        
        return {
            'name': screenshot_name,
            'path': screenshot_path,
            'scroll_position': scroll_top,
            'viewport_height': viewport_height
        }

    def _save_page_info(self, screenshots_dir: str, page_info: dict):
        """Saves the overall page information to a file."""
        with open(os.path.join(screenshots_dir, 'page_info.json'), 'w') as f:
            json.dump(page_info, f, indent=2)

    def _restore_window_size(self, original_size: dict):
        """Restores the window to its original size."""
        try:
            self.driver.set_window_size(original_size['width'], original_size['height'])
        except Exception as restore_error:
            logging.warning(f"Failed to restore window size: {restore_error}") 
            
    def _scroll_through_page(self) -> None:
        """Scroll through the entire page to load all dynamic content."""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                    
                last_height = new_height
                
            self.driver.execute_script("window.scrollTo(0, 0);")
            
        except Exception as e:
            logging.warning(f"Error during page scrolling: {e}")