import urllib.parse

class SearchFilters:
    def __init__(self, location=None, industry=None):
        self.location = location
        self.industry = industry
        
    def to_url_params(self):
        params = {}
        
        if self.location:
            location_encoded = urllib.parse.quote(self.location)
            params['geoUrn'] = self._get_location_urn(self.location)
            
        if self.industry:
            industry_encoded = urllib.parse.quote(self.industry)
            params['industryUrn'] = self._get_industry_urn(self.industry)
            
        return params
    
    def _get_location_urn(self, location):
        location_mapping = {
            'san francisco bay area': '103644278',
            'new york': '103644278',
            'london': '102299470',
            'toronto': '101174742',
            'seattle': '103644278',
            'austin': '103644278',
            'boston': '103644278',
            'chicago': '103644278',
            'los angeles': '103644278',
            'denver': '103644278',
            'remote': '103644278',
            'united states': '103644278',
            'canada': '101174742',
            'united kingdom': '102299470',
            'england': '102299470',
            'germany': '101282230',
            'france': '105015875',
            'belgium': '100565514',
            'spain': '105646813',
            'italy': '103350119',
            'australia': '101452733',
            'india': '102713980',
            'china': '102890883',
            'japan': '101355337',
            'brazil': '106057199',
            'mexico': '103323778',
            'netherlands': '102890719',
            'singapore': '102454443',
            'switzerland': '106693272',
            'sweden': '105117694',
            'south korea': '105149562',
            'russia': '101728296',
            'united arab emirates': '104305776',
            'uae': '104305776'
        }
        
        location_lower = location.lower().strip()
        return location_mapping.get(location_lower, '102264497')
    
    def _get_industry_urn(self, industry):
        industry_mapping = {
            'accommodation services': '2190',
            'food and beverage services': '34',
            'bars taverns and nightclubs': '2217',
            'caterers': '2212',
            'mobile food services': '2214',
            'restaurants': '32',
            'hospitality': '31',
            'bed and breakfasts hostels homestays': '2197',
            'hotels and motels': '2194',
            'administrative and support services': '1912',
            'collection agencies': '1938',
            'events services': '110',
            'facilities services': '122',
            'janitorial services': '1965',
            'landscaping services': '2934',
            'fundraising': '101',
            'office administration': '1916',
            'security and investigations': '121',
            'security guards and patrol services': '1956',
            'security systems services': '1958',
            'staffing and recruiting': '104',
            'design': '3227',
            'e-learning': '3208',
            'education management': '3200',
            'entertainment': '3237',
            'fine art': '3196',
            'food beverages': '3195',
            'food production': '3224',
            'furniture': '3193',
            'government relations': '3232',
            'health wellness and fitness': '3207',
            'human resources': '3210',
            'import and export': '3209',
            'industrial automation': '3216',
            'information technology and services': '3231',
            'leisure travel tourism': '3194',
            'luxury goods and jewelry': '3212',
            'maritime': '3236',
            'mechanical or industrial engineering': '3221',
            'medical devices': '3217',
            'music': '3205',
            'non-profit organization management': '3202',
            'online media': '3214',
            'outsourcing offshoring': '3206',
            'packaging and containers': '3223',
            'paper and forest products': '3239',
            'philanthropy': '3230',
            'program development': '3203',
            'public policy': '3201',
            'renewables environment': '3213',
            'research': '3233',
            'semiconductors': '3218',
            'sporting goods': '3225',
            'tobacco': '3228',
            'transportation trucking railroad': '3222',
            'veterinary': '3188',
            'warehousing': '3229',
            'wine and spirits': '3220',
            'technology': '3231',
            'software development': '3231',
            'information technology': '3231',
            'financial services': '43',
            'banking': '43',
            'consulting': '96',
            'healthcare': '4',
            'pharmaceuticals': '4',
            'education': '3200',
            'media': '3214',
            'entertainment': '3237',
            'retail': '84',
            'manufacturing': '18',
            'automotive': '18',
            'real estate': '47',
            'construction': '47',
            'energy': '3',
            'oil and gas': '3',
            'aerospace': '2',
            'defense': '2',
            'telecommunications': '8',
            'transportation': '3222',
            'logistics': '3222',
            'government': '45',
            'non-profit': '3202',
            'marketing': '77',
            'advertising': '77',
            'human resources': '3210',
            'legal': '10',
            'accounting': '5',
            'sales': '85',
            'customer service': '85'
        }
        
        industry_lower = industry.lower().strip()
        return industry_mapping.get(industry_lower, '6')
    
    def is_empty(self):
        return not self.location and not self.industry
    
    def __str__(self):
        filters = []
        if self.location:
            filters.append(f"Location: {self.location}")
        if self.industry:
            filters.append(f"Industry: {self.industry}")
        return ", ".join(filters) if filters else "No filters"

def build_search_url(query, filters=None):
    base_url = "https://www.linkedin.com/search/results/people/"
    encoded_query = urllib.parse.quote(query)
    url = f"{base_url}?keywords={encoded_query}"
    
    if filters and not filters.is_empty():
        params = filters.to_url_params()
        param_strings = []
        for key, value in params.items():
            param_strings.append(f"{key}={value}")
        
        if param_strings:
            url += "&" + "&".join(param_strings)
    
    return url
