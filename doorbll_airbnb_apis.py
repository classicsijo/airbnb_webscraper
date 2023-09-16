import requests
import base64
import json
import time


## Define the request headers (fixed)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Airbnb-Supports-Airlock-V2": "true",
    "X-Airbnb-API-Key": "d306zoyjsyarp7ifhu67rjxn52tv0t20",
    "X-CSRF-Token": "null",
    "X-CSRF-Without-Token": "1",
    "X-Airbnb-GraphQL-Platform": "web",
    "X-Airbnb-GraphQL-Platform-Client": "minimalist-niobe",
    "X-Niobe-Short-Circuited": "true",
    "Origin": "https://www.airbnb.co.uk",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Alt-Used": "www.airbnb.co.uk",
    "TE": "trailers",
}


class api_request:
    def __init__(self, APIname, currency, location):
        self.session = requests.Session()
        self.APIname = APIname
        if APIname == 'explore':
            self.url = f"https://www.airbnb.co.uk/api/v3/ExploreSearch?operationName=ExploreSearch&locale=en-GB&currency={currency}"
        elif APIname == 'stays':
            self.url = f"https://www.airbnb.co.uk/api/v3/StaysSearch?operationName=StaysSearch&locale=en-GB&currency={currency}"
        else:
            raise ValueError('Provide avalid API name')
        
        print("Pinging Airbnb to get initial cookies")
        self.session.get("https://www.airbnb.co.uk", headers=headers)
        time.sleep(2)
        
        ## Access a map search in Airbnb to get additional cookies. Required for the API to work
        self.session.get(f'https://www.airbnb.co.uk/s/{location}--United-Kingdom', headers=headers)
        time.sleep(2)
    
    ## Generate the request data for the Explore API
    def create_data_payload_explore(self, coords, offset):
        return {
            'variables': {
                "request": {
                    "metadataOnly": 'false',
                    "version": "1.8.3",
                    "itemsPerGrid": 36,
                    "tabId": "home_tab",
                    "refinementPaths": ["/homes"],
                    "source": "structured_search_input_header",
                    "searchType": "pagination",
                    "mapToggle": 'false',
                    "neLat": coords['neLat'],
                    "neLng": coords['neLng'],
                    "swLat": coords['swLat'],
                    "swLng": coords['swLng'],
                    "searchByMap": 'true',
                    "itemsOffset": offset,
                    "cdnCacheSafe": 'false',
                    "simpleSearchTreatment": "simple_search_only",
                    "treatmentFlags": [],
                    "screenSize": "large",
                    "zoomLevel": coords['zoom']
                }
            },
        'extensions': {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "647ecde501ef18a6096e0bc1d41ed24b74aba0d99c072b34d84660ada41988f0"
            }
        }
    }
    
    ## Generate the request data for the Stays API
    def create_data_payload_stays(self, coords, pagination):
        return {
        "operationName": "StaysSearch",
        "variables": {
            "staysSearchRequest": {
                "requestedPageType": "STAYS_SEARCH",
                "cursor": pagination,
                "metadataOnly": False,
                "source": "structured_search_input_header",
                "searchType": "user_map_move",
                "treatmentFlags": [
                    "decompose_stays_search_m2_treatment",
                    "decompose_stays_search_m3_treatment",
                    "decompose_stays_search_m3_5_treatment",
                    "flex_destinations_june_2021_launch_web_treatment",
                    "new_filter_bar_v2_fm_header",
                    "flexible_dates_12_month_lead_time",
                    "lazy_load_flex_search_map_compact",
                    "lazy_load_flex_search_map_wide",
                    "im_flexible_may_2022_treatment",
                    "search_add_category_bar_ui_ranking_web",
                    "feed_map_decouple_m11_treatment",
                    "decompose_filters_treatment",
                    "pet_toggle_filter_panel_treatment_flag",
                    "flexible_dates_options_extend_one_three_seven_days",
                    "super_date_flexibility",
                    "micro_flex_improvements",
                    "micro_flex_show_by_default",
                    "search_input_placeholder_phrases",
                    "pets_fee_treatment",
                ],
                "rawParams": [
                    {"filterName": "adults", "filterValues": ["1"]},
                    {"filterName": "cdnCacheSafe", "filterValues": ["false"]},
                    {"filterName": "channel", "filterValues": ["EXPLORE"]},
                    {"filterName": "datePickerType", "filterValues": ["calendar"]},
                    #{"filterName": "flexibleTripDates", "filterValues": ["january"]},
                    {"filterName": "flexibleTripLengths", "filterValues": ["one_week"]},
                    {"filterName": "itemsPerGrid", "filterValues": ["18"]},
                    {"filterName": "monthlyLength", "filterValues": ["3"]},
                    #{"filterName": "monthlyStartDate", "filterValues": ["2023-10-01"]},
                    {"filterName": "neLat", "filterValues": [str(coords['neLat'])]},
                    {"filterName": "neLng", "filterValues": [str(coords['neLng'])]},
                    {"filterName": "priceFilterNumNights", "filterValues": ["2"]},
                    #{"filterName": "refinementPaths", "filterValues": ["/homes"]},
                    {"filterName": "screenSize", "filterValues": ["large"]},
                    {"filterName": "searchByMap", "filterValues": ["true"]},
                    {"filterName": "swLat", "filterValues": [str(coords['swLat'])]},
                    {"filterName": "swLng", "filterValues": [str(coords['swLng'])]},
                    {"filterName": "tabId", "filterValues": ["home_tab"]},
                    {"filterName": "version", "filterValues": ["1.8.3"]},
                    {"filterName": "zoomLevel", "filterValues": [str(coords['zoom'])]},
                ],
            },
            "feedMapDecoupleEnabled": True,
            "decomposeFiltersEnabled": True,
            "decomposeCleanupEnabled": False,
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "4e1362fea6e1dbe59f87d7f09fb254c9a700aac0d32c612c19ae12049fea1655",
            }
        },
    }
    

    def make_api_request(self, coords, offset):
        """
        Each API is called once for each page of results. In Explore API there are 36 per page, 18 in Stays API
        The Stays API requires page data to be converted to base64 before being transmitted
        """
        
        if self.APIname == 'explore':
            dataPayload = self.create_data_payload_explore(coords, offset)
        elif self.APIname == 'stays':
            if offset == 0:
                pagination_offset = {"section_offset":0,"items_offset":0,"version":1}
            else:
                pagination_offset = {"section_offset":3, "items_offset":offset, "version":1}
            json_string = json.dumps(pagination_offset, separators=(",", ":"))
            pagination = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
            dataPayload = self.create_data_payload_stays(coords, pagination)
        
        while True:
            try:
                response = self.session.post(self.url, headers=headers, json=dataPayload, timeout=12)  
                if response.status_code == 429:
                    print("Too many requests to server. Restart with a slower speed or use a VPN")
                    time.sleep(30)
                elif response.status_code != 200:
                    ## Save response failures as a json file in the main folder for debugging
                    print(f"Response failure. Status code: {response.status_code}")
                    with open(f"error_{response.status_code}.json", "w", encoding="utf-8") as file:
                        file.write(response.text)
                else:
                    break            
            except requests.exceptions.HTTPError as http_error:
                print(f"HTTP error occurred: {http_error}")
            except requests.exceptions.ConnectionError as connection_error:
                print(f"Connection error occurred: {connection_error}")
            except requests.exceptions.Timeout as timeout_error:
                print(f"Timeout error occurred: {timeout_error}")
            except requests.exceptions.RequestException as request_error:
                print(f"Request exception occurred: {request_error}")
            except Exception as e:
                print(f"An unexpected request error occurred: {e}")
            finally:
                time.sleep(3)
            
        return json.loads(response.text)
    
    def closeSession(self):
        self.session.close()