from abc import ABC, abstractmethod
from typing import Optional
from ..domain.graph import CrawlGraph
from ..domain.page import Page

class BaseRepository(ABC):
    @abstractmethod
    def save_graph(self, graph: CrawlGraph) -> bool:
        pass
    
    @abstractmethod
    def load_graph(self, start_url: str) -> Optional[CrawlGraph]:
        pass
    
    @abstractmethod
    def save_page(self, page: Page) -> bool:
        pass
    
    @abstractmethod
    def load_page(self, page_id: str) -> Optional[Page]:
        pass 