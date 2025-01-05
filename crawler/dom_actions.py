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

from .domain.elements import ElementLocation, InteractiveElement, ScreenshotSection

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

    def find_interactive_elements(self) -> Dict[str, List[InteractiveElement]]:
        """Find and return all interactive elements as InteractiveElement objects."""
        selectors = {
            # Basic form elements
            "buttons": """
                button,
                input[type='button'],
                input[type='submit'],
                input[type='reset'],
                [role='button'],
                [class*='btn'],
                [class*='button']
            """,
            
            # Links and navigation
            "links": """
                a[href]:not([href^='#']):not([href^='javascript']),
                [role='link']
            """,
            
            # Text inputs
            "text_inputs": """
                input[type='text'],
                input[type='email'],
                input[type='password'],
                input[type='search'],
                input[type='tel'],
                input[type='url'],
                input[type='number'],
                textarea,
                [contenteditable='true']
            """,
            
            # Selection inputs
            "select_inputs": """
                select,
                [role='listbox'],
                [role='combobox']
            """,
            
            # Checkboxes and radio buttons
            "toggles": """
                input[type='checkbox'],
                input[type='radio'],
                [role='checkbox'],
                [role='radio'],
                [role='switch']
            """,
            
            # Date and time inputs
            "datetime_inputs": """
                input[type='date'],
                input[type='datetime-local'],
                input[type='month'],
                input[type='time'],
                input[type='week']
            """,
            
            # Special inputs
            "special_inputs": """
                input[type='file'],
                input[type='color'],
                input[type='range'],
                [role='slider']
            """,
            
            # Interactive containers
            "containers": """
                details,
                dialog,
                [role='dialog'],
                [role='alertdialog'],
                [class*='modal'],
                [aria-modal='true']
            """,
            
            # Navigation elements
            "navigation": """
                [role='navigation'],
                [role='menu'],
                [role='menubar'],
                [role='menuitem'],
                [role='tab'],
                [role='tablist'],
                nav
            """,
            
            # Expandable content
            "expandable": """
                [aria-expanded],
                [data-toggle='collapse'],
                .accordion,
                .collapse,
                summary
            """,
            
            # Interactive media
            "media": """
                video[controls],
                audio[controls],
                [role='slider'],
                [role='progressbar']
            """,
            
            # Tooltips and popups
            "tooltips": """
                [title]:not(script):not(style),
                [data-tooltip],
                [aria-describedby],
                [role='tooltip']
            """,
            
            # Drag and drop
            "draggable": """
                [draggable='true'],
                [role='gridcell'],
                [aria-grabbed]
            """
        }
        
        interactive_elements = {}
        element_count = 0  # For generating unique IDs
        
        for element_type, selector in selectors.items():
            try:
                # Clean up selector by removing extra whitespace
                clean_selector = ' '.join(selector.split())
                elements = self.driver.find_elements(By.CSS_SELECTOR, clean_selector)
                
                # Filter out hidden elements
                visible_elements = []
                for element in elements:
                    if self.is_effectively_visible(element):
                        element_count += 1
                        
                        # Get element text, handling special cases
                        element_text = element.get_attribute('value') or element.text
                        if not element_text and element.tag_name in ['input', 'textarea']:
                            element_text = element.get_attribute('placeholder') or ''
                        
                        # Determine if element is an input field
                        is_input = (
                            element.tag_name in ['input', 'textarea', 'select'] or
                            element.get_attribute('contenteditable') == 'true'
                        )
                        
                        visible_elements.append(
                            InteractiveElement(
                                element_id=f"{element_type}_{element_count}",
                                element_type=element_type,
                                tag_name=element.tag_name,
                                text=element_text,
                                location=ElementLocation(
                                    x=element.location['x'],
                                    y=element.location['y'],
                                    width=element.size['width'],
                                    height=element.size['height']
                                ),
                                screenshot_section=ScreenshotSection(
                                    start_section=1,  # Will be updated by element_tracker
                                    end_section=1     # Will be updated by element_tracker
                                ),
                                attributes={
                                    attr: element.get_attribute(attr) 
                                    for attr in [
                                        'class', 'id', 'href', 'role', 'aria-label',
                                        'title', 'name', 'type', 'value', 'placeholder'
                                    ] 
                                    if element.get_attribute(attr)
                                },
                                is_enabled=element.is_enabled(),
                                is_displayed=element.is_displayed(),
                                has_input_field=is_input
                            )
                        )
                
                if visible_elements:  # Only add to dictionary if elements were found
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

    def find_element_by_id(self, element_id: str) -> Optional[WebElement]:
        """Find an element by its element_id from our tracking system."""
        try:
            # First try to find by our custom element_id in data-element-id attribute
            element = self.find_element(By.CSS_SELECTOR, f'[data-element-id="{element_id}"]')
            if element:
                return element
            
            # If not found, try to find by the original element attributes
            element_type, number = element_id.rsplit('_', 1)
            
            # Build a list of possible selectors based on element type
            selectors = []
            if element_type == "buttons":
                selectors = ["button", "input[type='button']", "input[type='submit']", "[role='button']"]
            elif element_type == "links":
                selectors = ["a", "[role='link']"]
            elif element_type == "text_inputs":
                selectors = ["input[type='text']", "input[type='email']", "textarea"]
            # Add more element type mappings as needed
            
            # Try each selector
            elements = []
            for selector in selectors:
                elements.extend(self.driver.find_elements(By.CSS_SELECTOR, selector))
            
            # Try to match the element by index
            index = int(number) - 1
            if 0 <= index < len(elements):
                return elements[index]
            
            return None
            
        except Exception as e:
            logging.warning(f"Failed to find element by ID {element_id}: {e}")
            return None

    def click_by_id(self, element_id: str) -> bool:
        """Click an element by its element_id."""
        element = self.find_element_by_id(element_id)
        if element:
            return self.click(element)
        return False

    def input_text_by_id(self, element_id: str, text: str) -> bool:
        """Input text into an element by its element_id."""
        element = self.find_element_by_id(element_id)
        if element:
            return self.input_text(element, text)
        return False

    def hover_by_id(self, element_id: str) -> bool:
        """Hover over an element by its element_id."""
        element = self.find_element_by_id(element_id)
        if element:
            return self.hover(element)
        return False

    def scroll_to_by_id(self, element_id: str) -> bool:
        """Scroll to an element by its element_id."""
        element = self.find_element_by_id(element_id)
        if element:
            return self.scroll_to(element)
        return False 