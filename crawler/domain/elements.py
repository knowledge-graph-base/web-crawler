from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime

@dataclass
class ElementLocation:
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        return self.width * self.height

@dataclass
class ScreenshotSection:
    start_section: int
    end_section: int
    spans_sections: bool = False

@dataclass
class InteractiveElement:
    element_id: str  # Unique identifier
    element_type: str  # button, link, input, etc.
    tag_name: str
    text: str
    location: ElementLocation
    screenshot_section: ScreenshotSection
    attributes: Dict[str, str] = field(default_factory=dict)
    is_enabled: bool = True
    is_displayed: bool = True
    has_input_field: bool = False
    parent_form_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'element_id': self.element_id,
            'element_type': self.element_type,
            'tag_name': self.tag_name,
            'text': self.text,
            'location': {
                'x': self.location.x,
                'y': self.location.y,
                'width': self.location.width,
                'height': self.location.height
            },
            'screenshot_section': {
                'start_section': self.screenshot_section.start_section,
                'end_section': self.screenshot_section.end_section,
                'spans_sections': self.screenshot_section.spans_sections
            },
            'attributes': self.attributes,
            'is_enabled': self.is_enabled,
            'is_displayed': self.is_displayed,
            'has_input_field': self.has_input_field,
            'parent_form_id': self.parent_form_id,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InteractiveElement':
        location = ElementLocation(**data['location'])
        screenshot_section = ScreenshotSection(**data['screenshot_section'])
        return cls(
            element_id=data['element_id'],
            element_type=data['element_type'],
            tag_name=data['tag_name'],
            text=data['text'],
            location=location,
            screenshot_section=screenshot_section,
            attributes=data['attributes'],
            is_enabled=data['is_enabled'],
            is_displayed=data['is_displayed'],
            has_input_field=data['has_input_field'],
            parent_form_id=data['parent_form_id'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        ) 