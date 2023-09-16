import json
import math
import re
import os
import doorbll_airbnb_apis  ## Custom script for running Python requests


## Configuration constants
SEARCH_URL = 'https://www.airbnb.co.uk/s/Swansea/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2023-10-01&monthly_length=3&price_filter_input_type=2&price_filter_num_nights=5&channel=EXPLORE&query=Swansea&place_id=ChIJsZdOWlVFbkgRdMvnL44Sdz0&date_picker_type=calendar&source=structured_search_input_header&search_type=user_map_move&ne_lat=51.66847029916367&ne_lng=-3.893271602131847&sw_lat=51.57138493761716&sw_lng=-4.026045528145602&zoom=12.678604930674044&zoom_level=12.678604930674044&search_by_map=true'
LOCATION = 'Swansea'
CURRENCY = 'GBP'
APPEND_ADDITIONAL_STAY_INFO = True


def get_map_tile_from_url(url):
    """ Extract map tile coordinates from the given URL """
    
    pattern_coords = r'ne_lat=([-0-9.]+)&ne_lng=([-0-9.]+)&sw_lat=([-0-9.]+)&sw_lng=([-0-9.]+)'
    match_coords = re.search(pattern_coords, url)
    
    pattern_zoom = r'zoom=([\d.]+)'
    match_zoom = re.search(pattern_zoom, url)
    
    if match_coords and match_zoom:
        ne_lat, ne_lng, sw_lat, sw_lng = match_coords.groups()
        zoom = match_zoom.group(1)
        mapTile = {
            "neLat": float(ne_lat),
            "neLng": float(ne_lng),
            "swLat": float(sw_lat),
            "swLng": float(sw_lng),
            "zoom": int(float(zoom))
        }
        return mapTile
    else:
        raise Exception("URL does not contain co-ordinates. Make sure the input URL string contains ne_lat, ne_lng, sw_lat, sw_lng and zoom") 


def apply_haversine_formula(lat1, lat2):
    """ Calculate the distance between two points using Haversine formula
        Where 6371 is a constant, the radius of the earth """
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return 6371.0 * c

def calculate_area_from_coords(mapTile):
    width_km = apply_haversine_formula(mapTile['swLat'], mapTile['neLat'])
    height_km = apply_haversine_formula(mapTile['swLng'], mapTile['neLng'])
    area_km2 = int(width_km * height_km)
    
    return area_km2

def divide_map_tiles(coords):
    """
    When there are more than 300 results in a map tile, Airbnb will only show the first 300
    In this case, split the tile into quarters and provide Ne/Sw co-ordinates for each of these 4 tiles
    These are appended to the list of tile
    """
    halfLat = (coords['neLat']-coords['swLat'])/2
    halfLng = (coords['neLng']-coords['swLng'])/2
    zoom = coords['zoom']+1
    
    coords_1 = {'neLat': coords['neLat'], 'neLng': coords['neLng'], 'swLat': coords['swLat']+halfLat, 'swLng': coords['swLng']+halfLng, 'zoom': zoom}
    coords_2 = {'neLat': coords['neLat']-halfLat, 'neLng': coords['neLng'], 'swLat': coords['swLat'], 'swLng': coords['swLng']+halfLat, 'zoom': zoom}
    coords_3 = {'neLat': coords['neLat'], 'neLng': coords['neLng']-halfLng, 'swLat': coords['swLat']+halfLat, 'swLng': coords['swLng'], 'zoom': zoom}
    coords_4 = {'neLat': coords['neLat']-halfLat, 'neLng': coords['neLng']-halfLng, 'swLat': coords['swLat'], 'swLng': coords['swLng'], 'zoom': zoom}

    return [coords_1, coords_2, coords_3, coords_4]

def run_exploreAPI():
    mapTile_list = [get_map_tile_from_url(SEARCH_URL)]    ## Always starts with one large map tile
    already_downloaded_listingIDs = []

    exploreAPI = doorbll_airbnb_apis.api_request('explore', CURRENCY, LOCATION)
    
    while len(mapTile_list) > 0:
        """
        For each map tile, iterate through each page of results (36 per page). The cutoff for properties listed on a
        tile is 300+, after this divide the tile into quarters and keep re-running the process.
        Listing data is embedded deep in the returned JSON, stored in the Subset variable
        """
        
        coords = mapTile_list.pop(0)
        offset = 0
            
        results = exploreAPI.make_api_request(coords, offset)
        totalCount = int(results['data']['dora']['exploreV3']['metadata']['paginationMetadata']['totalCount'])
        print(f"Approximate MapTile area is {calculate_area_from_coords(coords)+1} km²")       ## Add 1 to estimated size to stop mild confusion of 0 km² tiles
        
        if totalCount >= 300:
            print("300+ Listings in this MapTile. Generating 4 additional tiles")
            mapTile_list.extend(divide_map_tiles(coords)) 
            print(f" - MapTiles now remaining: {len(mapTile_list)}")
            continue        
        elif totalCount == 0:
            print(" - No Listings in this MapTile", end="")        
            
        ## Iterate through each page of results
        while offset < totalCount:
            if offset > 0:
                results = exploreAPI.make_api_request(coords, offset)
            
            exploreResultsSubset = results['data']['dora']['exploreV3']['sections'][1]['items']
            
            for e in exploreResultsSubset:
                listing_id = e['listing']['id']
                
                ## If the listing has not already been downloaded, save the json file
                if listing_id not in already_downloaded_listingIDs:
                    already_downloaded_listingIDs.append(listing_id)
                    explore_dict = e['listing']
                    with open(f"{LOCATION}/{listing_id}.json", "w", encoding="utf-8") as file:
                        file.write(json.dumps(explore_dict))
    
            offset += 36
            offset = offset if offset <= totalCount else totalCount
            
            print(f"\r - Downloading {offset}/{totalCount}", end="")
        
        print(f"\nMapTiles remaining: {len(mapTile_list)} -- Total Listings: {len(already_downloaded_listingIDs)}")

    exploreAPI.closeSession()
    return already_downloaded_listingIDs

def run_staysAPI(already_downloaded_listingIDs):
    mapTile_list = [get_map_tile_from_url(SEARCH_URL)]
    already_updated_listingIDs = []

    staysAPI = doorbll_airbnb_apis.api_request('stays', CURRENCY, LOCATION)
    
    while len(mapTile_list) > 0 and APPEND_ADDITIONAL_STAY_INFO:
        """
        This process runs after the Explore API. After retrieving listing data using the same MapTile methods,
        it reads the above saved JSON files and appends additional dicts to it.
        The only useful addition is pricing data. This is the cost for 5 nights when the property is next available
        This is typically only found for 80-90% of listings, covering the majority of short term lets.
        It will not be found when any of the following is true:
            - The listing has 0 availability
            - The listing has a minimum stay of more than 5 nights
            - The listing has no availability for at least 5 nights
            - The listing has no availability in the next two months
        """
    
        coords = mapTile_list.pop(0)
        offset = 0
        
        results = staysAPI.make_api_request(coords, offset)
    
        ## For debugging. If the Explore API stage is skipped, get a list of listing IDs from the json files in a folder
        if len(already_downloaded_listingIDs) == 0:
            current_directory = os.getcwd()
            file_list = os.listdir(f'{current_directory}\\{LOCATION}')
            for filename in file_list:
                if filename.endswith('.json'):
                    filename_without_extension = os.path.splitext(filename)[0]
                    already_downloaded_listingIDs.append(filename_without_extension)
                    
        try:
            totalCount_Title = results['data']['presentation']['explore']['sections']['sectionIndependentData']['staysSearch']['sectionConfiguration']['pageTitleSections']['sections'][0]['sectionData']['structuredTitle']
            matches = re.search(r'(\d+,\d+|\d+)', totalCount_Title)  
            totalCount = int(matches.group(0).replace(',', ''))
        except TypeError:
            totalCount = 0  
        print(f"The approximate MapTile area is {calculate_area_from_coords(coords)+1} km²")    ## Add 1 to estimated size to stop mild confusion of 0 km² tiles
        
        if totalCount >= 300:
            print("300+ Listings in this MapTile. Generating 4 additional tiles")
            mapTile_list.extend(divide_map_tiles(coords)) 
            print(f" - Updated MapTiles remaining: {len(mapTile_list)}")
            continue        
        elif totalCount == 0:
            print(" - No Listings in this MapTile", end="")
        else:
            print(f"\r - Downloaded {offset}/{totalCount}", end="")
            
        while offset < totalCount:
            
            if offset > 0: 
                results = staysAPI.make_api_request(coords, offset)
        
            searchResultsSubset = results['data']['presentation']['explore']['sections']['sectionIndependentData']['staysSearch']['searchResults']
            
            for s in searchResultsSubset:
                if 'listing' in s and 'id' in s['listing']:     ## Not every listing in the search results is a property. There are recommended shared stays. These do not have a listing ID, so ignore them
                    listing_id = s['listing']['id']
                    s['listing_stays'] = s.pop('listing')       ## Rename the dict key 'listing' to 'listing_stays', so it is appended to the json file without conflict
                   
                    if listing_id not in already_updated_listingIDs and listing_id in already_downloaded_listingIDs:
                        already_updated_listingIDs.append(listing_id)
    
                        ## Read in the existing json file for the listing id, and append to it
                        with open(f'{LOCATION}/{listing_id}.json', 'r') as file:
                            existing_json = json.load(file)
                        s = {**existing_json, **s}
                    
                    elif listing_id not in already_downloaded_listingIDs:
                        print(f"\nListing ID {listing_id} not seen on initial explore API")
                
                with open(f"{LOCATION}/{listing_id}.json", "w", encoding="utf-8") as file:
                    file.write(json.dumps(s))      
        
            offset += 18
            offset = offset if offset <= totalCount else totalCount
                
            print(f"\r - Updating {len(already_updated_listingIDs)}/{len(already_downloaded_listingIDs)} listings", end="")
        
        print(f"\nMapTiles remaining: {len(mapTile_list)}")    
        
    staysAPI.closeSession()
    return already_updated_listingIDs
    
if __name__ == "__main__":
    print("Starting Doorbll Airbnb Scraping")
    
    if not os.path.exists(LOCATION):
        os.makedirs(LOCATION)
    else:
        input(f'Output folder {LOCATION} already exists. JSON files will be appended to this folder. Press enter to continue')
    
    ## Stage 1: Explore API. Iterate through each map tile
    print("Starting MapTile processing for Explore API")
    already_downloaded_listingIDs = run_exploreAPI()

    ## Stage 2: Stays API. Optional. Append basic pricing info for most listings
    print("Starting MapTile processing for stays API")
    already_updated_listingIDs = run_staysAPI(already_downloaded_listingIDs)

    ## End program
    print(f'End of Airbnb webscrape for {LOCATION}\n Total listings downloaded {len(already_downloaded_listingIDs)}')
    if APPEND_ADDITIONAL_STAY_INFO:
        print(f'Total listings updated with pricing {len(already_updated_listingIDs)}/{len(already_downloaded_listingIDs)}')
    
    