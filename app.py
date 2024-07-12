from flask import Flask, request, render_template, redirect, url_for, flash
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
import ollama
import yt_dlp
import shutil

"""
   FOR 
   WHISPER 
   API"""

# Load Whisper model
whisperModel = whisper.load_model("base")


# Function to chunk the audio file
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

# Configure the Google Generative AI
genai.configure(api_key=os.getenv("GEM_KEY"))

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
        result = subprocess.run(['node', './caption-scraper.js', url_for_captions], capture_output=True, text=True,
                                encoding='utf-8')

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
def download_video_and_subtitles(video_url):
    """Download video and subtitles using yt_dlp."""
    ydl_opts = {
        'outtmpl': os.path.join(VIDEO_DOWNLOAD_PATH, '%(id)s.%(ext)s'),
        'writesubtitles': True,
        'subtitlesformat': 'srt',
        'format': 'best'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_id = info_dict.get("id", None)
        video_ext = info_dict.get("ext", None)
        video_path = os.path.join(VIDEO_DOWNLOAD_PATH, f"{video_id}.{video_ext}")
        subtitle_path = os.path.join(VIDEO_DOWNLOAD_PATH, f"{video_id}.en.srt")
        return video_path, subtitle_path



"""
   BELOW 
   ARE
   ALL THE ROUTES
   FOR OUR APPLICATION
"""



@app.route('/')
def home():
    return render_template('generic.html')


@app.route('/generic', methods=['GET','POST'])
def generic():
    if request.method == 'GET':
        return render_template('generic.html')
    elif request.method == 'POST':
        # Get the prompt written by user from the form

        prompt = request.form.get('prompt')
        prompt = f"I want you to take this prompt from user '{prompt}' now you have to Categorize this prompt into [summarize,pros&cons,define,other] and you can categorize in only one type.Multiple types not allowed and generate a single category selected from the list and dont add extra text just select one of the categorizes"

        try:
            response = model.generate_content([prompt])
            category = response.text
        except:
            try:
                print("Trying Ollama Gemini gave error")
                prompt = f"I want you to take this prompt from user '{prompt}' now you have to Categorize this prompt into [summarize,pros&cons,define,other] and you can categorize in only one type.Multiple types not allowed and generate a single category selected from the list and dont add extra text just select one of the categorizes and write in only small leter NO CAPITAL LETTERS"
                response = ollama.generate(model='llama3', prompt=prompt)
                category = response['response']
            except Exception as e:
                error = str(e)
                return render_template('error.html', error=error)
        yturl = request.form.get('youtube-url')


        print(category)
        # Return the output according to the categorization
        print(category)
        if "pros&cons" in category:
            # Make internal POST request to /pros_cons
            internal_response = requests.post(
                url_for('pros_cons', _external=True),
                data={'youtube-url': yturl}
            )
            return internal_response.text
        elif "summarize" in category:
            # Make internal POST request to /summarize
            internal_response = requests.post(
                url_for('summarize', _external=True),
                data={'youtube-url': yturl}
            )
            return internal_response.text

        elif "define" in category:
            # Make internal POST request to /opinions_arguments
            internal_response = requests.post(
                url_for('define', _external=True),
                data={'youtube-url': yturl}
            )
            return internal_response.text
        elif "other" in category:
            # Make a generic response
            url = request.form.get('youtube-url')
            prompt = request.form.get('prompt')
            main_text = get_captions(url)
            print(main_text)

            try:
                prompt = f"Write a balanced and informative analysis of the pros and cons from the following text and add <br> tags where a new line begins: {main_text}.The prompt is this:{prompt} ."

                response = model.generate_content([prompt])
                response = response.text
                response_html = markdown2.markdown(response)
                return render_template('generic-response.html', generic=response_html)
            except:
                try:
                    print("Trying Ollama Gemini gave error")
                    response = ollama.generate(model='llama3', prompt=prompt)
                    response = response['response']
                    response_html = markdown2.markdown(response)
                    return render_template('generic-response.html', generic=response_html)
                except Exception as e:
                    error = str(e)
                    return render_template('error.html', error=error)

        else:
            # Make internal POST request to /summarize
            internal_response = requests.post(
                url_for('summarize', _external=True),
                data={'youtube-url': yturl}
            )


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
            print(str(e))
            print("Trying Ollama")
            try:
                response = ollama.generate(model='llama3', prompt=prompt)
                analysis = response['response']
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
            except:
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
    return render_template('index.html')


@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        # Extract the YouTube video URL
        url = request.form.get('youtube-url')
    except KeyError:
        return render_template('error.html', error="Missing YouTube URL in the request.")
    lang = request.form.get('language')

    # Now get captions from video
    main_text = get_captions(url)
    summary_size = request.form.get('summary_size', type=int, default=100)  # Default summary size if not provided

    try:
        prompt = f"Summarize the following text in approximately {summary_size} words. Do not include any pretext like 'Following is the summary of x', give direct answer and convert this into {lang}: {main_text}"
        response = model.generate_content([prompt])
        summary = response.text

    except Exception as e:
        summary = None
        print(str(e))
        print("Trying Ollama")
        try:
            response = ollama.generate(model='llama3', prompt=prompt)
            summary = response['response']
        except:
            error = str(e)

    if summary:
        return render_template('summarize.html', original_text=main_text, summary=summary)
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
    #main_text = get_captions_with_time(url)
    main_text = "jhj"
    # print("main text",main_text)
    summary_size = request.form.get('summary_size', type=int, default=100)  # Default summary size if not provided
    image_frames = []
    keyimage = {}
    try:
        prompt = f"'''input: Recap the event discussed in the following text in the main event points in numbered form : {main_text}. Do not include any pre-text like here are the main events. start directly from the points with 1 2 3 etc'''"
        response = model.generate_content([prompt])
        keypoints = response.text
        lines = keypoints.splitlines()f
        # print(response.text)
        print("hhjhjhjhjh")
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
                response = ollama.generate(model='llama3', prompt=prompt)
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
                response = ollama.generate(model='llama3', prompt=prompt)
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
                response = ollama.generate(model='llama3', prompt=prompt)
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
                response = ollama.generate(model='llama3', prompt=prompt)
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
            response = ollama.generate(model='llama3', prompt=prompt)
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
            response = ollama.generate(model='llama3', prompt=prompt)
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
            response = ollama.generate(model='llama3', prompt=prompt)
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
