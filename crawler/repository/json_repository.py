import json
import logging
import os
from typing import Optional, Dict, List

from crawler.utils import clean_filename
from .base_repository import BaseRepository
from ..domain.graph import CrawlGraph
from ..domain.page import Page
from ..domain.elements import InteractiveElement

class JsonRepository(BaseRepository):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.pages_dir = os.path.join(base_dir, "pages")
        self.graphs_dir = os.path.join(base_dir, "graphs")
        self.elements_dir = os.path.join(base_dir, "elements")
        
        # Create necessary directories
        os.makedirs(self.pages_dir, exist_ok=True)
        os.makedirs(self.graphs_dir, exist_ok=True)
        os.makedirs(self.elements_dir, exist_ok=True)
        
        # In-memory cache for elements
        self._elements_cache = {}

    def save_page(self, page: Page) -> bool:
        try:
            filename = f"page_{page.page_id}.json"
            path = os.path.join(self.pages_dir, filename)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(page.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save page: {e}")
            return False

    def load_page(self, page_id: str) -> Optional[Page]:
        try:
            filename = f"page_{page_id}.json"
            path = os.path.join(self.pages_dir, filename)
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Page.from_dict(data)
        except Exception as e:
            logging.error(f"Failed to load page: {e}")
            return None

    def save_graph(self, graph: CrawlGraph) -> bool:
        try:
            filename = f"graph_{clean_filename(graph.start_url)}_{graph.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            path = os.path.join(self.graphs_dir, filename)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(graph.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save graph: {e}")
            return False

    def load_graph(self, start_url: str) -> Optional[CrawlGraph]:
        try:
            filename = f"graph_{clean_filename(start_url)}.json"
            path = os.path.join(self.graphs_dir, filename)
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CrawlGraph.from_dict(data)
        except Exception as e:
            logging.error(f"Failed to load graph: {e}")
            return None

    def save_elements(self, url: str, elements_dict: Dict[str, List[InteractiveElement]]) -> bool:
        """Save interactive elements for a URL."""
        try:
            filename = f"elements_{clean_filename(url)}.json"
            path = os.path.join(self.elements_dir, filename)
            
            # Convert elements to serializable format
            serializable_elements = {
                element_type: [self._element_to_dict(e) for e in elements]
                for element_type, elements in elements_dict.items()
            }
            
            # Save to cache
            self._elements_cache[url] = elements_dict
            
            # Save to file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(serializable_elements, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save elements: {e}")
            return False

    def get_elements(self, url: str) -> Optional[Dict[str, List[InteractiveElement]]]:
        """Get interactive elements for a URL, first from cache then from file."""
        try:
            # Check cache first
            if url in self._elements_cache:
                return self._elements_cache[url]
            
            # If not in cache, try to load from file
            filename = f"elements_{clean_filename(url)}.json"
            path = os.path.join(self.elements_dir, filename)
            
            if not os.path.exists(path):
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                elements_dict = {
                    element_type: [self._dict_to_element(e) for e in elements]
                    for element_type, elements in data.items()
                }
                
                # Update cache
                self._elements_cache[url] = elements_dict
                return elements_dict
        except Exception as e:
            logging.error(f"Failed to load elements: {e}")
            return None

    def _element_to_dict(self, element: InteractiveElement) -> dict:
        """Convert InteractiveElement to dictionary."""
        return {
            'element_id': element.element_id,
            'element_type': element.element_type,
            'tag_name': element.tag_name,
            'text': element.text,
            'location': {
                'x': element.location.x,
                'y': element.location.y,
                'width': element.location.width,
                'height': element.location.height
            },
            'screenshot_section': {
                'start_section': element.screenshot_section.start_section,
                'end_section': element.screenshot_section.end_section,
                'spans_sections': element.screenshot_section.spans_sections
            },
            'attributes': element.attributes,
            'is_enabled': element.is_enabled,
            'is_displayed': element.is_displayed,
            'has_input_field': element.has_input_field,
            'parent_form_id': element.parent_form_id,
            'timestamp': element.timestamp.isoformat()
        }

    def _dict_to_element(self, data: dict) -> InteractiveElement:
        """Convert dictionary to InteractiveElement."""
        from ..domain.elements import ElementLocation, ScreenshotSection
        from datetime import datetime
        
        return InteractiveElement(
            element_id=data['element_id'],
            element_type=data['element_type'],
            tag_name=data['tag_name'],
            text=data['text'],
            location=ElementLocation(
                x=data['location']['x'],
                y=data['location']['y'],
                width=data['location']['width'],
                height=data['location']['height']
            ),
            screenshot_section=ScreenshotSection(
                start_section=data['screenshot_section']['start_section'],
                end_section=data['screenshot_section']['end_section'],
                spans_sections=data['screenshot_section']['spans_sections']
            ),
            attributes=data['attributes'],
            is_enabled=data['is_enabled'],
            is_displayed=data['is_displayed'],
            has_input_field=data['has_input_field'],
            parent_form_id=data.get('parent_form_id'),
            timestamp=datetime.fromisoformat(data['timestamp'])
        ) 