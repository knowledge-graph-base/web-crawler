from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from .elements import InteractiveElement

@dataclass
class Screenshot:
    screenshot_id: str
    path: str
    section_number: int
    viewport_height: int
    viewport_width: int
    scroll_position: int

@dataclass
class PageMetadata:
    url: str
    title: str
    timestamp: datetime
    total_height: int
    total_width: int
    load_time: float
    viewport_height: int
    viewport_width: int

@dataclass
class Page:
    page_id: str
    metadata: PageMetadata
    screenshots: List[Screenshot]
    interactive_elements: List[InteractiveElement]
    html_snapshot: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'page_id': self.page_id,
            'metadata': {
                'url': self.metadata.url,
                'title': self.metadata.title,
                'timestamp': self.metadata.timestamp.isoformat(),
                'total_height': self.metadata.total_height,
                'total_width': self.metadata.total_width,
                'load_time': self.metadata.load_time,
                'viewport_height': self.metadata.viewport_height,
                'viewport_width': self.metadata.viewport_width
            },
            'screenshots': [
                {
                    'screenshot_id': s.screenshot_id,
                    'path': s.path,
                    'section_number': s.section_number,
                    'viewport_height': s.viewport_height,
                    'viewport_width': s.viewport_width,
                    'scroll_position': s.scroll_position
                }
                for s in self.screenshots
            ],
            'interactive_elements': [
                element.to_dict() for element in self.interactive_elements
            ],
            'html_snapshot': self.html_snapshot
        } 