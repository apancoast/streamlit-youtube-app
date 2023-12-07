import json
import pandas as pd
import streamlit as st

def extract_data_from_element(element):
    og_title = element['title']
    datetime = element['time']
    
    if og_title == 'Answered survey question':
        return og_title, 'From Google Ads', None, None, None, None
    
    if og_title == 'Watched a video that has been removed':
        return og_title, 'No', None, None, None, None
    
    if og_title.startswith('Visited'):
        return 'Visted Ad', 'From Google Ads', None, None, None, None
    
    if og_title.startswith('Watched'):
        title = og_title[len('Watched '):]
        vid_link = element['titleUrl']
        ad = 'From Google Ads' if 'details' in element else 'No'
        
        subtitles = element.get('subtitles', [])
        if subtitles:
            subtitle = subtitles[0]
            channel = subtitle.get('name')
            channel_link = subtitle.get('url')
            return title, ad, vid_link, channel, channel_link, datetime
    
    return None, None, None, None, None, None

def process_file(uploaded_file):
    file_contents = uploaded_file.read()

    titles = []
    vid_links = []
    channels = []
    channel_links = []
    datetimes = []
    ads = []

    json_data = json.loads(file_contents)
    for element in json_data:
        if element['time'].startswith('2023'):
            (
                title,
                ad,
                vid_link,
                channel,
                channel_link,
                datetime
            ) = extract_data_from_element(element)
            
            if title is None:
                continue
            
            titles.append(title)
            vid_links.append(vid_link)
            channels.append(channel)
            channel_links.append(channel_link)
            datetimes.append(datetime)
            ads.append(ad)
        else:
            break

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

def main():
    st.title("YouTube History Parser")
    uploaded_file = st.file_uploader("Upload a JSON file", type=['json'])

    if uploaded_file is not None:
        try:
            history_df = process_file(uploaded_file)
            no_dups = history_df.drop_duplicates(subset='vid_url')
            no_ads = no_dups[no_dups['ad'] == 'No']
            top_5_df = no_ads['channel'].value_counts().head(5).reset_index().rename(columns={'index': 'channel', 'channel': 'counts'})
            top_5_df = pd.merge(top_5_df, history_df[['channel', 'channel_url']], on='channel', how='left').drop_duplicates().reset_index(drop=True)
            st.dataframe(top_5_df)
        except (json.JSONDecodeError, KeyError) as e:
            st.error("Error processing the file. Please make sure it's a valid JSON file.")

if __name__ == "__main__":
    main()
