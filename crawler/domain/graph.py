from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from .page import Page
from .decisions import ActionType, ActionDecision, ClickAction, HoverAction, InputAction, NavigateAction, ScrollAction

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
    def from_decision(cls, action_id: str, decision: ActionDecision, duration: float, success: bool) -> 'Action':
        """Create an Action from an ActionDecision"""
        common_args = {
            'action_id': action_id,
            'timestamp': datetime.now(),
            'duration': duration,
            'success': success
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
    state_id: str
    page_id: str
    timestamp: datetime
    form_values: Dict[str, str]
    scroll_position: int
    action_history: List[Action] = field(default_factory=list)
    dom_changes: Dict[str, str] = field(default_factory=dict)  # Track DOM changes
    
    def to_dict(self) -> Dict:
        return {
            'state_id': self.state_id,
            'page_id': self.page_id,
            'timestamp': self.timestamp.isoformat(),
            'form_values': self.form_values,
            'scroll_position': self.scroll_position,
            'action_history': [action.to_dict() for action in self.action_history],
            'dom_changes': self.dom_changes
        }
    
    def add_action(self, action: Action):
        self.action_history.append(action)
    
    def get_last_action(self) -> Optional[Action]:
        return self.action_history[-1] if self.action_history else None

@dataclass
class Edge:
    source_state_id: str
    target_state_id: str
    action: Action
    weight: float
    transition_time: float  # Time taken for state transition
    
    def to_dict(self) -> Dict:
        return {
            'source_state_id': self.source_state_id,
            'target_state_id': self.target_state_id,
            'action': self.action.to_dict(),
            'weight': self.weight,
            'transition_time': self.transition_time
        }

@dataclass
class CrawlGraph:
    start_url: str
    pages: Dict[str, Page]  # page_id -> Page
    states: Dict[str, PageState]  # state_id -> PageState
    edges: List[Edge]
    timestamp: datetime = field(default_factory=datetime.now)
    visited_states: Set[str] = field(default_factory=set)
    
    def add_page(self, page: Page):
        """Add a new page to the graph"""
        self.pages[page.page_id] = page
    
    def add_state(self, state: PageState):
        """Add a new state to the graph"""
        self.states[state.state_id] = state
        self.visited_states.add(state.state_id)
    
    def add_edge(self, edge: Edge):
        """Add a new edge to the graph"""
        self.edges.append(edge)
    
    def get_state_transitions(self, state_id: str) -> List[Edge]:
        """Get all transitions from a given state"""
        return [edge for edge in self.edges if edge.source_state_id == state_id]
    
    def get_page_states(self, page_id: str) -> List[PageState]:
        """Get all states for a given page"""
        return [state for state in self.states.values() if state.page_id == page_id]
    
    def to_dict(self) -> Dict:
        return {
            'start_url': self.start_url,
            'pages': {pid: page.to_dict() for pid, page in self.pages.items()},
            'states': {sid: state.to_dict() for sid, state in self.states.items()},
            'edges': [edge.to_dict() for edge in self.edges],
            'timestamp': self.timestamp.isoformat(),
            'visited_states': list(self.visited_states)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CrawlGraph':
        """Create a CrawlGraph from a dictionary"""
        pages = {pid: Page.from_dict(pdata) for pid, pdata in data['pages'].items()}
        states = {sid: PageState.from_dict(sdata) for sid, sdata in data['states'].items()}
        edges = [Edge.from_dict(edata) for edata in data['edges']]
        
        return cls(
            start_url=data['start_url'],
            pages=pages,
            states=states,
            edges=edges,
            timestamp=datetime.fromisoformat(data['timestamp']),
            visited_states=set(data['visited_states'])
        ) 