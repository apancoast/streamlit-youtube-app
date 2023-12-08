import streamlit as st
import pandas as pd
import json
import requests
import re
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import os
import tempfile

# @st.cache(allow_output_mutation=True)

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
    
    no_dups = history_df.drop_duplicates(subset='vid_url')

    # Unlikely a concern, but we'll remove ads just in case. Not going to catch ads that are from unlisted videos on brand channels
    no_ads = no_dups[no_dups['ad'] == 'No']

    # let's finally get those top channels
    top_5_df = no_ads[['channel', 'channel_url']].value_counts().sort_values(ascending=False).head(5).reset_index().rename(columns={0: 'counts'})

    return top_5_df

def create_image(background_image, dataframe):
    if background_image == 1:
        background_image_url = 'https://raw.githubusercontent.com/apancoast/youtube_top_channels/main/background_images/1.jpg'
        fill_color = (0, 0, 0)  # Black
    else:
        background_image_url = 'https://raw.githubusercontent.com/apancoast/youtube_top_channels/main/background_images/2.jpg'
        fill_color = (255, 255, 255)

    # Image dimensions
    image_width = 240
    image_height = 240

    # Font sizes
    font_size_large = 50
    font_size_small = 40
    title_font_size = 90
    number_font_size = 100
    
    # Font faces
    lgt_url = "https://github.com/apancoast/youtube_top_channels/raw/main/fonts/youtube-sans-light.ttf"
    lgt_response = requests.get(lgt_url)

    # Create temporary files to store the fonts
    with tempfile.NamedTemporaryFile(delete=False) as lgt_temp_file:
        lgt_temp_file.write(lgt_response.content)
        lgt_temp_path = lgt_temp_file.name
        
    med_url = "https://github.com/apancoast/youtube_top_channels/raw/main/fonts/youtube-sans-medium.ttf"
    med_response = requests.get(med_url)

    # Create temporary files to store the fonts
    with tempfile.NamedTemporaryFile(delete=False) as med_temp_file:
        med_temp_file.write(med_response.content)
        med_temp_path = med_temp_file.name 
    
    bold_url = "https://github.com/apancoast/youtube_top_channels/raw/main/fonts/youtube-sans-bold.ttf"
    bold_response = requests.get(bold_url)

    # Create temporary files to store the fonts
    with tempfile.NamedTemporaryFile(delete=False) as bold_temp_file:
        bold_temp_file.write(bold_response.content)
        bold_temp_path = bold_temp_file.name

    # Load fonts
    channel_font = ImageFont.truetype(font=lgt_temp_path, size=font_size_large)
    watched_font = ImageFont.truetype(font=lgt_temp_path, size=font_size_small)
    title_font = ImageFont.truetype(font=med_temp_path, size=title_font_size)
    number_font = ImageFont.truetype(font=bold_temp_path, size=number_font_size)

    # Load background image from URL
    response = requests.get(background_image_url)
    background_image = Image.open(BytesIO(response.content))

    # Starting coordinates
    x_offset = 125
    y_offset = 300
    
    # Iterate over top_5 DataFrame
    for index, row in dataframe.iterrows():
        channel = row['channel']
        url = row['channel_url']
        count = row['count']

        response = requests.get(url)
        html_content = response.content.decode('utf-8')

        # Find the meta tag containing og:title and the associated image link
        pattern = r'<meta property="og:title" content=".*?"><link rel="image_src" href="(.*?)">'
        match = re.search(pattern, html_content)

        if match:
            image_link = match.group(1)
            # Download the image
            image_response = requests.get(image_link)
            try:
                # Save the image temporarily
                with open('temp_image.jpg', 'wb') as f:
                    f.write(image_response.content)
                image_path = 'temp_image.jpg'
                
                # Load and resize the image
                image = Image.open(image_path).resize((image_width, image_height))
                
                # Add title text
                title_text = "My Top YouTube Channels"
                title_text_position = (55, 150)
                draw = ImageDraw.Draw(background_image)
                draw.text(title_text_position, title_text, font=title_font, fill=fill_color)

                # Draw number text
                number_text = str(index + 1)
                number_text_position = (x_offset, y_offset)
                draw.text(number_text_position, number_text, font=number_font, fill=fill_color)

                # Paste the image on the background image
                background_image.paste(image, (x_offset + number_font_size, y_offset))

                # Draw channel text
                channel_text = channel
                channel_text_position = (x_offset + image_width + 135, y_offset)
                draw.text(channel_text_position, channel_text, font=channel_font, fill=fill_color)

                # Draw count text
                count_text = f'{count} videos watched'
                count_text_position = (x_offset + image_width + 135, channel_text_position[1] + font_size_large)
                draw.text(count_text_position, count_text, font=watched_font, fill=fill_color)

                # Add subtext
                subtext = "coded by github.com/apancoast".upper()
                subtext_position = (450, background_image.height - 150)
                draw.text(subtext_position, subtext, font=watched_font, fill=fill_color)
                
                # Delete the temporary image file
                os.remove(image_path)

                y_offset += 280
            except Exception as e:
                print(f'Error processing image from {image_path}: {str(e)}')
        else:
            print(f'Image link not found in the HTML content of {url}')

    # Save the final image
    output_path = 'result_image.jpg'
    background_image.save(output_path)
    
    return st.image(background_image, caption='Results! Right click the image to download.')

def get_channel_links(dataframe):
    global df
    df_new = pd.DataFrame({
        'col1':[1,2],
        'col3':["X","Y"]
    })
    df.drop(['col2'], axis = 1, inplace = True)
    st.session_state.df = df.merge(df_new, on="col1")


# Streamlit app
def main():
    st.title("Discover Your Top YouTube Channels")
    st.write('This app reads your YouTube watch history JSON file (available via [Google Takeout](https://takeout.google.com/)), returns your top five channels with video counts, and generates an image with the results. If you have any issues, please feel free to contact me at pancoastashley@gmail.com.')

    st.subheader('Upload your watch history JSON to get started.')
                
    uploaded_file = st.file_uploader("Upload a JSON file", type=['json'])

    if uploaded_file is not None:
        top_5_df = process_file(uploaded_file)

        st.subheader("Your Top Channels")
        st.dataframe(top_5_df, hide_index=True, column_order=('channel', 'count'))
        
        st.subheader("Choose a background image")
        col1, col2 = st.columns(2)
        with col1:
            st.image('https://raw.githubusercontent.com/apancoast/youtube_top_channels/main/background_images/1.jpg', width=100, caption='Background 1')
            bg1 = st.button('Choose Background 1')
        with col2:
            st.image('https://raw.githubusercontent.com/apancoast/youtube_top_channels/main/background_images/2.jpg', width=100, caption='Background 2')
            bg2 = st.button('Choose Background 2')

        if bg1:
            create_image(1, top_5_df)
        elif bg2:
            create_image(2, top_5_df)
        else:
            st.write('Select a background image for your top channel display.')
        
if __name__ == "__main__":
    main()
