from abc import ABC, abstractmethod
from typing import Optional
from ..domain.actions import ActionDecision, PageState

class BaseDecisionMaker(ABC):
    @abstractmethod
    def decide_next_action(self, state: PageState) -> Optional[ActionDecision]:
        """Decide what action to take next based on the current page state"""
        pass

    @abstractmethod
    def should_continue_exploration(self, state: PageState) -> bool:
        """Decide whether to continue exploring from the current state"""
        pass 