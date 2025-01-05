from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
import time
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict

from .visualization_handler import CrawlVisualizer
from .utils import clean_filename, timestamp_str
from .dom_actions import DOMActions
from selenium.webdriver.common.by import By
from .element_tracker import ElementTracker
from .screenshot_handler import ScreenshotHandler
from .domain.graph import CrawlGraph, Edge, Action, PageState
from .domain.page import Page, PageMetadata
from .domain.actions import ActionDecision, ClickAction, HoverAction, InputAction, NavigateAction, ScrollAction  
from .repository.json_repository import JsonRepository
from .decision_maker.base_decision_maker import BaseDecisionMaker

class InteractiveCrawler:
    def __init__(self, driver: WebDriver, decision_maker: BaseDecisionMaker):
        """
        Initialize the interactive crawler.
        
        Args:
            driver: Selenium WebDriver instance
            decision_maker: Decision maker instance to guide the crawling
        """
        self.driver = driver
        self.decision_maker = decision_maker
        
        # Initialize handlers and utilities
        base_dir = os.path.join(os.path.dirname(__file__), "..")
        self.repository = JsonRepository(base_dir)
        self.log_file = os.path.join(base_dir, "crawl_log.md")
        
        self.visualizer = CrawlVisualizer(self.log_file)
        self.dom_actions = DOMActions(driver)
        self.element_tracker = ElementTracker(base_dir)
        self.screenshot_handler = ScreenshotHandler(driver, base_dir)
        
        logging.basicConfig(level=logging.INFO)

    def crawl(self, start_url: str) -> CrawlGraph:
        """
        Start crawling from the given URL using decision maker for navigation.
        
        Args:
            start_url: The URL to start crawling from
            
        Returns:
            CrawlGraph: The graph representing the crawled pages and their relationships
        """
        graph = CrawlGraph(start_url=start_url, pages={}, states={}, edges=[])
        current_state = None
        
        # Start with the initial URL
        success, page = self._process_page(start_url)
        if not success:
            return graph

        # Add initial page to graph
        graph.add_page(page)
        self.repository.save_page(page)
        current_state = self._create_page_state(page)
        graph.add_state(current_state)  # Add initial state to graph

        # Main interaction loop
        while True:
            # Get next action from decision maker
            action = self.decision_maker.decide_next_action(current_state)
            if not action:
                break

            # Execute action and get new state
            success, new_state, action_result = self._execute_action(action)
            if success and new_state:
                # Add new state to graph
                graph.add_state(new_state)
                
                # Create edge for the action
                edge = Edge(
                    source_state_id=current_state.state_id,
                    target_state_id=new_state.state_id,
                    action=action_result,
                    weight=1.0,
                    transition_time=action_result.duration
                )
                graph.add_edge(edge)
                
                # Update current state
                current_state = new_state

            # Check if we should continue exploration
            if not self.decision_maker.should_continue_exploration(current_state):
                break

        # Save final graph state
        self.repository.save_graph(graph)
        return graph

    def _process_page(self, url: str) -> tuple[bool, Optional[Page]]:
        """
        Process a single page during crawling.
        
        Args:
            url: The URL to process
            
        Returns:
            tuple[bool, Optional[Page]]: Success status and the processed Page object if successful
        """
        start_time = time.time()
        
        try:
            # Load the page
            if not self._visit_url(url):
                return False, None

            # Take screenshots
            screenshot_info = self.screenshot_handler.take_full_page_screenshot(url)
            if not screenshot_info:
                return False, None

            # Get interactive elements
            interactive_elements = self._get_interactive_elements()
            
            # Calculate load time
            load_time = time.time() - start_time

            # Create page metadata
            metadata = PageMetadata(
                url=url,
                title=self.driver.title,
                timestamp=datetime.now(),
                total_height=screenshot_info['dimensions']['height'],
                total_width=screenshot_info['dimensions']['width'],
                load_time=load_time,
                viewport_height=self.driver.get_window_size()['height'],
                viewport_width=self.driver.get_window_size()['width']
            )

            # Create page object
            page = Page(
                page_id=f"page_{clean_filename(url)}",
                metadata=metadata,
                screenshots=screenshot_info['screenshots'],
                interactive_elements=interactive_elements
            )

            # Log page visit
            self.visualizer.log_page_visit(
                url=url,
                title=self.driver.title,
                screenshot_name=screenshot_info['name'],
                dimensions=screenshot_info['dimensions'],
                processing_time=load_time
            )

            return True, page

        except Exception as e:
            logging.error(f"Failed to process page {url}: {str(e)}")
            return False, None

    def _execute_action(self, action: ActionDecision) -> tuple[bool, Optional[PageState], Optional[Action]]:
        """
        Execute an action and return the new state.
        
        Args:
            action: The action to execute
            
        Returns:
            tuple[bool, Optional[PageState], Optional[Action]]: Success status, new state if successful, and action result
        """
        start_time = time.time()
        try:
            # Execute the action using DOM Actions
            action_success = False
            if isinstance(action, ClickAction):
                action_success = self.dom_actions.click_by_id(action.element_id)
            elif isinstance(action, InputAction):
                action_success = self.dom_actions.input_text_by_id(action.element_id, action.input_value)
            elif isinstance(action, HoverAction):
                action_success = self.dom_actions.hover_by_id(action.element_id)
            elif isinstance(action, ScrollAction):
                if action.element_id:
                    action_success = self.dom_actions.scroll_to_by_id(action.element_id)
                else:
                    self.driver.execute_script(f"window.scrollTo(0, {action.position});")
                    action_success = True
            elif isinstance(action, NavigateAction):
                self.driver.get(action.url)
                action_success = True

            if not action_success:
                logging.error(f"Failed to execute action: {action}")
                return False, None, None

            # Process the new page state
            success, page = self._process_page(self.driver.current_url)
            if not success:
                return False, None, None

            # Create action result
            duration = time.time() - start_time
            action_result = Action.from_decision(
                action_id=f"action_{timestamp_str()}",
                decision=action,
                duration=duration,
                success=True
            )

            # Create new state
            new_state = self._create_page_state(page)
            return True, new_state, action_result

        except Exception as e:
            logging.error(f"Failed to execute action: {e}")
            return False, None, None

    def _create_page_state(self, page: Page) -> PageState:
        """
        Create a PageState object from a Page object.
        
        Args:
            page: The Page object to convert
            
        Returns:
            PageState: The current state of the page
        """
        scroll_position = self.driver.execute_script("return window.pageYOffset")
        
        # Get form values
        form_values = {}
        input_elements = self.driver.find_elements(By.TAG_NAME, 'input')
        for element in input_elements:
            element_id = element.get_attribute('id')
            if element_id:
                form_values[element_id] = element.get_attribute('value') or ''

        # Create a unique state ID
        state_id = f"state_{timestamp_str()}"

        return PageState(
            state_id=state_id,
            page_id=page.page_id,
            url=page.metadata.url,
            timestamp=datetime.now(),
            screenshot_paths=[s['path'] for s in page.screenshots],
            interactive_elements=[
                {
                    'element_id': e.element_id,
                    'element_type': e.element_type,
                    'text': e.text,
                    'has_input_field': e.has_input_field
                }
                for e in page.interactive_elements
            ],
            current_scroll_position=scroll_position,
            form_values=form_values,
            page_title=page.metadata.title
        )

    def _visit_url(self, url: str) -> bool:
        """
        Visit a URL with retry logic.
        
        Args:
            url: The URL to visit
            
        Returns:
            bool: True if successful, False otherwise
        """
        max_retries = 3
        current_try = 0
        
        while current_try < max_retries:
            try:
                logging.info(f"Visiting: {url} (Attempt {current_try + 1}/{max_retries})")
                return self._load_page(url)
                
            except TimeoutException:
                current_try += 1
                logging.warning(f"Timeout while visiting {url}, retrying ({current_try}/{max_retries})")
                if current_try == max_retries:
                    self.visualizer.log_error(url, f"Timeout after {max_retries} attempts")
                    return False
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error visiting {url}: {str(e)}")
                self.visualizer.log_error(url, str(e))
                return False

    def _load_page(self, url: str) -> bool:
        """
        Load the page and wait for it to be ready.
        
        Args:
            url: The URL to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(5)
            self.driver.execute_script("return document.readyState") == "complete"
            logging.info(f"Page loaded: {url}")
            return True
        except Exception as e:
            logging.error(f"Error loading page {url}: {str(e)}")
            return False

    def _get_interactive_elements(self) -> List:
        """Get all interactive elements from the current page."""
        interactive_elements_dict = self.dom_actions.find_interactive_elements()
        return [
            element
            for element_list in interactive_elements_dict.values()
            for element in element_list
        ]