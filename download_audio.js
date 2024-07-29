import ytdl from 'ytdl-core';
import fs from 'fs';

const videoUrl = process.argv[2];
const videoId = ytdl.getURLVideoID(videoUrl);

ytdl.getInfo(videoId).then(info => {
    const title = info.videoDetails.title.replace(/[^\w\s]/gi, '');
    const filename = `${title}.mp3`;
    const filePath = `./audio_files/${filename}`;

    // Ensure the audio_files directory exists
    if (!fs.existsSync('./audio_files')) {
        fs.mkdirSync('./audio_files');
    }

    const audioStream = ytdl(videoUrl, { filter: 'audioonly' });
    const fileStream = fs.createWriteStream(filePath);

    audioStream.pipe(fileStream);

    audioStream.on('end', () => {
        console.log(filePath);
    });

    audioStream.on('error', err => {
        console.error(err);
        process.exit(1);
    });
}).catch(err => {
    console.error(err);
    process.exit(1);
});
