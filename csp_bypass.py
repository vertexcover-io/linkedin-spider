import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException

class CSPBypassHandler:
    def __init__(self, driver):
        self.driver = driver
        self.setup_csp_bypass()
        
    def setup_csp_bypass(self):
        try:
            self.driver.execute_cdp_cmd('Security.setIgnoreCertificateErrors', {'ignore': True})
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    (function() {
                        const originalConsoleError = console.error;
                        const originalConsoleWarn = console.warn;
                        const originalConsoleLog = console.log;
                        
                        const suppressPatterns = [
                            'interactionType undefined',
                            'tracking spec interactionType',
                            'Please verify that your tracking spec',
                            'Refused to execute inline script',
                            'Content Security Policy',
                            'CSP'
                        ];
                        
                        function shouldSuppress(message) {
                            return suppressPatterns.some(pattern => 
                                String(message).toLowerCase().includes(pattern.toLowerCase())
                            );
                        }
                        
                        console.error = function(...args) {
                            if (!shouldSuppress(args.join(' '))) {
                                originalConsoleError.apply(console, args);
                            }
                        };
                        
                        console.warn = function(...args) {
                            if (!shouldSuppress(args.join(' '))) {
                                originalConsoleWarn.apply(console, args);
                            }
                        };
                        
                        console.log = function(...args) {
                            if (!shouldSuppress(args.join(' '))) {
                                originalConsoleLog.apply(console, args);
                            }
                        };
                        
                        window.addEventListener('error', function(e) {
                            if (e.message && shouldSuppress(e.message)) {
                                e.preventDefault();
                                e.stopPropagation();
                                return false;
                            }
                        }, true);
                        
                        window.addEventListener('unhandledrejection', function(e) {
                            if (e.reason && shouldSuppress(String(e.reason))) {
                                e.preventDefault();
                                e.stopPropagation();
                                return false;
                            }
                        }, true);
                        
                        const originalEval = window.eval;
                        window.eval = function(code) {
                            try {
                                return originalEval.call(this, code);
                            } catch (e) {
                                if (shouldSuppress(String(e))) {
                                    return null;
                                }
                                throw e;
                            }
                        };
                        
                        const originalCreateElement = document.createElement;
                        document.createElement = function(tagName) {
                            const element = originalCreateElement.call(document, tagName);
                            if (tagName.toLowerCase() === 'script') {
                                const originalSetAttribute = element.setAttribute;
                                element.setAttribute = function(name, value) {
                                    if (name === 'src' && shouldSuppress(value)) {
                                        return;
                                    }
                                    return originalSetAttribute.call(this, name, value);
                                };
                            }
                            return element;
                        };
                    })();
                '''
            })
            
            self.driver.execute_cdp_cmd('Runtime.addBinding', {'name': 'trackingSuppress'})
            
        except Exception:
            pass
            
    def suppress_tracking_errors(self):
        try:
            self.driver.execute_script('''
                window.addEventListener('beforeunload', function() {
                    if (window.stop) window.stop();
                });
                
                setTimeout(function() {
                    const scripts = document.querySelectorAll('script[src*="tracking"], script[src*="analytics"]');
                    scripts.forEach(script => {
                        if (script.src.includes('tracking') || script.src.includes('analytics')) {
                            script.remove();
                        }
                    });
                }, 1000);
            ''')
        except JavascriptException:
            pass
            
    def simulate_natural_interaction(self, element):
        try:
            rect = element.rect
            viewport_height = self.driver.execute_script("return window.innerHeight")
            viewport_width = self.driver.execute_script("return window.innerWidth")
            
            element_center_x = rect['x'] + rect['width'] / 2
            element_center_y = rect['y'] + rect['height'] / 2
            
            if (0 <= element_center_x <= viewport_width and 
                0 <= element_center_y <= viewport_height):
                
                visible_area = min(rect['width'] * rect['height'], 
                                 (viewport_width - max(0, rect['x'])) * 
                                 (viewport_height - max(0, rect['y'])))
                total_area = rect['width'] * rect['height']
                
                if total_area > 0 and (visible_area / total_area) >= 0.5:
                    time.sleep(random.uniform(0.1, 0.3))
                    return True
                    
            return False
            
        except Exception:
            return False
            
    def handle_csp_violation(self):
        try:
            self.driver.execute_cdp_cmd('Page.setBypassCSP', {'enabled': True})
        except:
            try:
                self.driver.execute_cdp_cmd('Security.setOverrideCertificateErrors', {'override': True})
            except:
                pass