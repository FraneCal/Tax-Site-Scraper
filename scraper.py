from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import json

URL = "https://dits.deloitte.com/TaxTreatySubMenu"

driver = webdriver.Chrome()
driver.get(URL)
driver.maximize_window()

# Accept cookies
try:
    accept_cookies = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
    )
    accept_cookies.click()
except TimeoutException:
    print("No accept cookies button found.")

try:
    # Wait for jurisdiction list to load
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.jurisdiction-list.tab-headers'))
    )
    time.sleep(2)  # Let Angular render everything

    # Find all jurisdiction items
    items = driver.find_elements(By.CSS_SELECTOR, 'div.jurisdiction-list.tab-headers div.jurisdiction-item')

    print(f"Found {len(items)} jurisdictions.")

    for item in items:
        try:
            label = item.find_element(By.TAG_NAME, "span").text.strip()
            checkbox = item.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')

            print(f"Country: {label}")

            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)

        except Exception as e:
            print(f"Failed to process a checkbox: {e}")

    print("All checkboxes processed.")

except TimeoutException:
    print("Jurisdiction list or checkboxes not found.")

#Click Treaty Status tab
try:
    treaty_status = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="treatyStatusTab"]/a'))
    )
    treaty_status.click()
except Exception as e:
    print(f"Could not click Treaty Status tab: {e}")

# Click checkboxes in Treaty Status
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.status-list'))
    )
    time.sleep(1)

    status_checkboxes = driver.find_elements(By.CSS_SELECTOR, 'div.status-list input[type="checkbox"]')

    print(f"Found {len(status_checkboxes)} status checkboxes.")

    for cb in status_checkboxes:
        try:
            label = cb.find_element(By.XPATH, '..').text.strip()  # Get label text (Active, Pending, etc.)

            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
        except Exception as e:
            print(f"Could not click status checkbox: {e}")

    print("All status checkboxes clicked.")

except TimeoutException:
    print("Could not find status checkboxes.")

#Click Income Type tab
try:
    income_type = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="incomeTypeTab"]/a'))
    )
    income_type.click()
except Exception as e:
    print(f"Could not click Income type tab: {e}")

# Click checkboxes in Income Type
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[formarrayname="RateType"]'))
    )
    time.sleep(1)

    rate_checkboxes = driver.find_elements(By.CSS_SELECTOR, 'div[formarrayname="RateType"] input[type="checkbox"]')

    print(f"Found {len(rate_checkboxes)} rate checkboxes.")

    for cb in rate_checkboxes:
        try:
            label = cb.find_element(By.XPATH, '..').text.strip()  # Get label like "Dividends"

            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
        except Exception as e:
            print(f"Could not click rate checkbox: {e}")

    print("All rate type checkboxes clicked.")

except TimeoutException:
    print("Could not find rate checkboxes.")


# Click Submit button
try:
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="TreatySubMenu"]/li[5]/div/div/div/button'))
    )
    submit_button.click()
except Exception as e:
    print(f"Could not click Income type tab: {e}")

# Wait for the result section to appear (max 50 seconds)
try:
    WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.logo-description .taxTreatyTabHeader'))
    )
    print("Result page loaded.")
except TimeoutException:
    print("Timed out waiting for result content to load.")

time.sleep(3)

page_source = driver.page_source

driver.quit()

soup = BeautifulSoup(page_source, "html.parser")

# Extract country name
country_tag = soup.select_one('div.d-flex.align-items-center span')
country_name = country_tag.text.strip().lower() if country_tag else "unknown_country"

# Extract domestic withholding tax rates
tax_block = soup.select_one('div.withholding-tax-rate-container')

domestic_tax_data = {"domestic_withholding_tax_rates": {}}

if tax_block:
    rows = tax_block.select('div.row')
    for row in rows:
        try:
            label = row.select_one('.tax-rate-label').text.strip().lower()
            value = row.select_one('a').text.strip()

            if "dividend" in label:
                domestic_tax_data["domestic_withholding_tax_rates"]["dividends"] = {"value": value, "note": ""}
            elif "interest" in label:
                domestic_tax_data["domestic_withholding_tax_rates"]["interests"] = {"value": value, "note": ""}
            elif "royalt" in label:
                domestic_tax_data["domestic_withholding_tax_rates"]["royalties"] = {"value": value, "note": ""}
        except Exception as e:
            print(f"Failed to parse a tax row: {e}")
else:
    print("Could not find tax block.")

# Save to JSON file
with open(f"{country_name}.json", "w", encoding="utf-8") as f:
    json.dump(domestic_tax_data, f, ensure_ascii=False, indent=4)

print(f"Data saved to {country_name}.json")
