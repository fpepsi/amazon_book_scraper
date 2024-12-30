import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


user_query = None
# Prompt user for input
while not user_query or user_query.isspace():
    user_query = input("Hello, please type up to 5 words which will be used on my Amazon book search: ").strip()
    if not user_query or user_query.isspace():
        print("You must provide at least one word. \n")

# Create a list of words from user input
user_query_list = user_query.split()[:5]
search_query = " ".join(user_query_list)
price_list = []

# Initialize Selenium WebDriver
def initialize_browser():
    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking") 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    }
    )
    return driver


# Scrape Amazon for books
def scrape_amazon_books(search_query):
    driver = initialize_browser()
    books = []

    try:
        # Open Amazon website
        driver.get("https://www.amazon.com")

        # Select the books category
        search_bar_form = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "nav-search-bar-form"))
        )
        books_filter = search_bar_form.find_element(By.XPATH, './/select[@id="searchDropdownBox"]')
        books_filter.send_keys("Books")

        # Enter the search query
        search_input = driver.find_element(By.ID, "twotabsearchtextbox")
        search_input.clear()
        search_input.send_keys(search_query)
        search_input.send_keys(Keys.RETURN)

       # Wait for results to load
        results_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot.s-result-list.s-search-results.sg-row"))
        )

        # Find all list items with role="listitem"
        list_items = results_div.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')

        # Scrape information from each list item
        for item in list_items[:20]:
            try:
                puisg_row = item.find_element(By.CSS_SELECTOR, ".puisg-row")
                title = puisg_row.find_element(By.CSS_SELECTOR, "h2 span").text
                image = puisg_row.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")

                # Find all price sections inside specified anchor elements
                price_sections = puisg_row.find_elements(By.CSS_SELECTOR,"a.a-link-normal.s-no-hover.s-underline-text.s-underline-link-text.s-link-style.a-text-normal span.a-price span.a-offscreen")
                price_list = [price.get_attribute("innerText").strip() for price in price_sections if price.get_attribute("innerText").strip()]

                books.append({"title": title, "image": image, "prices": price_list})
            except Exception as e:
                # Skip if any information is missing
                continue

    except TimeoutException:
        print("Failed to load the page or find elements on time.")
    finally:
        if 'driver' in locals():
            print("Debugging information:")
            print(f"URL: {driver.current_url}")
            print("Press any key to close the driver...")
            input()  # Wait for user input
            driver.quit()

    return books

# Save results to a CSV file
def save_books_to_csv(books):
    with open("amazon_books.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "image", "prices"])
        writer.writeheader()
        for book in books:
            book["prices"] = ", ".join(book["prices"])  # Convert the list of prices to a string
            writer.writerow(book)
    print("Books saved to 'amazon_books.csv'.")

# Main flow
books = scrape_amazon_books(search_query)
if books:
    save_books_to_csv(books)
else:
    print("No books found matching the search query.")
