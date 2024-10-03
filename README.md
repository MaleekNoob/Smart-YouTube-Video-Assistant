# YouTube Smart Video Assistant

**YouTube Smart Video Assistant** is an AI-powered web application that helps you quickly grasp the content of YouTube videos. 

### Features

* **YouTube Transcript Extraction:** Fetches transcript and timestamps from YouTube videos.
* **Whisper API Integration:** Transcribes videos without captions using the Whisper API.
* **Gemini API:** Summarizes the video's content or provides bullet points with timestamps for key moments.
* **Snapshot Generation:** Extracts snapshots from the video at important timestamps for visual context.
* **Efficient Processing:** Optimized to reduce processing time and improve user experience.

**Demo:** 

* (https://youtu.be/OngOqH2DVnA?si=WlsPaIO0nOuoEnwi)

### How It Works

1. **Input URL:** User submits a YouTube video URL.
2. **Fetch Captions/Transcribe:** Application fetches captions or uses Whisper API to transcribe the video.
3. **Summarization:** Gemini API identifies key moments and summarizes the video.
4. **Snapshot Generation:** Python script generates snapshots from the video at important timestamps.
5. **Results:** User receives a summarized text response along with snapshots to quickly grasp the content.

### Technology Stack

* **Backend:** Flask (Python)
* **APIs:**
    * YouTube API for fetching captions and metadata
    * Whisper API for transcribing audio
    * Gemini API for summarizing and extracting key moments
* **Video Processing:** OpenCV, yt-dlp
* **Frontend:** HTML, CSS, JavaScript

### Installation and Setup

**Prerequisites:**

* Python 3.7+
* Flask
* yt-dlp
* OpenCV
* Whisper API Key
* Gemini API Key
* YouTube Data API Key


**Clone the Repository**

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

**Install Dependencies**

```bash
pip install -r requirements.txt
```

**Set Up API Keys**

You'll need to configure your API keys in the environment:

```bash
export YOUTUBE_API_KEY=your_youtube_api_key
export WHISPER_API_KEY=your_whisper_api_key
export GEMINI_API_KEY=your_gemini_api_key
```

**Run the Application**

```bash
flask run
```

The application will be available at http://127.0.0.1:5000/.

### Usage

1. Enter a YouTube video URL in the input field.
2. (Optional) Provide a custom prompt (e.g., summary, key points, etc.).
3. Click "Submit".
4. The app will display the summarized text along with images captured from the key moments in the video.

### Example Output

* **Summary:** A short text summarizing the video or providing bullet points of the key moments.
* **Snapshots:** Visual snapshots extracted from important moments within the video.

### Future Enhancements

* Add support for multiple languages in transcription and summarization.
* Improve frame extraction by directly accessing video streams.
* Enhance UI with responsive design and video preview for each snapshot.

### Contributing

Feel free to fork this project, make improvements, and submit pull requests! Contributions are welcome.

### License

This project is licensed under the MIT License - see the LICENSE file for details.

### Contact

For any inquiries or feedback, reach out at maleekhussainali456@gmail.com.
