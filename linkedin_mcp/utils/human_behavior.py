import time
import random
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from ..core.config import ScraperConfig

class HumanBehavior:
    def __init__(self, driver, wait, actions):
        self.driver = driver
        self.wait = wait
        self.actions = actions
        
    def human_delay(self, min_delay=None, max_delay=None):
        if min_delay is None and max_delay is None:
            min_delay, max_delay = ScraperConfig.HUMAN_DELAY_RANGE
        elif max_delay is None:
            max_delay = min_delay + random.uniform(0.5, 2.0)
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def human_type(self, element, text, clear_first=True):
        if clear_first:
            element.clear()
            self.human_delay(0.2, 0.5)
            
        if len(text) > 5 and random.random() < 0.1:
            typo_pos = random.randint(1, len(text) - 1)
            typo_char = random.choice("qwertyuiopasdfghjklzxcvbnm")
            
            for char in text[:typo_pos]:
                element.send_keys(char)
                time.sleep(random.uniform(*ScraperConfig.TYPING_DELAY_RANGE))
                
            element.send_keys(typo_char)
            time.sleep(random.uniform(0.1, 0.3))
            
            element.send_keys(Keys.BACKSPACE)
            time.sleep(random.uniform(0.1, 0.2))
            
            for char in text[typo_pos:]:
                element.send_keys(char)
                time.sleep(random.uniform(*ScraperConfig.TYPING_DELAY_RANGE))
        else:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(*ScraperConfig.TYPING_DELAY_RANGE))
                
        if random.random() < 0.3:
            self.human_delay(0.3, 0.8)
            
    def _can_scroll(self, direction):
        try:
            scroll_info = self.driver.execute_script("""
                return {
                    scrollTop: window.pageYOffset || document.documentElement.scrollTop,
                    scrollHeight: document.documentElement.scrollHeight,
                    clientHeight: document.documentElement.clientHeight,
                    canScrollDown: (window.pageYOffset || document.documentElement.scrollTop) < 
                                  (document.documentElement.scrollHeight - document.documentElement.clientHeight),
                    canScrollUp: (window.pageYOffset || document.documentElement.scrollTop) > 0
                };
            """)
            
            if direction == "down":
                return scroll_info.get('canScrollDown', False)
            else:
                return scroll_info.get('canScrollUp', False)
        except Exception:
            return True
    
    def _safe_scroll(self, direction, distance):
        try:
            if not self._can_scroll(direction):
                return False
                
            if direction == "down":
                self.driver.execute_script(f"window.scrollBy(0, {distance});")
            else:
                self.driver.execute_script(f"window.scrollBy(0, -{distance});")
            return True
        except Exception:
            return False

    def human_scroll(self, direction="down", distance=None):
        if distance is None:
            distance = random.randint(300, 800)
            
        if not self._can_scroll(direction):
            return
            
        scroll_steps = random.randint(3, 8)
        step_size = distance // scroll_steps
        
        for _ in range(scroll_steps):
            scroll_distance = step_size + random.randint(-50, 50)
            if not self._safe_scroll(direction, scroll_distance):
                break
                
            time.sleep(random.uniform(*ScraperConfig.SCROLL_PAUSE_RANGE))
            
        if random.random() < 0.2:
            self.human_delay(0.5, 1.5)
            back_distance = random.randint(50, 200)
            opposite_direction = "up" if direction == "down" else "down"
            if self._can_scroll(opposite_direction):
                self._safe_scroll(opposite_direction, back_distance)
            time.sleep(random.uniform(0.3, 0.7))
            
    def human_click(self, element, move_to_first=True):
        if move_to_first:
            self.actions.move_to_element_with_offset(
                element,
                random.randint(-ScraperConfig.MOUSE_MOVE_VARIANCE, ScraperConfig.MOUSE_MOVE_VARIANCE),
                random.randint(-ScraperConfig.MOUSE_MOVE_VARIANCE, ScraperConfig.MOUSE_MOVE_VARIANCE)
            ).perform()
            
            time.sleep(random.uniform(0.1, 0.3))
            
        self.actions.click(element).perform()
        self.human_delay(0.2, 0.6)
        
    def simulate_reading_behavior(self, min_time=1, max_time=3):
        reading_time = random.uniform(min_time, max_time)
        start_time = time.time()
        
        while time.time() - start_time < reading_time:
            action = random.choice(['scroll_down', 'scroll_up', 'pause', 'small_scroll'])
            
            if action == 'scroll_down':
                self.human_scroll("down", random.randint(150, 400))
            elif action == 'scroll_up':
                self.human_scroll("up", random.randint(80, 200))
            elif action == 'small_scroll':
                self.human_scroll("down", random.randint(30, 100))
            else:
                time.sleep(random.uniform(0.5, 1.5))
                
        self.human_delay(0.3, 1.0)