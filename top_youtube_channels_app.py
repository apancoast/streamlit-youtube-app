import streamlit as st
import pandas as pd
import json
import requests
import re
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import os

# Function to process the uploaded file
def process_file(uploaded_file):
    # Read the uploaded file
    file_contents = uploaded_file.read()

    # Initialize empty lists to store extracted data
    titles = []
    vid_links = []
    channels = []
    channel_links = []
    datetimes = []
    ads = []

    # Retrieve data from JSON
    json_data = json.loads(file_contents)
    for element in json_data:
        datetime = element['time']
        if datetime.startswith('2023'):
            og_title = element['title']
            title = None
            vid_link = None
            channel = None
            channel_link = None
            ad = None
            
            if og_title == 'Answered survey question':
                title = og_title
                ad = 'From Google Ads'
                
            elif og_title == 'Watched a video that has been removed':
                title = og_title
                ad = 'No'
            
            elif og_title.startswith('Visited'):
                title = 'Visted Ad'
                ad = 'From Google Ads'
            
            elif og_title.startswith('Watched'):
                title = og_title[len('Watched '):]
                vid_link = element['titleUrl']
                ad = 'From Google Ads' if 'details' in element else 'No'
                
                subtitles = element.get('subtitles', [])
                if subtitles:
                    subtitle = subtitles[0]
                    channel = subtitle.get('name')
                    channel_link = subtitle.get('url')
                else:
                    continue
                
            else:
                continue
            
        else:
            break

        # Append extracted data to respective lists
        titles.append(title)
        vid_links.append(vid_link)
        channels.append(channel)
        channel_links.append(channel_link)
        datetimes.append(datetime)
        ads.append(ad)

    # Create a Pandas DataFrame from the extracted data
    data = {
        'title': titles,
        'vid_url': vid_links,
        'channel': channels,
        'channel_url': channel_links,
        'datetime': datetimes,
        'ad': ads
    }
    history_df = pd.DataFrame(data)
    return history_df

# Streamlit app
def main():
    st.title("YouTube History Parser")
    uploaded_file = st.file_uploader("Upload a JSON file", type=['json'])

    if uploaded_file is not None:
        df = process_file(uploaded_file)
        st.dataframe(df.head())

if __name__ == "__main__":
    main()
