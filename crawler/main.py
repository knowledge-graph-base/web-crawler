# crawler/main.py

import sys
import os
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from bfs_crawler import BFSCrawler
from utils import manual_decision_prompt
# https://news.ycombinator.com
def main():
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
    driver.set_page_load_timeout(60)  # 30 seconds timeout

    # Create BFS crawler
    crawler = BFSCrawler(
        driver=driver,
        max_depth=2,
        user_decision_callback=manual_decision_prompt
    )

    # Run BFS
    graph = crawler.crawl(start_url)
    driver.quit()

    # Print summary
    print(f"\nCrawled {len(graph)} pages. Results stored in crawl_log.md and /screenshots.\n")

if __name__ == "__main__":
    # Ensure screenshots dir exists
    screenshots_dir = os.path.join(os.path.dirname(__file__), "..", "screenshots")
    if not os.path.exists(screenshots_dir):
        os.mkdir(screenshots_dir)

    # Clear or create the crawl log
    log_file = os.path.join(os.path.dirname(__file__), "..", "crawl_log.md")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("# Crawl Log\n\n")

    main()
