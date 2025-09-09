import time
import random
import platform
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException

class CSPBypassHandler:
    def __init__(self, driver):
        self.driver = driver
        self.is_macos = platform.system() == "Darwin"
        self.setup_csp_bypass()
        if self.is_macos:
            self.setup_macos_stealth()
        
    def setup_csp_bypass(self):
        try:
            self.driver.execute_cdp_cmd('Security.setIgnoreCertificateErrors', {'ignore': True})
            
            stealth_script = self._get_stealth_script()
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_script
            })
            
            self.driver.execute_cdp_cmd('Runtime.addBinding', {'name': 'trackingSuppress'})
            
        except Exception:
            pass
    
    def _get_stealth_script(self):
        base_script = '''
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
        '''
        
        if self.is_macos:
            macos_additions = '''
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'MacIntel',
                    configurable: true
                });
                
                Object.defineProperty(navigator, 'userAgent', {
                    get: () => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    configurable: true
                });
                
                Object.defineProperty(navigator, 'appVersion', {
                    get: () => '5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    configurable: true
                });
                
                Object.defineProperty(screen, 'width', {
                    get: () => 1920,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'height', {
                    get: () => 1080,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'availWidth', {
                    get: () => 1920,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'availHeight', {
                    get: () => 1055,
                    configurable: true
                });
                
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                    configurable: true
                });
                
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                    configurable: true
                });
                
                Object.defineProperty(navigator, 'maxTouchPoints', {
                    get: () => 0,
                    configurable: true
                });
                
                const originalPermissionsQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {
                    return originalPermissionsQuery.call(this, parameters).then(result => {
                        if (parameters.name === 'notifications') {
                            return { state: 'default', onchange: null };
                        }
                        return result;
                    });
                };
            '''
            base_script += macos_additions
        
        base_script += '''
            })();
        '''
        
        return base_script
    
    def setup_macos_stealth(self):
        try:
            self.driver.execute_cdp_cmd('Emulation.setUserAgentOverride', {
                'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'acceptLanguage': 'en-US,en;q=0.9',
                'platform': 'macOS'
            })
            
            self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                'timezoneId': 'America/New_York'
            })
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        configurable: true
                    });
                    
                    delete navigator.__proto__.webdriver;
                    
                    const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
                    Object.getOwnPropertyDescriptor = function(obj, prop) {
                        if (obj === navigator && prop === 'webdriver') {
                            return undefined;
                        }
                        return originalGetOwnPropertyDescriptor.call(this, obj, prop);
                    };
                    
                    Object.defineProperty(window, 'chrome', {
                        get: () => ({
                            runtime: {
                                onConnect: undefined,
                                onMessage: undefined
                            },
                            loadTimes: () => ({
                                commitLoadTime: Date.now() / 1000 - Math.random(),
                                connectionInfo: 'h2',
                                finishDocumentLoadTime: Date.now() / 1000,
                                finishLoadTime: Date.now() / 1000,
                                firstPaintAfterLoadTime: 0,
                                firstPaintTime: Date.now() / 1000,
                                navigationType: 'Other',
                                npnNegotiatedProtocol: 'h2',
                                requestTime: Date.now() / 1000 - Math.random(),
                                startLoadTime: Date.now() / 1000 - Math.random(),
                                wasAlternateProtocolAvailable: false,
                                wasFetchedViaSpdy: true,
                                wasNpnNegotiated: true
                            }),
                            csi: () => ({
                                onloadT: Date.now(),
                                pageT: Date.now() - performance.timing.navigationStart,
                                startE: performance.timing.navigationStart,
                                tran: 15
                            })
                        }),
                        configurable: true
                    });
                    
                    const originalPluginsGetter = Object.getOwnPropertyDescriptor(Navigator.prototype, 'plugins').get;
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => {
                            const pluginArray = Object.create(PluginArray.prototype, {
                                length: { value: 5, writable: false, enumerable: false, configurable: true },
                                0: {
                                    value: {
                                        0: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: null },
                                        description: 'Portable Document Format',
                                        filename: 'internal-pdf-viewer',
                                        length: 1,
                                        name: 'Chrome PDF Plugin'
                                    },
                                    writable: false,
                                    enumerable: true,
                                    configurable: true
                                },
                                1: {
                                    value: {
                                        0: { type: 'application/x-nacl', suffixes: '', description: 'Native Client Executable', enabledPlugin: null },
                                        1: { type: 'application/x-pnacl', suffixes: '', description: 'Portable Native Client Executable', enabledPlugin: null },
                                        description: 'Native Client',
                                        filename: 'internal-nacl-plugin',
                                        length: 2,
                                        name: 'Native Client'
                                    },
                                    writable: false,
                                    enumerable: true,
                                    configurable: true
                                },
                                2: {
                                    value: {
                                        description: 'Chrome PDF Viewer',
                                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                                        length: 0,
                                        name: 'Chrome PDF Viewer'
                                    },
                                    writable: false,
                                    enumerable: true,
                                    configurable: true
                                },
                                3: {
                                    value: {
                                        description: 'Chromium PDF Viewer',
                                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                                        length: 0,
                                        name: 'Chromium PDF Viewer'
                                    },
                                    writable: false,
                                    enumerable: true,
                                    configurable: true
                                },
                                4: {
                                    value: {
                                        description: 'Microsoft Edge PDF Viewer',
                                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                                        length: 0,
                                        name: 'Microsoft Edge PDF Viewer'
                                    },
                                    writable: false,
                                    enumerable: true,
                                    configurable: true
                                }
                            });
                            
                            return pluginArray;
                        },
                        configurable: true
                    });
                    
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter.call(this, parameter);
                    };
                '''
            })
            
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
            
            if self.is_macos:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'acceptLanguage': 'en-US,en;q=0.9',
                    'platform': 'macOS'
                })
                
                self.driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                    'width': 1920,
                    'height': 1080,
                    'deviceScaleFactor': 2,
                    'mobile': False
                })
                
        except:
            try:
                self.driver.execute_cdp_cmd('Security.setOverrideCertificateErrors', {'override': True})
            except:
                pass