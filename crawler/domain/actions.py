from dataclasses import dataclass, field
from typing import Dict, Optional, Union, List
from datetime import datetime
from enum import Enum

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
class Action:
    action_id: str
    action_type: ActionType
    element_id: str
    timestamp: datetime
    duration: float
    success: bool
    input_value: Optional[str] = None  # For input actions
    scroll_position: Optional[int] = None  # For scroll actions
    url: Optional[str] = None  # For navigate actions
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'element_id': self.element_id,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration,
            'success': self.success,
            'input_value': self.input_value,
            'scroll_position': self.scroll_position,
            'url': self.url,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Action':
        """Create an Action from a dictionary"""
        return cls(
            action_id=data['action_id'],
            action_type=ActionType(data['action_type']),
            element_id=data['element_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            duration=data['duration'],
            success=data['success'],
            input_value=data.get('input_value'),
            scroll_position=data.get('scroll_position'),
            url=data.get('url'),
            error_message=data.get('error_message')
        )
    
    @classmethod
    def from_decision(cls, action_id: str, decision: ActionDecision, duration: float, success: bool) -> 'Action':
        """Create an Action from an ActionDecision"""
        common_args = {
            'action_id': action_id,
            'timestamp': datetime.now(),
            'duration': duration,
            'success': success,
            'element_id': ''  # Default empty string
        }
        
        if isinstance(decision, InputAction):
            return cls(
                action_type=ActionType.INPUT,
                element_id=decision.element_id,
                input_value=decision.input_value,
                **common_args
            )
        elif isinstance(decision, ClickAction):
            return cls(
                action_type=ActionType.CLICK,
                element_id=decision.element_id,
                **common_args
            )
        elif isinstance(decision, HoverAction):
            return cls(
                action_type=ActionType.HOVER,
                element_id=decision.element_id,
                **common_args
            )
        elif isinstance(decision, ScrollAction):
            return cls(
                action_type=ActionType.SCROLL,
                scroll_position=decision.position,
                **common_args
            )
        elif isinstance(decision, NavigateAction):
            return cls(
                action_type=ActionType.NAVIGATE,
                url=decision.url,
                **common_args
            )
        else:
            raise ValueError(f"Unsupported action decision type: {type(decision)}") 

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
    form_values: Dict[str, str]  # Current values in form fields
    page_title: str
    action_history: List[Action] = field(default_factory=list)
    dom_changes: Dict[str, str] = field(default_factory=dict)  # Track DOM changes

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

    def add_action(self, action: Action):
        self.action_history.append(action)
    
    def get_last_action(self) -> Optional[Action]:
        return self.action_history[-1] if self.action_history else None 