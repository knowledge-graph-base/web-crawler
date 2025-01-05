from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict
from enum import Enum
from datetime import datetime

from crawler.domain.graph import Action

class ActionType(Enum):
    CLICK = "click"
    INPUT = "input"
    HOVER = "hover"
    SCROLL = "scroll"
    NAVIGATE = "navigate"

@dataclass
class InputAction:
    element_id: str
    input_value: str

@dataclass
class ClickAction:
    element_id: str

@dataclass
class HoverAction:
    element_id: str

@dataclass
class ScrollAction:
    position: int  # Scroll position in pixels

@dataclass
class NavigateAction:
    url: str

ActionDecision = Union[InputAction, ClickAction, HoverAction, ScrollAction, NavigateAction]

@dataclass
class PageState:
    """Represents the current state of the page"""
    state_id: str
    page_id: str
    url: str
    timestamp: datetime
    screenshot_paths: List[str]
    interactive_elements: List[dict]  # List of InteractiveElement as dict
    current_scroll_position: int
    form_values: dict  # Current values in form fields
    page_title: str
    action_history: List['Action'] = field(default_factory=list)
    dom_changes: dict = field(default_factory=dict)  # Track DOM changes

    def to_dict(self) -> Dict:
        return {
            'state_id': self.state_id,
            'page_id': self.page_id,
            'url': self.url,
            'timestamp': self.timestamp.isoformat(),
            'screenshot_paths': self.screenshot_paths,
            'interactive_elements': self.interactive_elements,
            'current_scroll_position': self.current_scroll_position,
            'form_values': self.form_values,
            'page_title': self.page_title,
            'action_history': [action.to_dict() for action in self.action_history],
            'dom_changes': self.dom_changes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PageState':
        return cls(
            state_id=data['state_id'],
            page_id=data['page_id'],
            url=data['url'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            screenshot_paths=data['screenshot_paths'],
            interactive_elements=data['interactive_elements'],
            current_scroll_position=data['current_scroll_position'],
            form_values=data['form_values'],
            page_title=data['page_title'],
            action_history=[Action.from_dict(a) for a in data['action_history']],
            dom_changes=data['dom_changes']
        ) 