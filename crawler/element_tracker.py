from typing import Dict, List, Any
import json
import os
from selenium.webdriver.remote.webelement import WebElement
import logging

class ElementTracker:
    def __init__(self, base_dir: str):
        """Initialize the element tracker."""
        self.config_dir = os.path.join(base_dir, "configs")
        os.makedirs(self.config_dir, exist_ok=True)

    def save_page_elements(self, dom_actions, page_timestamp: str, url: str, 
                         viewport_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Save comprehensive data about page elements to a config file.
        Uses DOMActions to get element information.
        """
        try:
            # Get all elements using DOMActions
            interactive_elements = dom_actions.find_interactive_elements()
            
            # Process and structure the elements data
            elements_data = {
                'url': url,
                'timestamp': page_timestamp,
                'viewport_info': viewport_info or {},
                'elements': {}
            }

            # Process each type of element
            for element_type, elements in interactive_elements.items():
                try:
                    elements_data['elements'][element_type] = [
                        self._process_element_data(element, dom_actions)
                        for element in elements
                    ]
                except Exception as e:
                    logging.warning(f"Error processing {element_type} elements: {str(e)}")
                    elements_data['elements'][element_type] = []

            # Add section information
            if viewport_info and 'viewport_height' in viewport_info:
                self._add_section_information(elements_data, viewport_info['viewport_height'])

            # Save to config file
            config_path = os.path.join(self.config_dir, f"{page_timestamp}_elements.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(elements_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved elements configuration to {config_path}")

            return elements_data

        except Exception as e:
            logging.warning(f"Error saving page elements: {str(e)}")
            return {
                'url': url,
                'timestamp': page_timestamp,
                'viewport_info': viewport_info or {},
                'elements': {},
                'error': str(e)
            }

    def _process_element_data(self, element: WebElement, dom_actions) -> Dict[str, Any]:
        """Process element data and add additional useful information."""
        try:
            # Get base element info from DOMActions
            element_info = dom_actions.get_element_info(element)
            
            # Add additional computed information
            location = element_info.get('location', {})
            size = element_info.get('size', {})
            
            if location and size and all(key in location for key in ['x', 'y']) and all(key in size for key in ['width', 'height']):
                # Convert location to include top/bottom/left/right
                element_info['location'] = {
                    'top': location['y'],
                    'left': location['x'],
                    'bottom': location['y'] + size['height'],
                    'right': location['x'] + size['width'],
                    'x': location['x'],
                    'y': location['y']
                }
                
                element_info['computed'] = {
                    'center_point': {
                        'x': location['x'] + size['width'] / 2,
                        'y': location['y'] + size['height'] / 2
                    },
                    'clickable_area': size['width'] * size['height'],
                    'aspect_ratio': size['width'] / size['height'] if size['height'] != 0 else None
                }

            
            return element_info
        except Exception as e:
            logging.warning(f"Error processing element data: {str(e)}")
            return {
                'error': str(e),
                'location': {'top': 0, 'left': 0, 'bottom': 0, 'right': 0},
                'size': {'width': 0, 'height': 0}
            }

    def _add_section_information(self, elements_data: Dict, viewport_height: int):
        """Add information about which screenshot section contains each element."""
        try:
            for element_type, elements in elements_data.get('elements', {}).items():
                for element in elements:
                    location = element.get('location', {})
                    if location:
                        element_top = location.get('top', 0)
                        element_bottom = location.get('bottom', 0)
                        
                        # Calculate which sections this element appears in
                        start_section = max(1, int(element_top // viewport_height + 1))
                        end_section = max(1, int(element_bottom // viewport_height + 1))
                        
                        element['screenshot_sections'] = {
                            'start_section': start_section,
                            'end_section': end_section,
                            'spans_sections': start_section != end_section
                        }
            logging.info("Added section information to elements")
        except Exception as e:
            logging.warning(f"Error adding section information: {e}")

    def get_elements_in_section(self, elements_data: Dict, section_number: int) -> Dict[str, List]:
        """
        Get all elements that appear in a specific screenshot section.
        Useful for mapping elements to specific screenshots.
        """
        section_elements = {}
        
        for element_type, elements in elements_data['elements'].items():
            section_elements[element_type] = [
                element for element in elements
                if ('screenshot_sections' in element and
                    element['screenshot_sections']['start_section'] <= section_number <= 
                    element['screenshot_sections']['end_section'])
            ]
            
        return section_elements 