import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import math
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

import json
import os
import argparse
import sys

import requests
import urllib
import urllib3
from urllib3.exceptions import InsecureRequestWarning

import datetime
import time
from PIL import Image
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
geolocator = Nominatim(user_agent="kirt.raynes@obf.ateneo.edu")

path = os.getcwd()
if not os.path.exists(path+'\\Pictures'):
    os.makedirs(path + '\\Pictures')
    st.write('path created')
st.write(path)
@st.cache
##################################################################################################################
def read_data(file):
        return pd.read_csv(file,low_memory=False)
##################################################################################################################
df = read_data('BABY2.csv')
df = df.set_index('Museum ID')
df['Income'] = pd.to_numeric(df['Income'],errors='coerce')
df['State Code (FIPS)'] = pd.to_numeric(df['State Code (FIPS)'], errors='coerce')
##################################################################################################################

##################################################################################################################
us_state_abbrev = {
    'Alabama': 1,
    'Alaska': 2,
    'American Samoa': 60,
    'Arizona': 4,
    'Arkansas': 5,
    'California': 6,
    'Colorado': 7,
    'Connecticut': 8,
    'Delaware': 9,
    'District of Columbia': 10,
    'Florida': 12,
    'Georgia': 13,
    'Guam': 13,
    'Hawaii': 15,
    'Idaho': 16,
    'Illinois': 17,
    'Indiana': 18,
    'Iowa': 19,
    'Kansas': 20,
    'Kentucky': 21,
    'Louisiana': 22,
    'Maine': 23,
    'Maryland': 24,
    'Massachusetts': 25,
    'Michigan': 26,
    'Minnesota': 27,
    'Mississippi': 28,
    'Missouri': 29,
    'Montana': 30,
    'Nebraska': 31,
    'Nevada': 32,
    'New Hampshire': 33,
    'New Jersey': 34,
    'New Mexico':35,
    'New York': 36,
    'North Carolina': 37,
    'North Dakota': 38,
    'Northern Mariana Islands':69,
    'Ohio': 39,
    'Oklahoma': 40,
    'Oregon': 41,
    'Pennsylvania': 42,
    'Puerto Rico': 72,
    'Rhode Island': 44,
    'South Carolina': 45,
    'South Dakota': 46,
    'Tennessee': 47,
    'Texas': 48,
    'Utah': 49,
    'Vermont': 50,
    'Virgin Islands': 78,
    'Virginia': 51,
    'Washington': 53,
    'West Virginia': 54,
    'Wisconsin': 55,
    'Wyoming': 56
}
us_state_abbrev_rev = {v: k for k, v in us_state_abbrev.items()}
types = df['Museum Type'].unique().tolist()
states = list(us_state_abbrev.keys())
chromedriver = 'chromedriver.exe'
##################################################################################################################
def get_image(a):
    searchword1 = a
    searchurl = 'https://www.google.com/search?q=' + searchword1+' Building HD' +'&source=lnms&tbm=isch'
    dirs = path + '\\Pictures'
    maxcount = 10

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')

    try:
        browser = webdriver.Chrome(chromedriver, options=options)
    except Exception as e:
        print(f'Chromedriver not found')
        print(f'Install on your machine. exception: {e}')
        sys.exit()
    browser.set_window_size(1280, 1024)
    browser.get(searchurl)
    time.sleep(1)
    element = browser.find_element_by_tag_name('body')
    
    page_source = browser.page_source 
    soup = BeautifulSoup(page_source, 'lxml')
    images = soup.findAll('img')
    urls = []
    for image in images:
        try:
            url = image['data-src']
            if not url.find('https://'):
                urls.append(url)
        except:
            try:
                url = image['src']
                if not url.find('https://'):
                    urls.append(image['src'])
            except Exception as e:
                print(f'Cant find image source')
                print(e)
    count = 0
    if urls:
        for url in urls:
            try:
                print(url)
                file = 'img_' + str(count) + '.jpg'
                res = requests.get(url, verify=False, stream=True)
                rawdata = res.raw.read()
                with open(os.path.join(dirs, file), 'wb') as f:
                    f.write(rawdata)
                    count += 1
                    break
            except Exception as e:
                break
    browser.close()
    return file
##################################################################################################################
def  reassign_address(a,b):
    seven = df[(df['Museum Type'] == a) & (df['State Code (FIPS)'] == b)].loc[:,['Museum Name','Street Address (Physical Location)','State Code (FIPS)','Latitude','Longitude']]
    for i in seven.index:
        try:
            string = str(seven.loc[i,'Latitude']) + ', ' +str(seven.loc[i,'Longitude'])
            location = geolocator.reverse(string,language='en')
            if seven.loc[i, 'State Code (FIPS)'] != us_state_abbrev[location.raw['address']['state']]:
                seven.loc[i, 'State Code (FIPS)'] = us_state_abbrev[location.raw['address']['state']]
        except ValueError as error_message:
            continue
    return seven
##################################################################################################################
def filter_data(b):
    return seven[(seven['State Code (FIPS)'] == b)].loc[:,['Museum Name','Street Address (Physical Location)','Latitude','Longitude']]
##################################################################################################################
def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dist_lat1 = lat1*np.pi/180
    dist_lat2 = (lat2)*np.pi/180
    dlat = (lat2-lat1)*np.pi/180
    dlon = (lon2-lon1)*np.pi/180
    a = np.sin(dlat/2)**2 + np.cos(dist_lat1) * np.cos(dist_lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    d = R * c
    return d
##################################################################################################################

side = st.sidebar.selectbox('Select Audience mode',['Visitor','Investor'])

if side == 'Visitor':
    filelist = [ f for f in os.listdir(path + '\Pictures') if f.endswith(".jpg") ]
    if  filelist:
        for f in filelist:
            os.remove(os.path.join(path + '\Pictures', f))
    em = pd.DataFrame()
    st.title('Hi! What museum do you want to visit?')
    st.header('Please input your preference')
    st.subheader('We will list down the nearest museums to your location')
    selection = st.multiselect('Museum Type',types)
    selection1 = st.multiselect('State', states)
    top = st.slider('Display the top:',1, 10,step=1)
    
    user_input = st.text_input('Where are you right now?','107 Albany Ave, Brooklyn, NY 11213, USA')      
    start = st.button('Search')
    if start:
        c = Nominatim(user_agent="kirt.raynes@obf.ateneo.edu").geocode(user_input).latitude
        c1 = Nominatim(user_agent="kirt.raynes@obf.ateneo.edu").geocode(user_input).longitude
        st.write('Found you at', c, ', ',c1)
        for i in selection:
            for j in selection1:
                seven = reassign_address(i,us_state_abbrev[j])
                prim = filter_data(us_state_abbrev[j])
                em = em.append(prim)
        em['Distance (KM)'] = distance(c,c1,em['Latitude'],em['Longitude'])
        az = em.sort_values(by='Distance (KM)', ascending=True).head(top)
        for i in az.index:
            try:
                string = str(az.loc[i,'Latitude']) + ', ' +str(az.loc[i,'Longitude'])
                location = geolocator.reverse(string,language='en')
                az.loc[i,'Street Address (Physical Location)'] =  location.address
            except ValueError:
                continue
        map_lati = az.head(top)['Latitude']
        map_longi = az.head(top)['Longitude']
        map_data = pd.merge(map_lati, map_longi, right_index=True, left_index=True)
        map_data.columns=['lat','lon']
        st.map(map_data) #very simple map 
        for i in az.index:
            k = get_image(az.loc[i,'Museum Name'])
            pic = (path + "\\Pictures\\" + k)
            st.image(Image.open(pic))
            st.markdown(f"<div class ='alert alert-block alert-info'><p><b>Museum Name: </b>{az.loc[i,'Museum Name']}</p><p><b>Address: </b>{az.loc[i,'Street Address (Physical Location)']}</p><p><b>Distance:</b> {az.loc[i,'Distance (KM)']:.2f} KM</p></div>", unsafe_allow_html=True)
elif side == 'Investor':
    st.title('Welcome to Investor Mode')
    st.header('Kindly drag the slidebar to your desired income')    
    left_income, right_income = st.slider('Slider for Income', min_value = 0.0, max_value = max(df['Income']), step = 1.0, value = (0.0,1000000.0))
    top = st.slider('Display the top:',1, 10,step=1)
    st.dataframe(df[(df['Income'] >= left_income) & (df['Income'] < right_income)].head(top))
    
    
    
