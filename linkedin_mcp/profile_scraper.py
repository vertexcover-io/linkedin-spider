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
            self.human_behavior.human_delay(0.5, 1)
            
            profile_data['location'] = self._extract_location()
            
            self.human_behavior.human_scroll("down", random.randint(150, 300))
            self.human_behavior.human_delay(0.5, 1)
            
            profile_data['about'] = self._extract_about()
            
            self.human_behavior.human_scroll("down", random.randint(200, 400))
            self.human_behavior.human_delay(0.5, 1)
            
            profile_data['experience'] = self._extract_experience()
            
            self.human_behavior.human_scroll("down", random.randint(150, 300))
            self.human_behavior.human_delay(0.5, 1)
            
            profile_data['education'] = self._extract_education()
            profile_data['profile_url'] = profile_url
            
            self.human_behavior.simulate_reading_behavior(1, 2)
            
            print(f"✅ Successfully scraped profile: {profile_data.get('name', 'Unknown')}")
            print(f"   Headline: {profile_data.get('headline', 'N/A')}")
            print(f"   Location: {profile_data.get('location', 'N/A')}")
            print(f"   Experience items: {len(profile_data.get('experience', []))}")
            print(f"   Education items: {len(profile_data.get('education', []))}")
            
            return profile_data
            
        except Exception as e:
            print(f"❌ Error scraping profile {profile_url}: {str(e)}")
            return None

    def _extract_name(self):
        try:
            name_selectors = [
                "h1.RSnQVDmQxbukCcEYuGuNoPURqPArEkqgsivZycKp",
                "h1.inline.t-24.v-align-middle.break-words",
                "h1.text-heading-xlarge",
                ".artdeco-entity-lockup__title"
            ]

            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name_text = name_element.text.strip()
                    if name_text and len(name_text) > 2:
                        self.tracking_handler.wait_for_element_impression(name_element)
                        return name_text
                except NoSuchElementException:
                    continue

            return "N/A"

        except Exception:
            return "N/A"

    def _extract_headline(self):
        try:
            headline_selectors = [
                ".text-body-medium.break-words[data-generated-suggestion-target]",
                ".text-body-medium.break-words",
                ".artdeco-entity-lockup__subtitle",
                ".pv-text-details__left-panel .text-body-medium"
            ]
            
            for selector in headline_selectors:
                try:
                    headline_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    headline_text = headline_element.text.strip()
                    if headline_text and len(headline_text) > 5 and "at" in headline_text:
                        self.tracking_handler.wait_for_element_impression(headline_element)
                        return headline_text
                except NoSuchElementException:
                    continue
                    
            return "N/A"
                
        except Exception:
            return "N/A"
            
    def _extract_location(self):
        try:
            location_selectors = [
                ".text-body-small.inline.t-black--light.break-words",
                ".ZVupBccScmICpeahdixjbwMyWnohfmssKtcZE .text-body-small",
                ".pv-text-details__left-panel .text-body-small"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_element.text.strip()
                    if location_text and ("," in location_text or any(place in location_text.lower() for place in ["india", "usa", "uk", "canada", "remote"])):
                        self.tracking_handler.wait_for_element_impression(location_element)
                        return location_text
                except NoSuchElementException:
                    continue
                    
            return "N/A"
                
        except Exception:
            return "N/A"
            
    def _extract_about(self):
        print("_extract_about")
        try:
            
            about_section = self._find_section_by_heading(['About'])
            if about_section:
                about_selectors = [
                    ".IdnWMVUysOalzPUojLvpTmxeXGfnteFWMcNKo.inline-show-more-text--is-collapsed span[aria-hidden='true']",
                    ".xWvevAsqcYnAlDMCComHNkMiwccwseGUD span[aria-hidden='true']",
                    ".pv-shared-text-with-see-more",
                    ".inline-show-more-text span[aria-hidden='true']"
                ]
                
                for selector in about_selectors:
                    try:
                        about_element = about_section.find_element(By.CSS_SELECTOR, selector)
                        about_text = about_element.text.strip()
                        if about_text and len(about_text) > 20:
                            self.tracking_handler.wait_for_element_impression(about_element, 0.5)
                            return about_text
                    except NoSuchElementException:
                        continue
            
            fallback_selectors = [
                ".IdnWMVUysOalzPUojLvpTmxeXGfnteFWMcNKo span[aria-hidden='true']",
                ".xWvevAsqcYnAlDMCComHNkMiwccwseGUD span[aria-hidden='true']",
                ".pv-shared-text-with-see-more"
            ]
            
            for selector in fallback_selectors:
                try:
                    about_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    about_text = about_element.text.strip()
                    if about_text and len(about_text) > 20:
                        self.tracking_handler.wait_for_element_impression(about_element, 0.5)
                        return about_text
                except NoSuchElementException:
                    continue
                    
            return "N/A"
                
        except Exception as e:
            # print(f"Error extracting about section: {str(e)}")
            return "N/A"

    def _extract_experience(self):
        experience_list = []
        
        try:
            experience_section = self.driver.find_element(By.CSS_SELECTOR, "section[data-view-name='profile-card'] div[id='experience']")
            if not experience_section:
                return experience_list
            
            experience_section_parent = experience_section.find_element(By.XPATH, "./ancestor::section")
            experience_containers = experience_section_parent.find_elements(
                By.CSS_SELECTOR, ".artdeco-list__item.OhIkZIVOPVYvyeBOKipHCuUrcVGbjoEik"
            )
            
            for container in experience_containers[:8]:
                exp_data = self._extract_experience_item(container)
                if exp_data and (exp_data.get('title') != "N/A" or exp_data.get('company') != "N/A"):
                    experience_list.append(exp_data)
                    
        except Exception as e:
            print(f"Error scraping experience: {str(e)}")
            
        return experience_list
    
    def _extract_experience_item(self, container):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", container)
            self.tracking_handler.wait_for_element_impression(container)
            self.human_behavior.human_delay(0.2, 0.5)
        except Exception:
            pass
        
        exp_data = {"title": "N/A", "company": "N/A", "company_url": "N/A", "duration": "N/A", "location": "N/A"}
        
        try:
            title_selectors = [
                ".display-flex.align-items-center.mr1.hoverable-link-text.t-bold span[aria-hidden='true']",
                ".mr1.t-bold span[aria-hidden='true']",
                ".hoverable-link-text.t-bold span[aria-hidden='true']"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = container.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_element.text.strip()
                    if title_text and len(title_text) > 2:
                        exp_data['title'] = title_text
                        break
                except Exception:
                    continue
        except Exception:
            pass
        
        try:
            company_link = container.find_element(By.CSS_SELECTOR, "a[data-field='experience_company_logo'][href*='/company/']")
            exp_data['company_url'] = company_link.get_attribute('href')
        except Exception:
            pass
        
        try:
            company_selectors = [
                ".t-14.t-normal span[aria-hidden='true']"
            ]
            
            company_elements = container.find_elements(By.CSS_SELECTOR, ".t-14.t-normal span[aria-hidden='true']")
            for element in company_elements:
                company_text = element.text.strip()
                if (company_text and 
                    len(company_text) > 2 and 
                    not "·" in company_text and
                    not "Full-time" in company_text and
                    not "Part-time" in company_text and
                    not "Contract" in company_text and
                    not any(x in company_text.lower() for x in ['present', 'mos', 'yrs', '2019', '2020', '2021', '2022', '2023', '2024', '2025'])):
                    exp_data['company'] = company_text
                    break
        except Exception:
            pass
        
        try:
            duration_selectors = [
                ".t-14.t-normal.t-black--light span[aria-hidden='true']",
                ".pvs-entity__caption-wrapper .t-12 span[aria-hidden='true']",
                ".t-12.t-normal span[aria-hidden='true']"
            ]
            
            for selector in duration_selectors:
                try:
                    duration_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in duration_elements:
                        duration_text = element.text.strip()
                        if (duration_text and 
                            ('·' in duration_text or 'present' in duration_text.lower()) and 
                            (any(x in duration_text.lower() for x in ['mos', 'yrs', 'present', 'month', 'year']) or 
                             any(month in duration_text.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']))):
                            exp_data['duration'] = duration_text
                            break
                    if exp_data['duration'] != "N/A":
                        break
                except Exception:
                    continue
        except Exception:
            pass
        
        try:
            location_elements = container.find_elements(By.CSS_SELECTOR, ".t-14.t-normal.t-black--light span[aria-hidden='true']")
            for element in location_elements:
                location_text = element.text.strip()
                if (location_text and 
                    ("·" in location_text or any(keyword in location_text for keyword in ["On-site", "Remote", "Hybrid", "India", "USA", "UK"]))
                    and not any(word in location_text for word in ["mos", "yrs", "Present", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])):
                    exp_data['location'] = location_text
                    break
        except Exception:
            pass
        
        return exp_data
    
    def _extract_education(self):
        education_list = []
        
        try:
            education_section = self.driver.find_element(By.CSS_SELECTOR, "section[data-view-name='profile-card'] div[id='education']")
            if not education_section:
                return education_list
            
            education_section_parent = education_section.find_element(By.XPATH, "./ancestor::section")
            education_containers = education_section_parent.find_elements(
                By.CSS_SELECTOR, ".artdeco-list__item.OhIkZIVOPVYvyeBOKipHCuUrcVGbjoEik"
            )
            
            for container in education_containers[:5]:
                edu_data = self._extract_education_item(container)
                if edu_data and edu_data.get('school') != "N/A":
                    education_list.append(edu_data)
                    
        except Exception as e:
            print(f"Error scraping education: {str(e)}")
            
        return education_list
    
    def _extract_education_item(self, container):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", container)
            self.tracking_handler.wait_for_element_impression(container)
            self.human_behavior.human_delay(0.2, 0.5)
        except Exception:
            pass
        
        edu_data = {"school": "N/A", "degree": "N/A", "field_of_study": "N/A", "duration": "N/A", "grade": "N/A"}
        
        try:
            school_element = container.find_element(By.CSS_SELECTOR, ".display-flex.align-items-center.mr1.hoverable-link-text.t-bold span[aria-hidden='true']")
            school_text = school_element.text.strip()
            if school_text and len(school_text) > 5:
                edu_data['school'] = school_text
        except Exception:
            pass
        
        try:
            degree_elements = container.find_elements(By.CSS_SELECTOR, ".t-14.t-normal span[aria-hidden='true']")
            for element in degree_elements:
                degree_text = element.text.strip()
                if (degree_text and 
                    len(degree_text) > 5 and 
                    ("Bachelor" in degree_text or "Master" in degree_text or "BTech" in degree_text or "MTech" in degree_text or "PhD" in degree_text or "Diploma" in degree_text)):
                    if ',' in degree_text:
                        parts = degree_text.split(',')
                        edu_data['degree'] = parts[0].strip()
                        if len(parts) > 1:
                            edu_data['field_of_study'] = parts[1].strip()
                    else:
                        edu_data['degree'] = degree_text
                    break
        except Exception:
            pass
        
        try:
            duration_elements = container.find_elements(By.CSS_SELECTOR, ".pvs-entity__caption-wrapper span[aria-hidden='true']")
            for element in duration_elements:
                duration_text = element.text.strip()
                if (duration_text and 
                    ("201" in duration_text or "202" in duration_text) and 
                    (" - " in duration_text or "to" in duration_text.lower())):
                    edu_data['duration'] = duration_text
                    break
        except Exception:
            pass
        
        return edu_data
    
    def _find_section_by_heading(self, headings):
        try:
            for heading in headings:
                section_selectors = [
                    f"//h2[contains(text(), '{heading}')]/ancestor::section",
                    f"//h2/span[contains(text(), '{heading}')]/ancestor::section",
                    f"//div[@id='experience']/ancestor::section",
                    f"//div[@id='education']/ancestor::section"
                ]
                
                for selector in section_selectors:
                    try:
                        if 'experience' in heading.lower() and 'experience' not in selector:
                            continue
                        if 'education' in heading.lower() and 'education' not in selector:
                            continue
                        
                        section = self.driver.find_element(By.XPATH, selector)
                        return section
                    except Exception:
                        continue
            
            fallback_selectors = [
                "section:has(h2):has(.pvs-list__paged-list-item)",
                ".pv-profile-section.experience",
                ".pv-profile-section.education"
            ]
            
            for selector in fallback_selectors:
                try:
                    section = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return section
                except Exception:
                    continue
                    
        except Exception:
            pass
            
        return None
