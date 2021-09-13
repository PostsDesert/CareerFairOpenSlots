from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import re
import time

extracted_data = {}

driver = None

# Make the chrome driver headless
# Currently turned off to improve reliability of javascript loading into the DOM
#chrome_options = Options()
#chrome_options.add_argument("--headless")
#driver = webdriver.Chrome(options=chrome_options)

def setup(fair):
    driver.get(fair['url'])
    wait_and_find_elements(By.XPATH, '//*[@id="root"]/div/div/div[1]/header/div/div[2]/button')[0].click()
    driver.find_element_by_xpath("//*[contains(text(), 'Event Info')]").click()
    fair_title = wait_and_find_elements(By.TAG_NAME, 'h2')[0].text
    driver.find_element_by_xpath("//*[contains(text(), 'Close')]").click()
    print(fair_title)
    
    extracted_data[fair_title] = {}

    # If the major filer is specified, filter the results
    if (fair['filter_by_major'] != ""):
        driver.find_element_by_xpath("//*[contains(text(), 'Tap here to view filtered / favorites / notes')]").click()
        driver.find_element_by_xpath("//*[contains(text(), 'CHANGE FILTERS')]").click()
        driver.find_element_by_xpath("//*[contains(text(), 'Majors')]").click()
        driver.find_element_by_xpath(f"//*[contains(text(), '{fair['filter_by_major']}')]").click()
        driver.find_element_by_xpath("//*[contains(text(), 'Close')]").click()

    return fair_title

def wait_and_find_elements(selector_type, selector , delay=60):
    wait_on_element_load(selector_type, selector, delay)
    return driver.find_elements(selector_type, selector)

def wait_on_element_load(selector_type, selector, delay=60):
    try:
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((selector_type, selector)))
        # print("Page is ready!")
    except TimeoutException:
        print("Loading took too much time!")

# Iterate through the fair urls specified in the fair_list
def scrape_fairs(fair_list):
    global driver
    driver = webdriver.Chrome()
    for fair_index, fair in enumerate(fair_list):
        fair_title = setup(fair)
        # Iterate through the companies in the fair
        companies = wait_and_find_elements(By.CLASS_NAME, 'employer-list-item-container')
        current_company_index = 0
        while(current_company_index < len(companies)):
            try:
                driver = webdriver.Chrome()
                fair_title = setup(fair)
                for company_index in range(current_company_index, len(companies)):
                    current_company_index = company_index
                    company = wait_and_find_elements(By.CLASS_NAME, 'employer-list-item-container')[i]
                    company_name = company.text
                    print(company_name)
                    extracted_data[fair_title][company_name] = {}
                    driver.execute_script("arguments[0].click();", company)
                    wait_on_element_load(By.CLASS_NAME, "employer-card-title")
                    # If the company has meetings, iterate through them. Otherwise, skip the company.
                    has_meetings = driver.find_elements(By.CLASS_NAME, "MuiAccordionSummary-content")
                    if (len(has_meetings) == 0):
                        extracted_data[fair_title][company_name] = 'No Positions Posted'
                    else:
                        # Iterate through the positions
                        positions = wait_and_find_elements(By.CLASS_NAME, 'MuiListItem-container')
                        for i, p in enumerate(positions):
                            # This is to resolve a bug where the first time the MuiListItem-container is accessed, it returns a stale exception.
                            # This is likely because the javascript reloaded the elements after they were selected.
                            try:
                                wait_on_element_load(By.TAG_NAME, 'h5')
                                position = wait_and_find_elements(By.CLASS_NAME, 'MuiListItem-container')[i]
                            
                                position_title = position.text.split('\n')
                            except:
                                time.sleep(5)
                                wait_on_element_load(By.TAG_NAME, 'h5')
                                position = wait_and_find_elements(By.CLASS_NAME, 'MuiListItem-container')[i]
                            
                                position_title = position.text.split('\n')

                            position_name = position_title[0]
                            try:
                                position_date = position_title[1].split('|')[0]
                            except:
                                position_date = position_title[1]
                            position_recruiter = position_title[2]
                            position_location = position_title[3]
                            try:
                                position_desc = wait_and_find_elements(By.CLASS_NAME, 'Linkify')[0].text
                            except:
                                time.sleep(5)
                                position_desc = wait_and_find_elements(By.CLASS_NAME, 'Linkify')[0].text
                            print(position_name)

                            # Add all the position data to the dictionary
                            extracted_data[fair_title][company_name][position_name] = {
                                'date': position_date,
                                'recruiter': position_recruiter,
                                'location': position_location,
                                'description': position_desc
                            }

                            # Prevents StaleElementReferenceException
                            click_object = wait_and_find_elements(By.TAG_NAME, 'h5', 60)[i]
                            driver.execute_script("arguments[0].click();", click_object)

                            # Figure out if the meeting is a group meeting or a one-on-one meeting
                            wait_on_element_load(By.XPATH, "//*[contains(text(), 'Schedule Details')]", 60)
                            group_meetings = driver.find_elements(By.XPATH, "//*[contains(text(), 'This is a Group Schedule')]")
                            one_on_one_meetings = driver.find_elements(By.XPATH, "//*[contains(text(), 'Available Meeting Times')]")
                            extracted_data[fair_title][company_name][position_name]['Times'] = []
                            if (len(group_meetings) != 0):
                                print("Group Meeting")
                                extracted_data[fair_title][company_name][position_name]['Times'] = "Group Meeting"
                                extracted_data[fair_title][company_name][position_name]["Spots Open"] = 9999
                            elif (len(one_on_one_meetings) != 0):
                                print("one-on-one meeting")

                                # Determine the number of meeting times available
                                number_meeting_times = [int(s) for s in re.findall(r'\b\d+\b', one_on_one_meetings[0].text)][0]
                                extracted_data[fair_title][company_name][position_name]["Spots Open"] = number_meeting_times
                                if (number_meeting_times == 0):
                                    print("No meeting times available")
                                    extracted_data[fair_title][company_name][position_name]['Times'] = "No meeting times available"
                                else:
                                    # If meeting times available, add the times to the dictionary
                                    times = wait_and_find_elements(By.CLASS_NAME, 'MuiChip-label')
                                    for t in times:
                                        time_text = t.text
                                        if "AM" in time_text or "PM" in time_text: 
                                            print(time_text)
                                            extracted_data[fair_title][company_name][position_name]['Times'].append(time_text)
                            else:
                                raise ValueError('Not a group or one-on-one meeting')

                            driver.back()
                    driver.back()
                    if (company_index % 15 == 0 and company_index != 0):
                        print('Sleeping for 15 seconds...')
                        time.sleep(15)
                    print("Fair number ")
                    print("Company number {current_company_index}/{len(companies)}")
            except Exception as e:
                print(e)
                print(f"Error: Restarting from company number {current_company_index}/{len(companies)}")
                continue
        
    
    return extracted_data

    

