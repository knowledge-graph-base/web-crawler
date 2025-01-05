#!/usr/bin/env python3

import sys
import os
import time
import logging

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from crawler.interactive_crawler import InteractiveCrawler
from crawler.decision_maker.human_decision_maker import HumanDecisionMaker

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce logging noise from selenium
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def main():
    setup_logging()
    
    # Parse URL from command line or default
    if len(sys.argv) > 1:
        start_url = sys.argv[1]
    else:
        start_url = "https://quickbooks.intuit.com"

    # Setup Selenium for headless Chrome
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.page_load_strategy = 'eager'  # Don't wait for all resources to load
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")

    driver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=driver_service, options=chrome_options)
    driver.set_page_load_timeout(60)  # 60 seconds timeout

    # Create decision maker and crawler
    decision_maker = HumanDecisionMaker()
    crawler = InteractiveCrawler(
        driver=driver,
        decision_maker=decision_maker
    )

    # Run interactive crawl
    try:
        graph = crawler.crawl(start_url)
        print(f"\nCrawl completed. Results stored in crawl_log.md and /screenshots.\n")
        print(f"Graph contains {len(graph.nodes)} pages and {len(graph.edges)} actions.\n")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Ensure screenshots dir exists
    screenshots_dir = os.path.join("screenshots")
    if not os.path.exists(screenshots_dir):
        os.mkdir(screenshots_dir)

    # Clear or create the crawl log
    log_file = os.path.join("crawl_log.md")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("# Crawl Log\n\n")

    main() 