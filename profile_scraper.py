import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ProfileScraper:
    def __init__(self, driver, wait, human_behavior, tracking_handler):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.tracking_handler = tracking_handler
        
    def _is_valid_linkedin_url(self, url):
        if not url or not isinstance(url, str) or url == "N/A":
            return False
        linkedin_pattern = r'^https?://(www\.)?linkedin\.com/in/'
        return bool(re.match(linkedin_pattern, url))
    
    def scrape_profile(self, profile_url):
        if not self._is_valid_linkedin_url(profile_url):
            print(f"❌ Invalid profile URL: {profile_url}")
            return None
            
        print(f"Scraping profile: {profile_url}")
        
        try:
            self.driver.get(profile_url)
            
            self.human_behavior.human_delay(1, 2)
            self.human_behavior.simulate_reading_behavior(1, 3)
            
            profile_data = {}
            
            profile_data['name'] = self._extract_name()
            self.tracking_handler.simulate_interaction_types()
            
            profile_data['headline'] = self._extract_headline()
            self.human_behavior.human_scroll("down", random.randint(200, 400))
            self.human_behavior.human_delay(0.5, 1.5)
            
            profile_data['location'] = self._extract_location()
            
            self.human_behavior.human_scroll("down", random.randint(150, 300))
            self.human_behavior.human_delay(0.5, 1)
            
            profile_data['about'] = self._extract_about()
            
            self.human_behavior.human_scroll("down", random.randint(200, 400))
            self.human_behavior.human_delay(0.5, 1.5)
            
            profile_data['experience'] = self._extract_experience()
            profile_data['profile_url'] = profile_url
            
            self.human_behavior.simulate_reading_behavior(1, 2)
            
            print(f"✅ Successfully scraped profile: {profile_data.get('name', 'Unknown')}")
            print(f"   Headline: {profile_data.get('headline', 'N/A')}")
            print(f"   Location: {profile_data.get('location', 'N/A')}")
            print(f"   Experience items: {len(profile_data.get('experience', []))}")
            
            return profile_data
            
        except Exception as e:
            print(f"❌ Error scraping profile {profile_url}: {str(e)}")
            return None

    def _extract_name(self):
        print("_extract_name")
        try:
            name_selectors = [
                "h1.text-heading-xlarge",
                "h1[data-test-id='profile-name']",
                ".pv-text-details__left-panel h1",
                ".text-heading-xlarge",
                "h1.top-card-layout__title",
                ".artdeco-hoverable-trigger.artdeco-hoverable-trigger--content-placed-bottom.artdeco-hoverable-trigger--is-hoverable.ember-view"
            ]

            for selector in name_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    name_element = elements[0]
                    try:
                        self.tracking_handler.wait_for_element_impression(name_element)
                    except Exception:
                        pass
                    return name_element.text.strip()

            return "N/A"

        except Exception:
            return "N/A"

    def _extract_headline(self):
        print("_extract_headline")
        try:
            headline_selectors = [
                ".text-body-medium.break-words",
                ".pv-text-details__left-panel .text-body-medium", 
                ".top-card-layout__headline",
                "[data-test-id='profile-headline']",
                ".pv-entity__summary-info h2"
            ]
            
            headline = None
            for selector in headline_selectors:
                try:
                    headline = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.tracking_handler.wait_for_element_impression(headline)
                    break
                except NoSuchElementException:
                    continue
                    
            if headline:
                return headline.text.strip()
            else:
                return "N/A"
                
        except Exception:
            return "N/A"
            
    def _extract_location(self):
        try:
            location_selectors = [
                ".text-body-small.inline.t-black--light.break-words",
                ".pv-text-details__left-panel .text-body-small",
                ".top-card-layout__location",
                "[data-test-id='profile-location']",
                ".pv-text-details__right-panel span"
            ]
            
            location = None
            for selector in location_selectors:
                try:
                    location = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if "," in location.text:
                        self.tracking_handler.wait_for_element_impression(location)
                        break
                except NoSuchElementException:
                    continue
                    
            if location:
                return location.text.strip()
            else:
                return "N/A"
                
        except Exception:
            return "N/A"
            
    def _extract_about(self):
        try:
            about_selectors = [
                ".pv-shared-text-with-see-more",
                ".pv-about__summary-text",
                "[data-test-id='about-section'] .pv-shared-text-with-see-more",
                ".about .pv-shared-text-with-see-more",
                ".core-section-container__content .pv-shared-text-with-see-more"
            ]
            
            about_section = None
            for selector in about_selectors:
                try:
                    about_section = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.tracking_handler.wait_for_element_impression(about_section, 0.5)
                    break
                except NoSuchElementException:
                    continue
                    
            if about_section:
                return about_section.text.strip()
            else:
                return "N/A"
                
        except Exception:
            return "N/A"

    def _extract_experience(self):
        experience_list = []
        try:
            experience_containers = self.driver.find_elements(
                By.CSS_SELECTOR, ".artdeco-list__item"
            )

            for container in experience_containers[:5]:
                exp_data = {"title": "N/A", "company": "N/A", "duration": "N/A", "location": "N/A"}

                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", container)
                except Exception:
                    pass
                    
                try:
                    self.tracking_handler.wait_for_element_impression(container)
                except Exception:
                    pass
                    
                self.human_behavior.human_delay(0.2, 0.5)

                try:
                    logo_img = container.find_element(By.CSS_SELECTOR, "img[alt*='logo']")
                    alt_text = logo_img.get_attribute('alt')
                    if alt_text and 'logo' in alt_text:
                        exp_data['company'] = alt_text.replace(' logo', '').strip()
                except:
                    pass

                try:
                    spans = container.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                    texts = [span.text.strip() for span in spans if span.text.strip()]
                    
                    for text in texts:
                        if any(word in text.lower() for word in ['developer', 'engineer', 'director', 'manager', 'lead', 'cto', 'vp', 'president', 'head', 'senior', 'analyst', 'consultant', 'specialist', 'coordinator', 'assistant']):
                            if not any(keyword in text.lower() for keyword in ['full-time', 'part-time', 'contract', 'internship', 'remote', 'on-site', 'hybrid', 'mos', 'yrs', 'present']):
                                exp_data['title'] = text
                                break
                except:
                    exp_data['title'] = "N/A"

                try:
                    for text in texts:
                        if any(pattern in text.lower() for pattern in ['present', 'mos', 'yrs', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            if '·' in text and ('mos' in text or 'yrs' in text or 'present' in text):
                                exp_data['duration'] = text
                                break
                except:
                    pass

                try:
                    for text in texts:
                        if any(location_word in text.lower() for location_word in ['india', 'united states', 'california', 'new york', 'texas', 'florida', 'delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune', 'kolkata', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri', 'patna', 'vadodara', 'ghaziabad', 'ludhiana', 'agra', 'nashik', 'faridabad', 'meerut', 'rajkot', 'kalyan', 'vasai', 'varanasi', 'srinagar', 'aurangabad', 'noida', 'solapur', 'howrah', 'coimbatore', 'raipur', 'jabalpur', 'gwalior', 'vijayawada', 'jodhpur', 'madurai', 'ranchi', 'guntur', 'chandigarh', 'tiruchirappalli', 'mangalore', 'mysore', 'kozhikode', 'bhubaneswar', 'kota', 'amritsar', 'rajahmundry', 'bhavnagar', 'salem', 'warangal', 'guntakal', 'bhiwandi', 'saharanpur', 'gorakhpur', 'bikaner', 'amravati', 'nanded', 'kolhapur', 'sangli', 'malegaon', 'ulhasnagar', 'jalgaon', 'latur', 'ahmadnagar', 'dhule', 'ichalkaranji', 'parbhani', 'jalna', 'bhusawal', 'panvel', 'satara', 'beed', 'yavatmal', 'kamptee', 'gondia', 'barshi', 'achalpur', 'osmanabad', 'nandurbar', 'wardha', 'udgir', 'hinganghat']):
                            if '·' in text and any(work_type in text.lower() for work_type in ['on-site', 'remote', 'hybrid']):
                                exp_data['location'] = text
                                break
                except:
                    pass

                if exp_data['title'] != "N/A" or exp_data['company'] != "N/A":
                    experience_list.append(exp_data)

        except Exception as e:
            print(f"Error scraping experience: {str(e)}")

        return experience_list
