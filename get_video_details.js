import fetch from 'node-fetch';
import ytdl from 'ytdl-core';

const apiKey = 'AIzaSyCAV73EKedKhVm3Vslz389wY6_OB1z2aw0'; // Replace with your YouTube Data API key
const videoUrl = process.argv[2];
const videoId = ytdl.getURLVideoID(videoUrl);

async function getVideoDetails(videoId, apiKey) {
    const url = `https://www.googleapis.com/youtube/v3/videos?id=${videoId}&part=snippet,contentDetails,statistics,status&key=${apiKey}`;
    const response = await fetch(url);
    const data = await response.json();
    
    if (data.items.length === 0) {
        throw new Error('Video not found');
    }
    
    return data.items[0];
}

getVideoDetails(videoId, apiKey).then(details => {
    console.log(JSON.stringify(details, null, 2));
}).catch(err => {
    console.error(err);
    process.exit(1);
});
