import ytdl from 'ytdl-core';
import fs from 'fs';

const videoUrl = process.argv[2];
const videoId = ytdl.getURLVideoID(videoUrl);

ytdl.getInfo(videoId).then(info => {
    const title = info.videoDetails.title.replace(/[^\w\s]/gi, '');
    const filename = `${title}.mp4`;
    const filePath = `./${filename}`;
    const videoStream = ytdl(videoUrl);

    videoStream.pipe(fs.createWriteStream(filePath));

    videoStream.on('end', () => {
        console.log(filePath);
    });

    videoStream.on('error', err => {
        console.error(err);
        process.exit(1);
    });
}).catch(err => {
    console.error(err);
    process.exit(1);
});
