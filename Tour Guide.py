#!/usr/bin/env python
# coding: utf-8

# # TOUR GUIDE 
# **Main Features**
# 1. An app that Can Find your Location automatically 
# 2. Can find your typed location
# 3. Plot these locations on the Map
# 4. Find and Display the venues around you 
# 4. Can tell you at what distance every value is located and other details about
# 5. Mark Red for Low Green for Good and Dark Green for Very Good Ratings of a Venues
# 6. You can search specific category and Trending venues around you aswell

# ### All The necessary Imports 

# In[1]:


import json                               # library to handle JSON files
import folium                             # map rendering library
import requests                           # Handle Requests
import warnings                           # Ignore all th warning 
import numpy as np 
import pandas as pd 
import matplotlib.cm as cm
from matplotlib import pyplot as plt
import matplotlib.colors as colors
get_ipython().run_line_magic('matplotlib', 'inline')


from geopy.geocoders import Nominatim     # convert an address into latitude and longitude values
from pandas.io.json import json_normalize # tranform JSON file into a pandas dataframe


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
warnings.filterwarnings("ignore")


# #### Define Foursquare Credentials and Version
# https://developer.foursquare.com/

# In[35]:


CLIENT_ID     = '****************' # add your Foursquare ID
CLIENT_SECRET = '****************' # add your Foursquare Secret
ACCESS_TOKEN  = '****************' # add your FourSquare Access Token
VERSION = '20180604'


# ### Get the location of Device Using 
# #### https://mycurrentlocation.net/
# #### Scrape the (Lat , Lon ) Cordinates 

# In[37]:


# Return the Long. Lat. of the Your Current Location (Estimated)
def findmyLocation():
    chrome_options = Options()
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    timeout = 20
    driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='F:\chromedriver.exe')
    driver.get("https://mycurrentlocation.net/")
    wait = WebDriverWait(driver, timeout)
    longitude = driver.find_elements_by_xpath('//*[@id="longitude"]')
    longitude = [x.text for x in longitude]
    longitude = str(longitude[0])
    latitude = driver.find_elements_by_xpath('//*[@id="latitude"]')
    latitude = [x.text for x in latitude]
    latitude = str(latitude[0])
    driver.quit()
    return (latitude,longitude)

# Find the Location which you Will give it to (Return the Long. Lat. of the added Location)
def findlocation():
    address = input("Please enter the Address : ")
    geolocator = Nominatim(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36")
    location = geolocator.geocode(address)
    latitude = location.latitude
    longitude = location.longitude
    return (latitude,longitude)


    ##### FUNCTION TO FIND THE RATING OF A VANUES (Return darkgreen if rating GREATER than 8 , Green if greater than 7 , Below 7 Red  )
def rating(VENUE_ID):
    url = 'https://api.foursquare.com/v2/venues/{}?&client_id={}&client_secret={}&v={}'.format(
        VENUE_ID,
        CLIENT_ID, 
        CLIENT_SECRET, 
        VERSION)
    results = requests.get(url).json()
    try:
        x=results['response']['venue']['rating']
        if x>= 8:
            return "darkgreen"
        elif x >= 6 and x < 8 :
            return 'blue'
        else:
            return 'red'
    except KeyError:
        return 'red'
    except:
        return 'red'

### Return the Venues JSON containing all the details about a Venues

def venues(latitude , longitude , LIMIT = 100 , radius = 500 ): # limit of number of venues returned by Foursquare API
    """ return the NAME,LOCATION,ID,CATAGORY of a venues """
 
                                         #venues, users , tips
                                                #search,explore,trending  if search then pass te query too                ,query={} coffe, hotels ,resturents etc
    url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET,
    VERSION, 
    latitude, 
    longitude, 
    radius, 
    LIMIT)
    results = requests.get(url).json()
    if len(results["response"]["groups"][0]['items']) > 20 or radius > 2000 :
        return results
    else:
        return venues(latitude=latitude ,longitude=longitude,LIMIT = LIMIT , radius = radius+500 )
              


         # FUNCTION TO CLEAN THE JSON RESPONSE FROM THE FOURSQUARE API
def venues_clean(res):
    venues=res["response"]["groups"][0]['items'] # Extract the Venues JSON from the response 
    nearby_venues = json_normalize(venues) # flatten JSON and convert it into Pandas Dataframe
    data_df = nearby_venues[ [             # Filter Dataframe for the Required data of venues
    'venue.id','venue.name',
    'venue.categories',
    'venue.location.lat',
    'venue.location.lng',
    'venue.location.distance'] ]
    # Extract the catagory from the JSON 'venue.categories'
    data_df['venue.categories']=data_df['venue.categories'].apply( lambda x : x[0]["name"] )
    # Clean the name of Columns of Dataframe
    data_df.columns = [col.split(".")[-1] for col in data_df.columns]
    data_df["rating"]=data_df["id"].apply(rating)
    return data_df


##### Search Specific Catagory of Venues around a Location
def venues_cat(latitude ,longitude,search_query,LIMIT = 100 , radius = 1000 ): # limit of number of venues returned by Foursquare API
    """ return the NAME,LOCATION,ID,CATAGORY of venues """
    url = 'https://api.foursquare.com/v2/venues/search?client_id={}&client_secret={}&ll={},{}&v={}&query={}&radius={}&limit={}'.format(
        CLIENT_ID,
        CLIENT_SECRET,
        latitude,
        longitude,
        VERSION,
        search_query,
        radius,
        LIMIT)     
    results = requests.get(url).json()
    
    """If There is no Venue of that catagory around then Increase the radius of Search by 500 meter and search again.
        Repeat this process until you find a nearest Veneu"""
    
    if len(results["response"]["venues"]) > 5 or radius > 5000 :
        return results
    else:
        return venues_cat(latitude=latitude ,longitude=longitude,search_query = search_query,LIMIT = LIMIT , radius = radius+500 )
    
#### CLEAN THE DATA OF SEARCH  
def venues_cat_clean(res):
    df=json_normalize(res['response']['venues'])
    df=df[['id','name','categories','location.lat','location.lng','location.distance']]
    lis=[]
    for i in df['categories']:
        try:
            lis.append(i[0]['name'])
        except:
            lis.append("_")
    df["categories"]=lis
    df.columns = [col.split(".")[-1] for col in df.columns]
    df["rating"]=df["id"].apply(rating)
    
    return df


#### SEARCH TRENDING VENEUS
def venues_tre(latitude,longitude): # limit of number of venues returned by Foursquare API
    """ return the NAME,LOCATION,ID,CATAGORY of a trending venues """
    url = 'https://api.foursquare.com/v2/venues/trending?&client_id={}&client_secret={}&ll={},{}&v={}'.format(
        CLIENT_ID, 
        CLIENT_SECRET,  
        latitude, 
        longitude, 
        VERSION
        )
    results = requests.get(url).json()
    """If There is no trending Venue around Increase the radius of Search by 500 meter and search again.
    Repeat this process until you find a nearest Veneu"""
#     if len(results["response"]["venues"]) > 15 or radius > 10000:
    return results
#     else:
#         return venues_tre(latitude=latitude ,longitude=longitude , radius = radius+1000 )


def venues_tre_clean(res):
    df=json_normalize(res['response']['venues'])
    df=df[['id','name','categories','location.lat','location.lng','location.distance']]
    df.columns = [col.split(".")[-1] for col in df.columns]
    lis=[]
    for i in df['categories']:
        try:
            lis.append(i[0]['name'])
        except:
            lis.append("_")
    df["categories"]=lis
    df["rating"]=df["id"].apply(rating)
    return df


# ## FIND MY LOCATION 

# In[31]:


latitude,longitude = findmyLocation()                  # Find the Location of Added Address
mapo=folium.Map(location=[latitude,longitude],zoom_start=13,tiles='Stamen Terrain') # Its Blank Canvass of Map
folium.Marker(location=[latitude,longitude],popup="Estimated Location",tooltip="Your Location",icon=folium.CustomIcon(icon_image="C:/Users/Abdul Rehman/Myloc.gif")).add_to(mapo)
mapo


# ## FIND A LOCATION

# In[38]:


latitude,longitude = findlocation()                  # Find the Location of Added Address
mapobj1=folium.Map(location=[latitude,longitude],zoom_start=14) # Its Blank Canvass of Map
folium.Marker(location=[latitude,longitude],popup="Estimated Location",tooltip="Added Location",icon=folium.CustomIcon(icon_image="C:/Users/Abdul Rehman/loc.gif")).add_to(mapobj1)
mapobj1


# ## FIND High Rated VENUES AROUND

# In[39]:


res                = venues(latitude,longitude)      # Find the venues around that Blue Area Islamabd (Entered Location)  
data_df            = venues_clean(res)               # Clean the Data 


# In[40]:


data_df                                             # Show the data


# In[41]:


## Plotting these Venues 
for lat, lng, name, categories,distance,col in zip(data_df['lat'], data_df['lng'], data_df['name'], data_df['categories'],data_df['distance'],data_df['rating']):
    label = '{}, {}'.format(name, categories)
    folium.CircleMarker(
        [lat, lng],
        radius=6,
        tooltip=label,
        popup=str(distance)+"m away",
        color=col,
        fill=True,
        fill_color=col,
        fill_opacity=0.5).add_to(mapobj1)  
folium.TileLayer('openstreetmap',).add_to(mapobj1)
mapobj1


# ## SEARCH VENUES OF A CATAGORY 
# We can add more catagories from **Here** https://developer.foursquare.com/docs/build-with-foursquare/categories/

# In[42]:


search_query=input("Please Enter any of these \n Arts & Entertainment \n Museum \n Music Venue \n Stadium \n College & University \n Food \n Medical Center \n ")
res                = venues_cat(latitude,longitude,search_query)      # Find the venues of that catagory 
data_df            = venues_cat_clean(res)                            # Clean the Data 


# In[43]:


data_df


# In[44]:


mapobj1=folium.Map(location=[latitude,longitude],zoom_start=14) # Its Blank Canvass of Map
folium.Marker(location=[latitude,longitude],popup="Estimated Location",tooltip="Added Location",icon=folium.CustomIcon(icon_image="C:/Users/Abdul Rehman/loc.gif")).add_to(mapobj1)
for lat, lng, name, categories,distance,col in zip(data_df['lat'], data_df['lng'], data_df['name'], data_df['categories'],data_df['distance'],data_df['rating']):
    label = '{}, {}'.format(name, categories)
    folium.CircleMarker(
        [lat, lng],
        radius=6,
        tooltip=label,
        popup=str(distance)+"m away",
        color=col,
        fill=True,
        fill_color=col,
        fill_opacity=0.5).add_to(mapobj1)  
folium.TileLayer('openstreetmap',).add_to(mapobj1)
mapobj1


# ## Search for Trending Venues Around 

# In[45]:


res                = venues_tre(latitude,longitude)      # Find the venues trending
mapobj1=folium.Map(location=[latitude,longitude],zoom_start=14) # Its Blank Canvass of Map
folium.Marker(location=[latitude,longitude],popup="Estimated Location",tooltip="Added Location",icon=folium.CustomIcon(icon_image="C:/Users/Abdul Rehman/loc.gif")).add_to(mapobj1)

try:
    data_df            = venues_tre_clean(res)                            # Clean the Data 
    for lat, lng, name, categories,distance,col in zip(data_df['lat'], data_df['lng'], data_df['name'], data_df['categories'],data_df['distance'],data_df['rating']):
        label = '{}, {}'.format(name, categories)
        folium.CircleMarker(
        [lat, lng],
        radius=6,
        tooltip=label,
        popup=str(distance)+"m away",
        color=col,
        fill=True,
        fill_color=col,
        fill_opacity=0.5).add_to(mapobj1)  
    folium.TileLayer('openstreetmap',).add_to(mapobj1)
except:
    print("Sorry 😐! There is No trending Venue Around You\nTry other ways")
mapobj1


# ## THANK YOU!
