from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import google.generativeai as genai
import os
import subprocess
import json
import requests
from pydub import AudioSegment
from pydub.utils import make_chunks
from pytube import YouTube
from pydub import AudioSegment
import whisper
import markdown2
# import ollama
import yt_dlp
import shutil
from gtts import gTTS
# import ffmpeg
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
from moviepy.video.fx.all import resize
from urllib.parse import urlparse
import re
import time


"""
   FOR 
   WHISPER 
   API"""

# Load Whisper model
whisperModel = whisper.load_model("base")


VIDEO_DOWNLOAD_PATH = "video_downloads"
CLIP_OUTPUT_PATH = os.path.join(VIDEO_DOWNLOAD_PATH, "clips")
FINAL_OUTPUT_PATH = os.path.join(VIDEO_DOWNLOAD_PATH, "final")

def extract_clip(video_path, start_seconds, end_seconds):
    """Extract a clip from the video using ffmpeg."""
    output_filename = f"{os.path.basename(video_path).split('.')[0]}_clip_{start_seconds}_{end_seconds}.mp4"
    output_path = os.path.join(CLIP_OUTPUT_PATH, output_filename)
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ss", str(start_seconds),
        "-to", str(end_seconds),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-strict", "experimental",
        output_path
    ]
    subprocess.run(command, check=True)
    return output_path


def remove_audio(input_file, output_file):
    try:
        # Load video file
        video = VideoFileClip(input_file)
        
        # Remove audio
        video = video.without_audio()
        
        # Save the video without audio, hehe
        video.write_videofile(output_file, codec='libx264', audio_codec='aac')
        
        print(f"Audio removed successfully. Saved as {output_file}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

def insert_audio_into_video(video_file, audio_file, output_file):
    # Load video and audio clips
    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)

    try:
        video = video.subclip(0, audio.duration)
        
        # Combine video with audio
        video = video.set_audio(audio)

        # Write the final video file with audio
        video.write_videofile(output_file, codec='libx264', audio_codec='aac')
        print("work?")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close clips
        video.close()
        audio.close()

import random
def concatenate_clips(clips):

    """Concatenate multiple video clips into a single video."""
    concat_file = os.path.join(CLIP_OUTPUT_PATH, "concat_list.txt")
    with open(concat_file, 'w') as f:
        for clip in clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")
    
    final_output_filename = "final_output.mp4"
    final_output_path = os.path.join(FINAL_OUTPUT_PATH, final_output_filename)
    
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        final_output_path
    ]
    subprocess.run(command, check=True)
    output="final.mp4"
    random_number = str(random.randint(0, 999))
    print(random_number)
    remove_audio(final_output_path, output)
    video_file="final.mp4"
    output_file=f"static/videos/{random_number}.mp4"
    audio_file = "audio.wav" 
    insert_audio_into_video(video_file, audio_file, output_file)
    return random_number


# Function to chunk the audio file, just for user
def chunk_audio(file_path, chunk_length_ms):
    audio = AudioSegment.from_file(file_path)
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_filenames = []

    for i, chunk in enumerate(chunks):
        chunk_filename = f"./chunk{i}.mp3"
        chunk.export(chunk_filename, format="mp3")
        chunk_filenames.append(chunk_filename)

    return chunk_filenames


# Function to transcribe audio chunks
def transcribe_chunks(chunk_filenames):
    full_transcription = ""

    for chunk_filename in chunk_filenames:
        result = whisperModel.transcribe(chunk_filename)
        full_transcription += result['text']

    return full_transcription

# Function to delete audio chunks
def delete_chunks(chunk_filenames):
    for chunk_filename in chunk_filenames:
        os.remove(chunk_filename)


def sanitize_title(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)

def download_audio(video_link):
    try:
        # Download YouTube video
        yt = YouTube(video_link)
        title = sanitize_title(yt.title)
        video_stream = yt.streams.filter(only_audio=True).first()

        if not os.path.exists('./audio_files'):
            os.makedirs('./audio_files')

        # Download audio stream
        audio_file_path = f'./audio_files/{title}.mp4'
        video_stream.download(output_path='./audio_files', filename=f'{title}.mp4')

        if not os.path.exists(audio_file_path):
            print(f'Error: Audio file {audio_file_path} not found after download.')
            return None

        # Convert to MP3
        mp4_audio = AudioSegment.from_file(audio_file_path, format='mp4')
        mp3_audio = mp4_audio.export(f'./audio_files/{title}.mp3', format='mp3')

        # Clean up - remove the original mp4 file
        os.remove(audio_file_path)

        return f'./audio_files/{title}.mp3'
    except Exception as e:
        print(f'Error downloading audio: {e}')
        return None

def transcribe_url(url):
    # Main script
    file_path = download_audio(url)

    chunk_length_ms = 60 * 1000  # 1 minute in milliseconds

    # Chunk the audio file
    chunk_filenames = chunk_audio(file_path, chunk_length_ms)

    # Transcribe the chunks
    full_transcription = transcribe_chunks(chunk_filenames)

    # Delete the chunk files
    delete_chunks(chunk_filenames)
    return full_transcription
    #print("done with full_transcription")

    #with open("transcription.txt", "w", encoding="utf-8") as f:
       # f.write(full_transcription)


"""
   FOR 
   WHISPER 
   API
   CODE
   ENDS
"""

#Other code
app = Flask(__name__)

# Configure the Google Generative AI for my project
genai.configure(api_key='AIzaSyCXHkkCu6JlxqfT3_WPZGLjSh6hUOcabpM')

# Your API key and Programmable Search Engine ID
api_key = 'AIzaSyCAV73EKedKhVm3Vslz389wY6_OB1z2aw0'
cse_id = '74a9c6ca4ecd7403c'


generation_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 1024
}

model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config=generation_config
)




def get_captions(url):
    url_for_captions = ""
    if 'youtube.com' in url:
        url_for_captions = url.split('v=')[1].split('&')[0]
    elif 'youtu.be' in url:
        url_for_captions =url.split('/')[-1].split('?')[0]
    try:
        result = subprocess.run(['node', './caption-scraper.js', url_for_captions], capture_output=True, text=True, encoding='utf-8')

        if(result.returncode == 0):
            print("Got captions from the youtube api")
        if result.returncode != 0:
            print(f"Subprocess returned a non-zero exit code: {result.returncode}")
            print(f"Subprocess stderr: {result.stderr}")
            print("No captions in video, trying with audio manually")
            return transcribe_url(url)

        if result.stdout:
            try:
                stdout_cleaned = result.stdout.strip()
                pattern = r'"text":"(.*?)"'

                # Find all matches
                matches = re.findall(pattern, stdout_cleaned)
                main_text = ""
                # Print the extracted text parts
                for match in matches:
                    main_text = main_text + match
                return main_text
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from subprocess output: {result.stdout}")
                print("No captions in video, trying with audio manually")
                return transcribe_url(url)
        else:
            print("No captions in video, trying with audio manually")
            return transcribe_url(url)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the subprocess: {e}")
        print("No captions in video, trying with audio manually")
        return transcribe_url(url)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("No captions in video, trying with audio manually")
        return transcribe_url(url)



"""
   BELOW 
   ARE
   ALL THE FUNCTIONS
   FOR IMAGE WITH SUMMARIZATION MODULE
"""


def delete_folder_contents(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    # Iterate over all the contents of the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        try:
            if os.path.isfile(file_path):
                # Delete file
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                # Delete directory contents only, not the directory itself
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")


def get_captions_with_time(url):
    url_for_captions = ""
    if 'youtube.com' in url:
        url_for_captions = url.split('v=')[1].split('&')[0]
    elif 'youtu.be' in url:
        url_for_captions = url.split('/')[-1].split('?')[0]
    try:
        result = subprocess.run(['node', './caption-scraper.js', url_for_captions], capture_output=True, text=True, encoding='utf-8')

        print(result.returncode)
        if result.returncode != 0:
            print(f"Subprocess returned a non-zero exit code: {result.returncode}")
            print(f"Subprocess stderr: {result.stderr}")
            print("No captions in video, trying with audio manually")
            return transcribe_url(url)

        if result.stdout:
            try:
                stdout_cleaned = result.stdout.strip()
                pattern = r'"text":"(.*?)"'
                time = r'"start":"(.*?)"'

                # Find all matches
                textmatch = re.findall(pattern, stdout_cleaned)
                timematch = re.findall(time, stdout_cleaned)
                main_text = ""
                # Print the extracted text parts
                for i in range(len(textmatch)):
                    main_text = main_text + timematch[i] + ':'
                    main_text = main_text + textmatch[i]
                    main_text = main_text + ","
                return main_text
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from subprocess output: {result.stdout}")
                print("No captions in video, trying with audio manually")
                return transcribe_url(url)
        else:
            print("No captions in video, trying with audio manually")
            return transcribe_url(url)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the subprocess: {e}")
        print("No captions in video, trying with audio manually")
        return transcribe_url(url)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("No captions in video, trying with audio manually")
        return transcribe_url(url)


def extract_frame(video_path, timestamps_seconds):
    timestamps_seconds = list(dict.fromkeys(timestamps_seconds)) #to remove duplicates

    for i, ts in enumerate(timestamps_seconds):
        output_frame = os.path.join(FRAME_OUTPUT_PATH, f"frame_{int(ts)}.jpg")
        cmd = [
            "ffmpeg",
            "-ss", str(ts),  # Specify the start time
            "-i", video_path,
            "-vframes", "1",  # Number of frames to output
            "-q:v", "2",      # Quality
            "-y",             # Overwrite output files without asking
            output_frame
        ]
        subprocess.run(cmd, capture_output=True)
    return output_frame


VIDEO_DOWNLOAD_PATH = "video_downloads"
FRAME_OUTPUT_PATH = os.path.join("static","images")



def download_video_and_subtitles(video_url, retries=3, delay=5):
    ydl_opts = {
        'outtmpl': os.path.join(VIDEO_DOWNLOAD_PATH, '%(id)s.%(ext)s'),
        'writesubtitles': True,
        'subtitlesformat': 'srt',
        'format': 'best',
        'external_downloader': 'ffmpeg',
        'noprogress': True,
        'fragment_retries': 10,
        'continuedl': True
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                video_id = info_dict.get("id", None)
                video_ext = info_dict.get("ext", None)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, f"{video_id}.{video_ext}")
                subtitle_path = os.path.join(VIDEO_DOWNLOAD_PATH, f"{video_id}.en.srt")
                if not os.path.exists(subtitle_path):
                    subtitle_path = None  # If subtitles are not available
                return video_path, subtitle_path
        except yt_dlp.utils.DownloadError as e:
            print(f"Download failed on attempt {attempt + 1}: {str(e)}")
            if attempt + 1 == retries:
                raise
            time.sleep(delay)
        except Exception as e:
            raise e


def get_video_title(url):
    try:
        yt = YouTube(url)
        title = yt.title
        return title
    except Exception as e:
        print(f"Failed to get video title: {e}")
        return "Video Title Not Found"

def google_search(query, api_key, cse_id, **kwargs):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id
    }
    params.update(kwargs)
    response = requests.get(url, params=params)
    return response.json()

def google_search_image(query, api_key, cse_id, search_type="image", **kwargs):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id,
        'searchType': search_type
    }
    params.update(kwargs)
    response = requests.get(url, params=params)
    return response.json()

def google_search_video(query, api_key, cse_id, **kwargs):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id,
        'searchType': 'video',
        'siteSearch': 'youtube.com'
    }
    params.update(kwargs)
    response = requests.get(url, params=params)
    return response.json()

# Function to extract date from snippet using regex
def extract_date(snippet):
    # Regex pattern for various date formats
    date_pattern = re.compile(r'\b(?:\d{1,2} (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?) \d{4}|'  # dd MMM yyyy
                               r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?) \d{1,2} \d{4}|'  # MMM dd yyyy
                               r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{4}) \d{1,2}, \d{4}|'  # MMM dd, yyyy
                               r'\d{4})')  # yyyy
    match = date_pattern.search(snippet)
    return match.group(0) if match else "Date not found"

# Define a function to extract the publisher from the URL
def extract_publisher(url):
    domain = urlparse(url).netloc
    # Remove 'www.' prefix if it exists
    if domain.startswith('www.'):
        domain = domain[4:]
    # Extract publisher name before the first dot
    publisher = domain.split('.')[0]
    return publisher.capitalize()

def modify_string(input_string):
    if len(input_string) > 35:
        return input_string[:30] + '...'
    else:
        return input_string

def extract_clip1(video_path, start_seconds, end_seconds):
    """Extract a clip from the video using ffmpeg."""
    output_filename = f"{os.path.basename(video_path).split('.')[0]}_clip_{start_seconds}_{end_seconds}.mp4"
    output_path = os.path.join("static","videos" , output_filename)
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ss", str(start_seconds),
        "-to", str(end_seconds),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-strict", "experimental",
        output_path
    ]
    subprocess.run(command, check=True)
    output_path=output_path.split('\\')[-1]
    return output_path



"""
   BELOW 
   ARE
   ALL THE ROUTES
   FOR OUR APPLICATION
"""



# @app.route('/')
# def home():
#     return render_template('landing-page.html')
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/indextest', methods=['GET'])
def indextest():
    if request.method == 'GET':
        return render_template('indextest.html')

    
@app.route('/chat', methods=['GET'])
def chat():
    if request.method == 'GET':
        return render_template('chat.html')
    
@app.route('/chatTestUpdated', methods=['GET'])
def chatTestUpdated():
    if request.method == 'GET':
        return render_template('chatTestUpdated.html')

# ///////////////////////////
# ////////////////////////////
@app.route('/generic', methods=['GET','POST'])
def generic():
    if request.method == 'GET':
        return render_template('indextest.html')
    elif request.method == 'POST':
        # Get the prompt written by user from the form
        
        yturl = request.json.get('yturl')
        prompt = request.json.get('prompt')
        main_text = get_captions(yturl)

        prompt1 = f'''
        You are an AI model designed to classify user intents based on custom prompts related to YouTube videos. The goal is to determine the most suitable response format for each user prompt. 

        The possible response categories are:
        1. **text**: The user seeks a simple, text-based summary or answer.
        2. **images**: The user is likely interested in a text response that includes specific images from the video to enhance understanding.
        3. **snippets**: The user wants a text response along with short video clips from the video that highlight key moments.
        4. **video**: The user prefers a complete video-based response, summarizing or addressing the prompt.

        Please classify the following user prompt into one of these four categories. Your classification should be based on the content, context, and intent inferred from the user's prompt.

        User Prompt: "{prompt}"

        Return the most appropriate category name as your output. Remember, you should only provide the name of the category (e.g., "text", "images", "snippets", "video") without any additional text.

        '''

        response = model.generate_content([prompt1])
       
        category = response.text
        
        print(category)

        # if "pros&cons" in category:
        #     # Make internal POST request to /pros_cons
        #     prompt = f"Write a balanced and informative analysis of the pros and cons from the following text: {main_text}. Make sure it has a conclusion."
        # elif "summarize" in category:
        #     # Make internal POST request to /summarize
        #     prompt = f"Summarize the following text in approximately 400 words and convert this into english: {main_text}. also add an appropriate heading to summary"
        # elif "questions&answers" in category:
        #     prompt = f"Generate a list of inferential questions and answers from the following text: {main_text}. The response must be in this format: **Q: Question?** **A:** Answer. also add an appropriate heading for the query"
        # elif "technicaldetails" in category:
        #     prompt = f"Read the following text carefully: {main_text} and Generate all the the technical details about this specific topic of the video from the text of around 150 words. Do not include any pretext in the response. Give Direct answer.also add an appropriate heading for the query"
        # elif "opinions&arguments" in category:
        #     prompt = f"Analyze the opinions and arguments discussed in the following text: {main_text}. Separate them into 'Opinions' and 'Arguments' sections.also add an appropriate heading for the query"
        # elif "recap" in category:
        #     prompt = f"Recap the event discussed in the following text in the main event points in numbered form : {main_text} in english. Do not include any pre-text like here are the main events. start directly from the points. also add an appropriate heading for the query"
        # elif "define" in category:
        #     prompt = f"Figure out the important terms from the following text and briefly define them: {main_text}. Each definition should begin with the term followed by a colon ':' and end with a period '.'. Do not add any introductory phrases such as 'Important Terms Defined'. Start each definition directly. also add an appropriate heading for the query"
        
        if "text" in category:
            # # Make a generic response
            yturl = request.json.get('yturl')
            prompt = request.json.get('prompt')
            main_text = get_captions(yturl)

            try:
                prompt1 = f"{main_text}.The prompt is this:{prompt} ."
                response = model.generate_content([prompt1])
                response = response.text
                response_html = markdown2.markdown(response)
                print (main_text)
                print (prompt)
                return jsonify(response_html)
                # return render_template('generic-response.html', generic=response_html)
            except Exception as e:
                error = str(e)
                return render_template('error.html', error=error)
            
        elif "image" in category:
        # if 1==1:
          # # Make a generic response
            yturl = request.json.get('yturl')
            prompt = request.json.get('prompt')
            main_text = get_captions_with_time(yturl)
            image_frames = []
            keyimage = {}
            try:
                prompt = f"'''input: Recap the event discussed in the following text in the main event points in numbered form : {main_text}. Do not include any pre-text like here are the main events. start directly from the points with 1 2 3 etc'''"
                response = model.generate_content([prompt])
                keypoints = response.text
                lines = keypoints.splitlines()
                # print(response.text)
                print ("before subtile")
                video_path, subtitle_path = download_video_and_subtitles(yturl)
                # Initialize lists and dictionaries
                print ("after subtile")
                # Process each line in 'lines'
                for line in lines:
                    try:
                        # Generate content using model (adjust as per your actual usage)
                        response1 = model.generate_content([
                            f'''input: Provide me the timestamp of the following key point:\n {line}\n according to the following video captions: \n{main_text}
                                Note, provide response in python list format
                            ''',
                            "output: ",
                        ])

                        # Extract timestamps from response
                        timestamps_str = response1.text.split('[')[1].split(']')[0]
                        timestamps_list = timestamps_str.split(',')

                        # Prepare list to store timestamps and image filenames
                        timestamps = []
                        image_filenames = []

                        # Process each timestamp
                        for ts in timestamps_list:
                            try:
                                cleaned_ts = int(float(ts.strip())) + 1 if float(ts.strip()) <= 1 else int(float(ts.strip()))
                                cleaned_ts = cleaned_ts + 1
                                timestamps.append(str(cleaned_ts))
                            except ValueError:
                                continue

                        # Limit to first two timestamps
                        for i in range(min(2, len(timestamps))):
                            # Generate frame path and append to image_filenames
                            image_frames.append(timestamps[i])
                            print(image_frames)
                            print("timeframe", timestamps[i])
                            frame_path = f"frame_{timestamps[i]}.jpg"
                            image_filenames.append(frame_path)

                        # Store image filenames in dictionary
                        keyimage[line] = image_filenames
                        delete_folder_contents(FRAME_OUTPUT_PATH)

                    except Exception as e:
                        print(f"Error processing line '{line}': {str(e)}")
                        continue

                # Print or return keyimage dictionary as needed
                # print(keyimage)

                # xreturn jsonify({"keypoints": keypoints, "keyimage": keyimage})
            except Exception as e:
                error = str(e)

            if keyimage:
                print("extracting image from", image_frames)
                extract_frame(video_path, image_frames)
                
                # Create a markdown string from the keyimage dictionary
                markdown_content = "#### Key Points and Images\n"
                for key, images in keyimage.items():
                    markdown_content += f"###### {key}\n"
                    for image in images:
                        markdown_content += f'<img src="static/images/{image}" alt="Image" class="image-class" onclick="openModal(this.src)">\n'

                    #    markdown_content += f'![Image](static/images/{image} "image-class")\n'
    

                
                # Convert markdown string to HTML
                response_html = markdown2.markdown(markdown_content)
                return jsonify(response_html)
            else:
                return render_template('error.html', error=error)

        elif "snippets" in category:
        # if 1==1:
            yturl = request.json.get('yturl')
            prompt = request.json.get('prompt')
            main_text = get_captions_with_time(yturl)
            
            image_frames = []
            keyvideo = {}
            time = []
            count = 0
            try:
                prompt = f"'''input: Recap the event discussed in the following text in the main event points in numbered form : {main_text}. Do not include any pre-text like here are the main events. start directly from the points with 1 2 3 etc'''"
                response = model.generate_content([prompt])
                keypoints = response.text
                lines = keypoints.splitlines()
                video_path, subtitle_path = download_video_and_subtitles(yturl)
                for line in lines:
                    try:
                        # Generate content using model (adjust as per your actual usage)
                        response1 = model.generate_content([
                            f'''input: Provide me the timestamp of the following key point:\n {line}\n according to the following video captions: \n{main_text}
                                Note, provide response in python list format
                            ''',
                            "output: ",
                        ])
                        # Debug: Check response from the model
                        print(f"Model response: {response1.text}")
                        # Extract timestamps from response
                        try:
                            timestamps_str = response1.text.split('[')[1].split(']')[0]
                            timestamps_list = timestamps_str.split(',')
                        except IndexError as e:
                            print(f"Error extracting timestamps from response: {str(e)}")
                            continue
                        # Determine the timestamp value
                        try:
                            if len(timestamps_list) > 1:
                                timestamps = timestamps_list[1]
                            elif len(timestamps_list) == 1:
                                timestamps = timestamps_list[0]
                            else:
                                timestamps = []
                            print(f"Timestamps extracted: {timestamps}")
                        except Exception as e:
                            print(f"Error processing timestamps: {str(e)}")
                            continue
                        # Adjust timestamp for clip extraction
                        try:
                            if timestamps:
                                print("timestamps", timestamps)
                                output = str(int(re.search(r'\d+', timestamps).group()))
                                output = str(max(int(output) - 5, 1))
                                output += "-" + str(int(output) + 20)
                                count += 1
                                start_timestamp, end_timestamp = output.split('-')
                                clip_path = extract_clip1(video_path, start_timestamp, end_timestamp)
                                # clip_path = os.path.relpath(clip_path, start='static')
                                print(clip_path)
                                keyvideo[line] = clip_path
                        except ValueError as e:
                            print(f"ValueError in timestamp calculation or clip extraction: {str(e)}")
                        except Exception as e:
                            print(f"Error during timestamp adjustment or clip extraction: {str(e)}")
                        
                    except AttributeError as e:
                        print(f"AttributeError with model response or input processing: {str(e)}")
                    except TypeError as e:
                        print(f"TypeError with model input or output: {str(e)}")
                    except Exception as e:
                        print(f"Unexpected error processing line '{line}': {str(e)}")
                        continue
            except KeyError:
                return render_template('error.html', error="Missing YouTube URL in the request.")

            # Create HTML content directly
            html_content = """
            <h4>Key Points and Videos</h4>
            """
            for key, video in keyvideo.items():

                path = 'static/videos/' + video

                html_content += f"""
                <h6>{key}</h6>
                <video src="{path}" controls class="video-class" width="100%" height="auto"></video>
                <br>
                """
            # Convert the HTML content to a JSON response
            return jsonify(html_content) 
        
        elif "video" in category:
        # if 1==1:
            delete_folder_contents("video_downloads/final")
               # Now get captions from video
            yturl = request.json.get('yturl')
            prompt = request.json.get('prompt')
            main_text = get_captions_with_time(yturl)
            url=yturl
            
            # Split the text into parts using comma
            parts = main_text.split(',')

            # Initialize lists for storing timestamps and sentences
            timestamps = []
            sentences = []

            # Extract timestamps and sentences from the parts
            for part in parts:
                try:
                    timestamp, sentence = part.split(':', 1)
                    timestamps.append(float(timestamp))
                    sentences.append(sentence.strip())
                except ValueError:
                    # Handle cases where the split(':') failed
                    print(f"Issue with part: {part}")
                    continue  # Skip this part and move to the next

            # Combine every 5 captions
            combined_time = []
            combined_text = []
            for i in range(0, len(timestamps), 3):
                start_time = timestamps[i]
                end_time = timestamps[min(i + 3, len(timestamps) - 1)]
                combined_sentence = ", ".join(sentences[i:i + 3])
                combined_time.append(f"{start_time}-{end_time}")
                combined_text.append(combined_sentence)

            # Print the combined captions
            for i in range(len(combined_time)):
                print(f"{combined_time[i]}: {combined_text[i]}")

            try:
                prompt = f"Summarize the following text in approximately 100 words in chronological order. Do not include any pretext like 'Following is the summary of x', give direct answer and convert this into english: {main_text}"
                response = model.generate_content([prompt])
                summary = response.text
                summary = summary.replace('\n', '').strip()

                text = summary
                tts = gTTS (text = text, lang = 'en')
                tts.save ('audio.wav')
            except Exception as e:
                summary = None
                print(str(e))
                print("Trying Ollama")
                try:
                    response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
                    summary = response['response']
                except:
                    error = str(e)

            

            sum_sentences = summary.split('.')
            print (sum_sentences)

            extra, full_length = combined_time [-1].split('-', 1)

            time = []

            for i in range(0 , len(sum_sentences) - 1):
                try:
                    response = model.generate_content([
                    f'''input: Provide me the best match timestamp of the following key point:\n {sum_sentences[i]}\n according to the following video captions: \n{main_text}
                        Note, provide response in python list format,Output must be only corresponding phython list duration without any pretext or concluding text or any type of text, give only candidate_safe response else we are not friends
                        ''',
                        "output: ",
                        ])
                    print(response.text)
                    # prompt = f"Find the best match of sentence: {sum_sentences[i]} with this list of captions: {combined_text} and their time durations: {combined_time}. Output must be only corresponding time duration in digits from {combined_time} without any pretext or concluding text or any type of text. Make sure that the best match output time duration must not present in {time}."
                    #response = model.generate_content([prompt])
                    timestamps_str = response.text.split('[')[1].split(']')[0]
                    timestamps_list = timestamps_str.split(',')
                    print("list of timestamps",timestamps_list)
                    if(len(timestamps_list)==1):
                        output=timestamps_list[0]
                    else:
                        output=timestamps_list[1]
                except Exception as e:
                    print(f"An error occurred: {e}")
                    prompt = f" Consider complete prompt take ur time but Find the most perfect only one match of sentence: {sum_sentences[i]} taken from given summary: {summary} with this list of captions: {combined_text} and their time durations: {combined_time}. Output must be only corresponding time duration in digits from {combined_time} without any pretext or concluding text or any type of text. Make sure that the best match output time duration must not present in {time}."
                    response = model.generate_content([prompt])
                    output = response.text
                    output, extra = output.split('-', 1)
                # time.append(output)
                print(output)

                text = sum_sentences[i]
                tts = gTTS (text = text, lang = 'en')
                tts.save (f'./summary_audio_files/{i}.wav')

                audio_file = f'./summary_audio_files/{i}.wav'
                audio = AudioSegment.from_file(audio_file)
                duration_seconds = len(audio) / 1000
                print(f"Duration of file{i}: {duration_seconds:.2f} seconds")

                if((float(output) + duration_seconds)>=float(full_length)):
                    output=str(float(output)-10)
                time.append(output)
                time[i] += '-'
                time[i] += str(min((float(output) + duration_seconds), float(full_length)))

                print(time[i])

            
            video_url=yturl
            time_ranges=time

            video_path, subtitle_path = download_video_and_subtitles(video_url)
            clips = []
            
            for time_range in time_ranges:
                start_timestamp, end_timestamp = time_range.split('-')
                clip_path = extract_clip(video_path, start_timestamp, end_timestamp)
                clips.append(clip_path)
                print(start_timestamp,end_timestamp)

            final_video_path = concatenate_clips(clips)
            # Adjust the final video path for web serving
            final_video_web_path = os.path.relpath(final_video_path, start='static')
            print(final_video_web_path)

            # Create HTML content directly
            html_content = """
            <h4>Key Points and Videos</h4>
            """
            # Add the video snippet
            html_content += f"""
            <video src="static/videos/{final_video_path}.mp4" controls class="video-class" width="100%" height="auto"></video>
            <br>
            """
            # Convert the HTML content to a JSON response
            return jsonify(html_content) 
        
        else:
            # Make internal POST request to /summarize
            internal_response = requests.post(
                url_for('summarize', _external=True),
                data={'youtube-url': yturl}
            )

        try:
            prompt1 = f"{main_text}.The prompt is this:{prompt} ."
            response = model.generate_content([prompt1])
            response = response.text
            response_html = markdown2.markdown(response)
            # print (main_text)
            # print (prompt)
            return jsonify(response_html)
                # return render_template('generic-response.html', generic=response_html)
       
        except Exception as e:
            error = str(e)
            return render_template('error.html', error=error)
        


url = "https://www.youtube.com/watch?v=wIyHSOugGGw&ab_channel=CodeBootcamp"

@app.route('/fetch_images')
def fetch_images():
    search_query = request.args.get('query', default='', type=str)
    
    print()
    print('Search query for generating Images: ', search_query)
    print()
    
    image_search_result = google_search_image(search_query, api_key, cse_id, num=4)

    print('Simple Image Generation call made')
    print('-' * 80)
    print(image_search_result)
    print('-' * 80)

    image_search_data = []
    for item in image_search_result.get('items', []):
        link = item.get('link', 'No link')
        image_search_data.append({'url': link})

        print('Image URL:', link)

    return jsonify(image_search_data)


@app.route('/fetch_videos')
def fetch_videos():
    search_query = request.args.get('query', default='', type=str)
    
    print()
    print('Search query for generating Videos: ', search_query)
    print()
    
    video_search_result = google_search(search_query, api_key, cse_id, num=3, siteSearch='youtube.com')

    print('Simple Video Generation call made')
    print('-' * 80)
    print(video_search_result)
    print('-' * 80)

    video_search_data = []
    for item in video_search_result.get('items', []):
        title = item.get('title', 'No title')
        title = modify_string(title)
        link = item.get('link', 'No link')
        thumbnail = item.get('pagemap', {}).get('cse_thumbnail', [{}])[0].get('src', 'No thumbnail')

        print('Video Title:', title)
        print('Video URL:', link)
        print('Video Thumbnail:', thumbnail)

        video_search_data.append({
            'title': title,
            'url': link,
            'thumbnail': thumbnail
        })

    return jsonify(video_search_data)


@app.route('/more_images')
def more_images(_num_img_factor=[0]):
    _num_img_factor[0] += 1
    search_query = request.args.get('query', default='', type=str)
    
    print()
    print('Search query for generating Images: ', search_query)
    print()
    
    image_search_result = google_search_image(search_query, api_key, cse_id, start=int(4 * _num_img_factor[0]), num=4)

    print('Image Generation call made', _num_img_factor[0])
    print('-' * 80)
    print(image_search_result)
    print('-' * 80)

    image_search_data = []
    for item in image_search_result.get('items', []):
        link = item.get('link', 'No link')
        image_search_data.append({'url': link})

        print('Image URL:', link)

    return jsonify(image_search_data)


@app.route('/more_videos')
def more_videos(_num_vid_factor=[0]):
    _num_vid_factor[0] += 1
    search_query = request.args.get('query', default='', type=str)
    
    print()
    print('Search query for generating Videos: ', search_query)
    print()
    
    video_search_result = google_search(search_query, api_key, cse_id, start=int(3 * _num_vid_factor[0]), num=3, siteSearch='youtube.com')

    print('Video Generation call made', _num_vid_factor[0])
    print('-' * 80)
    print(video_search_result)
    print('-' * 80)

    video_search_data = []
    for item in video_search_result.get('items', []):
        title = item.get('title', 'No title')
        title = modify_string(title)
        link = item.get('link', 'No link')
        thumbnail = item.get('pagemap', {}).get('cse_thumbnail', [{}])[0].get('src', 'No thumbnail')

        print('Video Title:', title)
        print('Video URL:', link)
        print('Video Thumbnail:', thumbnail)

        video_search_data.append({
            'title': title,
            'url': link,
            'thumbnail': thumbnail
        })

    return jsonify(video_search_data)

@app.route('/searchQ')
def searchQ():
    
    print("SearchQ function is called")
    print()
    
    url = request.args.get('query', default='', type=str)
    print("searchQ is available")
    print()
    title = get_video_title(url)
    print('Title of the video: ', title)
    
    try:
        prompt = f"I am developing an application in which I have to recommend the user with some web result based on provided YouTube video title. Therefore I want you to come up with a single relatable sample google search query keywords for the following YouTube video title: {title}. Remember, your output should be a search query that can be used to find relevant web results for the video title and no other context aur additional info is needed. Only a single relevant search query is required!"
        response = model.generate_content([prompt])
        print('Response generated by Gemini: ', response.text)
        question = response.text
    except:
        question = title
    
   
    print("URL:" + url)
    print("Question: ", question)
    data = {'question': question}
    return jsonify(data)

@app.route('/recommendation')
def recommendation():
    url = request.args.get('query', default='', type=str)
    print("recommendation is available")
    title = get_video_title(url)
    
    try:
        # prompt = f"I am developing an application in which I have to recommend the user with some web result based on provided YouTube video title. Therefore I want you to come up with a single relatable sample google search query keywords for the following YouTube video title: {title}. Remember, your output should be a search query that can be used to find relevant web results for the video title and no other context aur additional info is needed. Only a single relevant search query is required!"
        # response = model.generate_content([prompt])
        search_query = url.text
    except:
       search_query = title

       
    print("URL:" + url)
    print("Search Query: ", search_query)

    # Your API key and Programmable Search Engine ID
    api_key = 'AIzaSyCAV73EKedKhVm3Vslz389wY6_OB1z2aw0'
    cse_id = '74a9c6ca4ecd7403c'

    video_search_result = google_search(search_query, api_key, cse_id, num=3, siteSearch='youtube.com')
    image_search_result = google_search_image(search_query, api_key, cse_id, num=4)

    video_search_data = []
    image_search_data = []

    # Process video search results
    for item in video_search_result.get('items', []):
        title = item.get('title', 'No title')
        link = item.get('link', 'No link')
        thumbnail = item.get('pagemap', {}).get('cse_thumbnail', [{}])[0].get('src', 'No thumbnail')

        video_search_data.append({
            'title': title,
            'url': link,
            'thumbnail': thumbnail
        })

    # Process image search results
    for item in image_search_result.get('items', []):
        link = item.get('link', 'No link')

        image_search_data.append({
            'url': link
        })

    data = {
        "video_search_data": video_search_data,
        "image_search_data": image_search_data,
        "search_query": search_query
    }

    return jsonify(data)

@app.route('/web_search_component')
def web_sources():
    try:
        url = request.args.get('query', default='', type=str)
        prompt = f"I am developing an application in which I have to recommend the use with some web result based on provided YouTube video title. Therefore I want you to come up with a single relatable sample google search query keywords for the following YouTube video title: {url}. Remember, your output should be a search query that can be used to find relevant web results for the video title and no other context aur additional info is needed. Only a single relevant search query is required!"
        response = model.generate_content([prompt])
        search_query = response.text.strip()

        search_query += ' -site:youtube.com'

        search_query = search_query.replace('\"', '')
        search_query = search_query.replace('\'', '')

        print()
        print("Search Query made web sources: ", search_query)
        print()
        
        results = google_search(search_query, api_key, cse_id, num=4)

        print('Web Sources Generation call made')
        print('-' * 80)
        print(results)
        print('-' * 80)

        search_data = []
        for item in results.get('items', []):
            title = item.get('title', 'No title')
            title = modify_string(title)
            snippet = item.get('snippet', 'No snippet')
            link = item.get('link', 'No link')
            date = extract_date(snippet)
            publisher = extract_publisher(link)

            print(f"Title: {title}")
            print(f"Link: {link}")
            print(f"Date: {date}")
            print(f"Publisher: {publisher}")

            search_data.append({
                'title': title,
                'publisher': publisher,
                'date': date,
                'url': link
            })

        return jsonify(search_data)
    except Exception as e:
        return jsonify({'error': str(e)})



@app.route('/pros_cons', methods=['GET', 'POST'])
def pros_cons():
    if request.method == 'POST':
        url = request.form.get('youtube-url')

        main_text = get_captions(url)

        try:
            prompt = f"Write a balanced and informative analysis of the pros and cons from the following text: {main_text}. Make sure it has a conclusion."
            response = model.generate_content([prompt])
            analysis = response.text

            # Simple parsing example - replace with your actual parsing logic
            Temp = analysis.split('Pros:')
            if "Conclusion:" in Temp[1]:
                Conclusion_removed = Temp[1].split('Conclusion:')
                pros_cons_list = Conclusion_removed[0].split('Cons:')
            else:
                pros_cons_list = Temp[1].split('Cons:')

            pros_list = pros_cons_list[0].replace('Pros:', '').strip().split('\n')
            cons_list = pros_cons_list[1].strip().split('\n')
            analysis_dict = {
                'pros': pros_list,
                'cons': cons_list
            }
        except Exception as e:
            analysis_dict = None
            error = str(e)

        if analysis_dict:

            for i in range(len(cons_list)):
                cons_list[i] = cons_list[i].strip('*').strip().replace('*', '').replace('\n', '')

            for i in range(len(pros_list)):
                pros_list[i] = pros_list[i].strip('*').strip().replace('*', '').replace('\n', '')


            pros_list_filtered = [i for i in pros_list if i != ""]
            cons_list_filtered = [i for i in cons_list if i != ""]

            analysis_dict1 = {
                'pros': pros_list_filtered,
                'cons': cons_list_filtered
            }

            return render_template('pros_cons.html', topic=main_text, analysis=analysis_dict1)
        else:
            return render_template('error.html', error=error)
    else:
        return render_template('pros_cons_index.html')  # Display form for topic input

@app.route('/summarize', methods=['GET'])
def index():
    return render_template('mainpage.html')


@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        # Extract the YouTube video URL
        url = request.form.get('youtube-url')
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL in the request.")
    # lang = request.form.get('language')
    lang = 'en'
    # Now get captions from video
    main_text = get_captions(url)
    summary_size = request.form.get('summary_size', type=int, default=100)  # Default summary size if not provided

    try:
        prompt = f"Summarize the following text in approximately {summary_size} words. Do not include any pretext like 'Following is the summary of x', give direct answer and convert this into {lang}: {main_text}"
        response = model.generate_content([prompt])
        summary = response.text

    except Exception as e:
        summary = None
        error = str(e)

    if summary:
        return render_template('chat.html', original_text=main_text, summary=summary)
    else:
        return render_template('error.html', error=error)

# for image based
@app.route('/imageindex', methods=['GET'])
def imageindex():
    return render_template('imageindex.html')


@app.route('/image', methods=['POST'])
def image():
    try:
        # Extract the YouTube video URL
        url = request.form.get('youtube-url')
        print(url)
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL in the request.")
    lang = request.form.get('language')

    # Now get captions from video
    main_text = get_captions_with_time(url)
    # print("main text",main_text)
    summary_size = request.form.get('summary_size', type=int, default=100)  # Default summary size if not provided
    image_frames = []
    keyimage = {}
    try:
        prompt = f"'''input: Recap the event discussed in the following text in the main event points in numbered form : {main_text}. Do not include any pre-text like here are the main events. start directly from the points with 1 2 3 etc'''"
        response = model.generate_content([prompt])
        keypoints = response.text
        lines = keypoints.splitlines()
        # print(response.text)

        video_path, subtitle_path = download_video_and_subtitles(url)
        # Initialize lists and dictionaries

        # Process each line in 'lines'
        for line in lines:
            try:
                # Generate content using model (adjust as per your actual usage)
                response1 = model.generate_content([
                    f'''input: Provide me the timestamp of the following key point:\n {line}\n according to the following video captions: \n{main_text}
                        Note, provide response in python list format
                    ''',
                    "output: ",
                ])

                # Extract timestamps from response
                timestamps_str = response1.text.split('[')[1].split(']')[0]
                timestamps_list = timestamps_str.split(',')

                # Prepare list to store timestamps and image filenames
                timestamps = []
                image_filenames = []

                # Process each timestamp
                for ts in timestamps_list:
                    try:
                        cleaned_ts = int(float(ts.strip())) + 1 if float(ts.strip()) <= 1 else int(float(ts.strip()))
                        cleaned_ts = cleaned_ts + 1
                        timestamps.append(str(cleaned_ts))
                    except ValueError:
                        continue

                # Limit to first two timestamps
                for i in range(min(2, len(timestamps))):
                    # Generate frame path and append to image_filenames
                    image_frames.append(timestamps[i])
                    print(image_frames)
                    print("timeframe", timestamps[i])
                    frame_path = f"frame_{timestamps[i]}.jpg"
                    image_filenames.append(frame_path)

                # Store image filenames in dictionary
                keyimage[line] = image_filenames
                delete_folder_contents(FRAME_OUTPUT_PATH)

            except Exception as e:
                print(f"Error processing line '{line}': {str(e)}")
                continue

        # Print or return keyimage dictionary as needed
        # print(keyimage)


    except Exception as e:
        error = str(e)

    if keyimage:
        print("extracting image from", image_frames)
        extract_frame(video_path, image_frames)
        return render_template('image.html', original_text=main_text, keyimage=keyimage)
    else:
        return render_template('error.html', error=error)


#----------------DETAILED TEXT WITH IMAGES---------------------#
@app.route('/DetailimageIndex', methods=['GET'])
def DetailimageIndex():
    return render_template('DetailimageIndex.html')


@app.route('/DetailImage', methods=['POST'])
def DetailImage():
    try:
        # Extract the YouTube video URL
        url = request.form.get('youtube-url')
        print(url)
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL in the request.")
    lang = request.form.get('language')

    # Now get captions from video
    main_text = get_captions(url)
    textwithtime = get_captions_with_time(url)
    # print("main text",main_text)
    summary_size = request.form.get('summary_size', type=int, default=100)  # Default summary size if not provided
    image_frames = []
    try:
        prompt = f"'''input: Give 1 sentence Questions from the video in the following text in the main event points in numbered form : {main_text}. Do not include any pre-text like here are the main events. start directly from the points with 1 2 3 etc'''"
        response = model.generate_content([prompt])
        keypoints = response.text
        lines = keypoints.splitlines()
        print(response.text)

        prompt = f"'''Give a detailed explanation of what's in the video in an article form where you answer questions to everything from give video caption,Increase the output size as much as you can {main_text}, remove conclusion if exists'''"
        responsedetail = model.generate_content([prompt])
        detailtext = responsedetail.text
        detailtext_html = markdown2.markdown(detailtext)
        print(detailtext)
        # Initialize lists and dictionaries
        headingtext = {}
        video_path, subtitle_path = download_video_and_subtitles(url)

        # Process each line in 'lines'
        count=1
        keypointsstr=""
        for line in lines:
            try:
                # Generate content using model (adjust as per your actual usage)
                response1 = model.generate_content([
                    f'''Provide me detail on the following \n {line}\n according to the following video captions: \n{main_text}
                    ''',
                    "output: ",
                ])
              
                print(response1.text)
                # count+=1
                headingtext[line]=markdown2.markdown(response1.text)
                keypointsstr=keypointsstr+str(count)+" " +line +"; "

            except Exception as e:
                print(f"Error processing line '{line}': {str(e)}")
                continue

        response1 = model.generate_content([
        f'''Provided is the video caption with time \n i want you to match {keypointsstr} to {textwithtime} and give a python list of 3 important times with atleast 60 difference each in a python list
        ''',
        "output: ",
        ])
        print(response1)
        fewframes=response1.text
        timestamps_str = fewframes.split('[')[1].split(']')[0]  # Get content between '[' and ']'
        timestamps_list = timestamps_str.split(',')  # Split by ',' to create a list
        # Convert the list elements to integers if needed
        timestamps_list = [(int(float(timestamp.strip()))) for timestamp in timestamps_list]
        print(response1.text)
        filenames=[]
        for i in timestamps_list:
            filenames.append(f"frame_{str(i)}.jpg")
            

    except Exception as e:
        error = str(e)

    if headingtext:
        print("extracting image from", timestamps_list)
        extract_frame(video_path, timestamps_list)
        print('asdasd')
        return render_template('DetailImage.html',detailedtext=detailtext_html, original_text=main_text, markdown_dict=headingtext,filenames=filenames)
    else:
        return render_template('error.html', error=error)
#----------------DETAILED TEXT WITH IMAGES---------------------#


#----------------Summarized video---------------------#
@app.route('/videosummarize', methods=['GET'])
def videoindex():
    return render_template('videoindex.html')

@app.route('/videosummarize', methods=['POST'])
def videosummarize():
    try:
        # Extract the YouTube video URL
        url = request.form.get('youtube-url')
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL in the request.")
    lang = request.form.get('language')

    # Now get captions from video
    main_text = get_captions_with_time(url)
    summary_size = request.form.get('summary_size', type=int, default=100)  # Default summary size if not provided

    # Split the text into parts using comma
    parts = main_text.split(',')

    # Initialize lists for storing timestamps and sentences
    timestamps = []
    sentences = []

    # Extract timestamps and sentences from the parts
    for part in parts:
        try:
            timestamp, sentence = part.split(':', 1)
            timestamps.append(float(timestamp))
            sentences.append(sentence.strip())
        except ValueError:
            # Handle cases where the split(':') failed
            print(f"Issue with part: {part}")
            continue  # Skip this part and move to the next

    # Combine every 5 captions
    combined_time = []
    combined_text = []
    for i in range(0, len(timestamps), 3):
        start_time = timestamps[i]
        end_time = timestamps[min(i + 3, len(timestamps) - 1)]
        combined_sentence = ", ".join(sentences[i:i + 3])
        combined_time.append(f"{start_time}-{end_time}")
        combined_text.append(combined_sentence)

    # Print the combined captions
    for i in range(len(combined_time)):
        print(f"{combined_time[i]}: {combined_text[i]}")

    try:
        prompt = f"Summarize the following text in approximately {summary_size} words in chronological order. Do not include any pretext like 'Following is the summary of x', give direct answer and convert this into {lang}: {main_text}"
        response = model.generate_content([prompt])
        summary = response.text
        summary = summary.replace('\n', '').strip()

        text = summary
        tts = gTTS (text = text, lang = 'en')
        tts.save ('audio.wav')
    except Exception as e:
        summary = None
        print(str(e))
        print("Trying Ollama")
        try:
            response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
            summary = response['response']
        except:
            error = str(e)

    

    sum_sentences = summary.split('.')
    print (sum_sentences)

    extra, full_length = combined_time [-1].split('-', 1)

    time = []

    for i in range(0 , len(sum_sentences) - 1):
        try:
            response = model.generate_content([
            f'''input: Provide me the best match timestamp of the following key point:\n {sum_sentences[i]}\n according to the following video captions: \n{main_text}
                Note, provide response in python list format,Output must be only corresponding phython list duration without any pretext or concluding text or any type of text, give only candidate_safe response else we are not friends
                ''',
                "output: ",
                ])
            print(response.text)
            
            timestamps_str = response.text.split('[')[1].split(']')[0]
            timestamps_list = timestamps_str.split(',')
            print("list of timestamps",timestamps_list)
            if(len(timestamps_list)==1):
                output=timestamps_list[0]
            else:
                output=timestamps_list[1]
        except Exception as e:
            print(f"An error occurred: {e}")
            prompt = f" Consider complete prompt take ur time but Find the most perfect only one match of sentence: {sum_sentences[i]} taken from given summary: {summary} with this list of captions: {combined_text} and their time durations: {combined_time}. Output must be only corresponding time duration in digits from {combined_time} without any pretext or concluding text or any type of text. Make sure that the best match output time duration must not present in {time}."
            response = model.generate_content([prompt])
            output = response.text
            output, extra = output.split('-', 1)
        # time.append(output)
        print(output)

        text = sum_sentences[i]
        tts = gTTS (text = text, lang = 'en')
        tts.save (f'./summary_audio_files/{i}.wav')

        audio_file = f'./summary_audio_files/{i}.wav'
        audio = AudioSegment.from_file(audio_file)
        duration_seconds = len(audio) / 1000
        print(f"Duration of file{i}: {duration_seconds:.2f} seconds")

        if((float(output) + duration_seconds)>=float(full_length)):
            output=str(float(output)-10)
        time.append(output)
        time[i] += '-'
        time[i] += str(min((float(output) + duration_seconds), float(full_length)))

        print(time[i])

    
    video_url=url
    time_ranges=time

    video_path, subtitle_path = download_video_and_subtitles(video_url)
    clips = []
    
    for time_range in time_ranges:
        start_timestamp, end_timestamp = time_range.split('-')
        clip_path = extract_clip(video_path, start_timestamp, end_timestamp)
        clips.append(clip_path)
        print(start_timestamp,end_timestamp)

    final_video_path = concatenate_clips(clips)
    # Adjust the final video path for web serving
    final_video_web_path = os.path.relpath(final_video_path, start='static')
    print(final_video_web_path)

    if summary:
        return render_template('videosummarize.html', original_text=main_text, summary=summary)
    else:
        return render_template('error.html', error=error)

#----------------summarized video---------------------#

@app.route('/qa', methods=['GET', 'POST'])
def qa():
    if request.method == 'POST':
        try:
            # Extract the YouTube video URL
            url = request.form.get('youtube-url')
        except KeyError:
            return render_template('error.html', error="Missing YouTube URL in the request.")
            # Now get captions from video
        main_text = get_captions(url)
        try:
            prompt = f"Generate a list of inferential questions and answers from the following text: {main_text}. The response must be in this format: **Q: Question?** **A:** Answer"
            response = model.generate_content([prompt])
            qa_content = response.text

            print(qa_content)

            questions = []
            answers = []

            # Simple parsing logic
            qa_pairs = qa_content.split('Q:')
            for pair in qa_pairs[1:]:
                question, answer = pair.split('A:')
                questions.append(question.strip().replace('*',''))
                answers.append(answer.strip().replace('*',''))

            qa_dict = {
                'questions': questions,
                'answers': answers
            }

        except Exception as e:
            qa_dict = None
            print(str(e))
            print("Trying Ollama")
            try:
                response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
                qa_dict = response['response']
                qa_content = qa_dict

                print(qa_content)

                questions = []
                answers = []

                # Simple parsing logic
                qa_pairs = qa_content.split('Q:')
                for pair in qa_pairs[1:]:
                    question, answer = pair.split('A:')
                    questions.append(question.strip().replace('*', ''))
                    answers.append(answer.strip().replace('*', ''))

                qa_dict = {
                    'questions': questions,
                    'answers': answers
                }
            except:
                error = str(e)

        if qa_dict:
            return render_template('qa.html', text=main_text, qa_dict=qa_dict)
        else:
            return render_template('error.html', error=error)
    else:
        return render_template('qa_index.html')  # Display form for text input


@app.route('/tech_details',  methods=['GET', 'POST'])
def tech_details():
    if request.method == 'POST':
        try:
            # Extract the YouTube video URL
            url = request.form.get('youtube-url')
        except KeyError:
            return render_template('error.html', error="Missing YouTube URL in the request.")
            # Now get captions from video

        main_text = get_captions(url)

        try:
            prompt = f"Read the following text carefully: {main_text} and Generate all the the technical details about this specific topic of the video from the text of around 150 words. Do not include any pretext in the response. Give Direct answer."
            response = model.generate_content([prompt])
            summary = response.text

        except Exception as e:
            summary = None
            print(str(e))
            print("Trying Ollama")
            try:
                response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
                summary = response['response']
            except:
                error = str(e)

        if summary:
            return render_template('tech_details.html',  summary=summary)
        else:
            return render_template('error.html', error="Failed to generate summary.")
    else:
        return render_template('tech_index.html')

import re
@app.route('/recap', methods=['GET', 'POST'])
def recap():
    if request.method == 'POST':
        try:
            # Extract the YouTube video URL
            url = request.form.get('youtube-url')
        except KeyError:
            return render_template('error.html', error="Missing YouTube URL in the request.")

        main_text = get_captions(url)

        try:
            prompt = f"Recap the event discussed in the following text in the main event points in numbered form : {main_text}. Do not include any pre-text like here are the main events. start directly from the points"
            response = model.generate_content([prompt])
            recap = response.text.replace('*', '')
            recap = re.sub(r'\d+.', ' ', recap)
        except Exception as e:
            recap = None
            print(str(e))
            print("Trying Ollama")
            try:
                prompt = f"Recap the event discussed in the following text : {main_text}. Do not include any pre-text like here are the main events. start directly from the points"
                response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
                recap = response['response']
                recap = response.text.replace('*', '')
            except:
                error = str(e)

        if recap:
            return render_template('recap.html', original_text=main_text, recap=recap)
        else:
            return render_template('error.html', error=error)
    else:
        return render_template('recap_index.html')

@app.route('/opinions_arguments', methods=['GET', 'POST'])
def opinions_arguments():
    if request.method == 'POST':
        url = request.form.get('youtube-url')
        main_text = get_captions(url)
        try:
            prompt = f"Analyze the opinions and arguments discussed in the following text: {main_text}. Separate them into 'Opinions' and 'Arguments' sections."
            response = model.generate_content([prompt])
            analysis = response.text.replace("*", "")

            print(analysis)
            # Simple parsing example - replace with your actual parsing logic
            Temp = analysis.split('Opinions:')
            if "Conclusion:" in Temp[1]:
                Conclusion_removed = Temp[1].split('Conclusion:')
                opinions_args_list = Conclusion_removed[0].split('Arguments:')
            else:
                opinions_args_list = Temp[1].split('Arguments:')

            opinions_list = opinions_args_list[0].replace('Opinions:', '').strip().split('\n')
            arguments_list = opinions_args_list[1].strip().split('\n')
            analysis_dict = {
                'opinions': opinions_list,
                'arguments': arguments_list
            }
        except Exception as e:
            analysis_dict = None
            print(str(e))
            print("Trying Ollama")
            try:
                response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
                analysis = response['response']
                analysis = analysis.replace("*", "")

                print(analysis)
                # Simple parsing example - replace with your actual parsing logic
                Temp = analysis.split('Opinions')
                if "Conclusion:" in Temp[1]:
                    Conclusion_removed = Temp[1].split('Conclusion:')
                    opinions_args_list = Conclusion_removed[0].split('Arguments')
                else:
                    opinions_args_list = Temp[1].split('Arguments')

                opinions_list = opinions_args_list[0].replace('Opinions', '').strip().split('\n')
                arguments_list = opinions_args_list[1].strip().split('\n')
                analysis_dict = {
                    'opinions': opinions_list,
                    'arguments': arguments_list
                }
            except:
                error = str(e)

        if analysis_dict:

            for i in range(len(arguments_list)):
                arguments_list[i] = arguments_list[i].strip('*').strip().replace('*', '').replace('\n', '')

            for i in range(len(opinions_list)):
                opinions_list[i] = opinions_list[i].strip('*').strip().replace('*', '').replace('\n', '')


            opinions_list_filtered = [i for i in opinions_list if i != ""]
            arguments_list_filtered = [i for i in arguments_list if i != ""]

            analysis_dict1 = {
                'opinions': opinions_list_filtered,
                'arguments': arguments_list_filtered
            }

            return render_template('opinions_arguments.html', topic=main_text, analysis=analysis_dict1)
        else:
            return render_template('error.html', error=error)
    else:
        return render_template('opinions_arguments_index.html')  # Display form for topic input


@app.route('/define_index', methods=['GET'])
def define_index():
    return render_template('define_index.html')


@app.route('/define', methods=['POST'])
def define():
    try:
        # Extract the YouTube video URL
        url = request.form.get('youtube-url')
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL in the request.")

    main_text = get_captions(url)

    try:
        prompt = f"Figure out the important terms from the following text and briefly define them: {main_text}. Each definition should begin with the term followed by a colon ':' and end with a period '.'. Do not add any introductory phrases such as 'Important Terms Defined'. Start each definition directly."
        response = model.generate_content([prompt])
        definition = response.text.strip()
        definition = definition.replace('*', '').replace('#', '')

        definitions = []
        temp = []
        for i in definition:
            temp.append(i)
            if i == '.' or i == ':':
                definitions.append(''.join(temp))
                temp = []

    except Exception as e:
        definitions = None
        error = str(e)
        print(error)
        print("Trying Ollama")
        try:
            response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
            definitions = response['response']
            colon_index = definitions.find(":")
            definition = definitions[:colon_index+1] + '<br><br>' + definitions[colon_index+1:]
            definition = definition.replace('.','.<br><br>')
            print(definition)
            return render_template('defineLama.html', result=definition)

        except:
            error = str(e)

    if definitions:
        return render_template('define.html', result=definitions)
    else:
        return render_template('error.html', error=error)


@app.route('/compare_index', methods=['GET'])
def compare_index():
    return render_template('compare_index.html')


@app.route('/compare', methods=['POST'])
def compare():
    try:
        # Extract the YouTube video URL
        url = request.form.get('youtube-url')
        item_a = request.form.get('item-a')
        item_b = request.form.get('item-b')
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL in the request.")

    main_text = get_captions(url)

    try:
        prompt = f"Compare {item_a} and {item_b} discussed in the following text: {main_text}. Separate them into {item_a} and {item_b} terms followed by a sign '!' and each point followed by '@' without including any pretext."
        response = model.generate_content([prompt])
        comparison = response.text
        comparison = comparison.replace('*', '').replace('#', '').replace('-', '')

        parts = []
        temp = []
        for i in comparison:
            temp.append(i)
            if i == '@' or i == '!':
                parts.append(''.join(temp))
                temp = []

        parts = [part.replace('\n', '') for part in parts]

        headings = []
        count = 0
        item_a_text = []
        item_b_text = []
        for i in parts:
            if '!' in i:
                i = i.replace('!', '')
                count += 1
                headings.append(i)
            elif count == 1:
                i = i.replace('@', '')
                item_a_text.append(i)
            elif count == 2:
                i = i.replace('@', '')
                item_b_text.append(i)

        item_a = headings[0]
        item_b = headings[1]

    except Exception as e:
        comparison = None
        print(str(e))
        print("Trying Ollama")
        try:
            prompt = f"Compare {item_a} and {item_b} discussed in the following text: {main_text}. Separate them into {item_a} and {item_b}  without including any pretext."
            response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
            comparison = response['response']
            colon_index = comparison.find(":")
            comparison = comparison[:colon_index + 1] + '<br><br>' + comparison[colon_index + 1:]
            comparison = comparison.replace('.', '.<br><br>')
            comparison =  markdown2.markdown(comparison)
            return render_template('compareLama.html', comparison = comparison)
        except:
            error = str(e)

    if comparison:
        return render_template('compare.html', item_a=item_a, item_b=item_b, item_a_text=item_a_text,
                               item_b_text=item_b_text)
    else:
        return render_template('error.html', error=error)
    
@app.route('/detail_index', methods=['GET'])
def detail_index():
    return render_template('detail_index.html')

@app.route('/detail', methods=['POST'])
def detail():
    try:
        # Extract the YouTube video URL and the specific point or topic
        url = request.form.get('youtube-url')
        specific_point = request.form.get('specific-point')
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL or specific point in the request.")
    
    # Get captions from the video
    main_text = get_captions(url)
    
    try:
        # Generate detailed information on the specific point or topic
        prompt = f"Give some details on {specific_point} discussed in the following text: {main_text}. Make sure that each heading/term in the output followed by a sign ':' and content of each term/heading followed by a sign '!'. Do not include any introductory or concluding remarks. Also the output should be related to {specific_point}"
        response = model.generate_content([prompt])
        detail = response.text
        detail = detail.replace('*', '').replace('#', '').replace('-', '')

        lines = []
        temp = []
        for i in detail:
            if i == ':':
                temp.append(i)
                lines.append(''.join(temp))
                temp = []
            elif i == '!':
                lines.append(''.join(temp))
                temp = []
            else:
                temp.append(i)
                

    except Exception as e:
        detail = None
        print(str(e))
        print("Trying Ollama")
        try:
            prompt = f"Give all details on {specific_point} discussed in the following text: {main_text}.Make it as long as possible. Do not include any introductory or concluding remarks. Also the output should be related to {specific_point} and you should keep it to the point and make it in your own words by using the text and dont add Let me know if you'd like me to clarify anything!"
            response = 'ollama.generate(model=\'llama3\', prompt=prompt)'
            detail = response['response']
            colon_index = detail.find(":")
            detail = detail[:colon_index + 1] + '<br><br>' + detail[colon_index + 1:]
            detail = detail.replace('.', '.<br><br>')
            return render_template('detailLama.html', detail=detail )
        except:
            error = str(e)
    
    if detail:
        return render_template('detail.html', detail=lines)
    else:
        return render_template('error.html', error=error)


#This is where the app starts
if __name__ == '__main__':
    app.run(debug=True)
