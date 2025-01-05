from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from typing import Dict, List, Callable
import time

class InteractionHandler:
    def __init__(self, driver: WebDriver, decision_callback: Callable):
        self.driver = driver
        self.decision_callback = decision_callback

    def detect_interactive_elements(self) -> Dict[str, List[WebElement]]:
        """Detect forms, buttons and other interactive elements on the page."""
        interactive_elements = {
            'forms': self.driver.find_elements(By.TAG_NAME, 'form'),
            'buttons': self.driver.find_elements(By.TAG_NAME, 'button'),
            'inputs': self.driver.find_elements(By.TAG_NAME, 'input')
        }
        
        return {k: v for k, v in interactive_elements.items() if v}

    def handle_form(self, form: WebElement):
        """Handle form interaction based on user input."""
        inputs = form.find_elements(By.TAG_NAME, 'input')
        for input_field in inputs:
            input_type = input_field.get_attribute('type')
            if input_type in ['text', 'email', 'password']:
                placeholder = input_field.get_attribute('placeholder') or input_field.get_attribute('name')
                value = self.decision_callback(f"Enter value for {placeholder}: ")
                if value.lower() != 'skip':
                    input_field.send_keys(value)

    def handle_clickable(self, element: WebElement):
        """Handle clickable element interaction."""
        element_text = element.text or element.get_attribute('value') or element.get_attribute('name')
        decision = self.decision_callback(f"Click on '{element_text}'?")
        if decision.lower() == 'yes':
            try:
                element.click()
                time.sleep(1)
            except Exception as e:
                print(f"Failed to click element: {str(e)}") 