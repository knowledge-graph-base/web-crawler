from typing import List, Optional
from .base_decision_maker import BaseDecisionMaker
from ..domain.actions import ActionDecision, InputAction, ClickAction, HoverAction, ScrollAction, NavigateAction, PageState

class HumanDecisionMaker(BaseDecisionMaker):
    def decide_next_action(self, state: PageState) -> Optional[ActionDecision]:
        print("\n=== Current Page State ===")
        print(f"URL: {state.url}")
        print(f"Title: {state.page_title}")
        print("\nInteractive Elements:")
        
        for i, element in enumerate(state.interactive_elements):
            print(f"\n{i + 1}. Type: {element['element_type']}")
            print(f"   ID: {element['element_id']}")
            print(f"   Text: {element['text']}")
            if element.get('has_input_field'):
                print(f"   Current Value: {state.form_values.get(element['element_id'], '')}")

        print("\nAvailable Actions:")
        print("1. Click an element")
        print("2. Input text")
        print("3. Hover over element")
        print("4. Scroll")
        print("5. Navigate to URL")
        print("6. Stop exploration")

        choice = input("\nChoose action (1-6): ").strip()

        if choice == "6":
            return None

        if choice == "1":
            element_num = int(input("Choose element number: ")) - 1
            element_id = state.interactive_elements[element_num]['element_id']
            return ClickAction(element_id=element_id)

        elif choice == "2":
            element_num = int(input("Choose input element number: ")) - 1
            element_id = state.interactive_elements[element_num]['element_id']
            value = input("Enter input value: ")
            return InputAction(element_id=element_id, input_value=value)

        elif choice == "3":
            element_num = int(input("Choose hover element number: ")) - 1
            element_id = state.interactive_elements[element_num]['element_id']
            return HoverAction(element_id=element_id)

        elif choice == "4":
            position = int(input("Enter scroll position (in pixels): "))
            return ScrollAction(position=position)

        elif choice == "5":
            url = input("Enter URL to navigate to: ")
            return NavigateAction(url=url)
        elif choice == "6":
            return None
        else:
            print("Invalid choice. Please try again.")
            return self.decide_next_action(state)

    def should_continue_exploration(self, state: PageState) -> bool:
        return input("\nContinue exploration? (y/n): ").lower().startswith('y') 