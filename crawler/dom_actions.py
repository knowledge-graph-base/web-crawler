from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from typing import Optional, List, Dict, Any
import logging
import time

class DOMActions:
    def __init__(self, driver: WebDriver, timeout: int = 10):
        self.driver = driver
        self.timeout = timeout
        self.actions = ActionChains(driver)

    def find_element(self, by: By, selector: str) -> Optional[WebElement]:
        """Safely find an element with wait."""
        try:
            element = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            logging.info(f"Element found: {by}={selector}")
            return element
        except TimeoutException:
            logging.warning(f"Element not found: {by}={selector}")
            return None

    def click(self, element: WebElement) -> bool:
        """Safely click an element."""
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable(element)
            ).click()
            logging.info(f"Clicked element: {element}")
            return True
        except (TimeoutException, ElementNotInteractableException) as e:
            logging.warning(f"Could not click element: {e}")
            return False

    def scroll_to(self, element: WebElement) -> bool:
        """Scroll element into view."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            logging.info(f"Scrolled to element: {element}")
            return True
        except Exception as e:
            logging.warning(f"Could not scroll to element: {e}")
            return False

    def drag_and_drop(self, source: WebElement, target: WebElement) -> bool:
        """Perform drag and drop operation."""
        try:
            self.actions.drag_and_drop(source, target).perform()
            logging.info(f"Dragged {source} to {target}")
            return True
        except Exception as e:
            logging.warning(f"Could not perform drag and drop: {e}")
            return False

    def input_text(self, element: WebElement, text: str) -> bool:
        """Input text into an element."""
        try:
            element.clear()
            element.send_keys(text)
            logging.info(f"Input text into element: {element}")
            return True
        except Exception as e:
            logging.warning(f"Could not input text: {e}")
            return False

    def hover(self, element: WebElement) -> bool:
        """Hover over an element."""
        try:
            self.actions.move_to_element(element).perform()
            logging.info(f"Hovered over element: {element}")
            return True
        except Exception as e:
            logging.warning(f"Could not hover over element: {e}")
            return False

    def get_element_info(self, element: WebElement) -> Dict[str, Any]:
        """Get comprehensive information about an element."""
        try:
            info = {
                "tag_name": element.tag_name,
                "text": element.text,
                "is_displayed": element.is_displayed(),
                "is_enabled": element.is_enabled(),
                "attributes": {}
            }
            
            # Safely get location and size
            try:
                info["location"] = element.location
                info["size"] = element.size
            except Exception as e:
                logging.debug(f"Could not get location/size: {e}")
                info["location"] = {"x": 0, "y": 0}
                info["size"] = {"width": 0, "height": 0}

            # Safely get attributes
            for attr in ["class", "id", "href", "aria-label", "role"]:
                try:
                    value = element.get_attribute(attr)
                    if value:
                        info["attributes"][attr] = value
                except Exception:
                    continue

            return info
        except Exception as e:
            logging.warning(f"Could not get element info: {e}")
            return {
                "error": str(e),
                "location": {"x": 0, "y": 0},
                "size": {"width": 0, "height": 0}
            }

    def scroll_through_page(self) -> None:
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

    def find_interactive_elements(self) -> Dict[str, List[WebElement]]:
        """Find all potentially interactive elements on the page, including those requiring scroll."""
        # First scroll through the entire page to ensure all elements are loaded
        self.scroll_through_page()
        
        # Enhanced selectors for better coverage
        selectors = {
            "buttons": "button, input[type='button'], input[type='submit']",
            "links": "a",
            "inputs": "input[type='text'], input[type='password'], input[type='email'], input[type='number'], textarea",
            "selects": "select",
            "clickable": "[onclick], [role='button'], [role='link'], [role='tab'], [role='menuitem'], [class*='btn'], [class*='button']",
            "draggable": "[draggable='true']",
            "dropzones": "[droppable='true'], [data-droppable='true']",
            "checkboxes": "input[type='checkbox']",
            "radio_buttons": "input[type='radio']",
            "sliders": "input[type='range']",
            "file_inputs": "input[type='file']",
            "date_inputs": "input[type='date'], input[type='datetime-local']",
            "color_pickers": "input[type='color']",
            "iframes": "iframe",
            "tabs": "[role='tab']",
            "menus": "[role='menu'], [role='menubar']",
            "tooltips": "[title], [data-tooltip], [aria-describedby]",
            "modals": "[role='dialog'], [class*='modal']",
            "expandable": "[aria-expanded], [data-toggle], .accordion, .collapse"
        }
        
        interactive_elements = {}
        
        for element_type, selector in selectors.items():
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                # Filter out hidden elements that are truly not accessible
                visible_elements = [
                    elem for elem in elements 
                    if self.is_effectively_visible(elem)
                ]
                interactive_elements[element_type] = visible_elements
            except Exception as e:
                logging.warning(f"Error finding {element_type}: {e}")
                interactive_elements[element_type] = []
                
        return interactive_elements

    def is_effectively_visible(self, element: WebElement) -> bool:
        """
        Check if an element is effectively visible and potentially interactive.
        This goes beyond just checking is_displayed() as some elements might be 
        temporarily hidden but still important.
        """
        try:
            # Check if element is connected to DOM
            if not self.driver.execute_script("return arguments[0].isConnected", element):
                return False
            
            # Get element properties
            style = self.driver.execute_script("""
                let style = window.getComputedStyle(arguments[0]);
                return {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    height: style.height,
                    width: style.width,
                    position: style.position,
                    clip: style.clip
                };
            """, element)
            
            # Check various conditions that might make an element effectively invisible
            if (style['display'] == 'none' or 
                style['visibility'] == 'hidden' or 
                style['opacity'] == '0' or 
                (style['height'] == '0px' and style['width'] == '0px')):
                return False
            
            # Special check for elements that might be clipped or positioned off-screen
            if style['position'] in ['fixed', 'absolute']:
                rect = element.rect
                viewport_height = self.driver.execute_script("return window.innerHeight")
                viewport_width = self.driver.execute_script("return window.innerWidth")
                
                # Check if element is positioned outside viewport
                if (rect['x'] < -rect['width'] or 
                    rect['y'] < -rect['height'] or 
                    rect['x'] > viewport_width or 
                    rect['y'] > viewport_height):
                    return False
            
            return True
            
        except Exception as e:
            logging.warning(f"Error checking visibility: {e}")
            return False 