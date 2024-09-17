import fetch from 'node-fetch';
import { getSubtitles } from 'youtube-captions-scraper';

const videoId = process.argv[2];
const apiKey = 'AIzaSyCAV73EKedKhVm3Vslz389wY6_OB1z2aw0';

(async () => {
    try {
        // Fetch the list of captions for the video
        const captionsList = await getCaptionsList(videoId, apiKey);

        // Check if the captions list is empty
        if (captionsList.length === 0) {
            throw new Error('No captions found for this video');
        }

        // Find English captions or use the first available
        let language = 'en';
        const englishCaption = captionsList.find(caption => caption.snippet.language === 'en');

        if (englishCaption) {
            language = englishCaption.snippet.language;
        } else {
            console.warn('No English captions found, using the first available language:', captionsList[0].snippet.language);
            language = captionsList[0].snippet.language;
        }

        // Fetch subtitles
        const captions = await getSubtitles({ videoID: videoId, lang: language });
        console.log(JSON.stringify(captions));

    } catch (err) {
        console.error('Error:', err);
        process.exit(1);
    }
})();

async function getCaptionsList(videoId, apiKey) {
    const url = `https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId=${videoId}&key=${apiKey}`;
    const response = await fetch(url);
    const data = await response.json();

    if (!data.items || data.items.length === 0) {
        throw new Error('No captions found for this video');
    }

    return data.items;
}
