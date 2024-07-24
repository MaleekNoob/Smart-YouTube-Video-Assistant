document.addEventListener("DOMContentLoaded", function() {
    // Replace these arrays with your dynamic data
    const images = [
        { src: 'https://d.newsweek.com/en/full/2418826/possible-democratic-presidential-candidates.jpg?w=1200&f=6c8bc2b03fe547462c2ee15ac5d3fdf4', alt: 'Image 1' },
        { src: 'https://media.cnn.com/api/v1/images/stellar/prod/231201191451-newsom-khanna-shapiro-whitmer-kelly-buttigieg-split.jpg?c=16x9&q=h_833,w_1480,c_fill', alt: 'Image 2' },
        { src: 'https://www.politico.com/dims4/default/caa9522/2147483647/strip/true/crop/1160x773+0+0/resize/630x420!/quality/90/?url=https%3A%2F%2Fstatic.politico.com%2F2a%2F41%2Fd05039374a83a75b69f3730b1ea5%2Fdemocratic-candidates-debates-hp.jpg', alt: 'Image 3' },
        { src: 'https://s.abcnews.com/images/Politics/GTY_clinton_omalley_sanders_kab_150806_16x9_992.jpg', alt: 'Image 4' }
    ];

    const videos = [
        { src: 'https://d3i6fh83elv35t.cloudfront.net/static/2023/02/2019-07-31T234608Z_461202589_RC1F3E4FD300_RTRMADP_3_USA-ELECTION-DEBATE-1024x683.jpg', title: 'Video 1', url: 'https://youtu.be/H9RSeDUdkCA?si=ry31hOo7a1B8Y3MS', publisher: 'CNN', views_count: '1.2M views' },
        { src: 'https://images.paramount.tech/uri/mgid:arc:imageassetref:bet.com:84cff12a-8944-4608-807a-ec3cef277e8e?quality=0.7&gen=ntrn', title: 'Video 2', url: 'https://youtu.be/iK5dpPzjaPA?si=tYEOoXGIZzxkF4jt', publisher: 'BBC', views_count: '466K views' },
        { src: 'https://d3i6fh83elv35t.cloudfront.net/static/2023/06/2020-03-08T015541Z_1239178039_RC2DFF92D2AW_RTRMADP_3_USA-ELECTION-SANDERS-1024x683.jpg', title: 'Video 3', url: 'https://youtu.be/43d2LhXCQvQ?si=26TxFOJvYba33wPH', publisher: 'CBS', views_count: '28K views' },
        { src: 'https://static.politico.com/dims4/default/cd21df5/2147483647/resize/1160x%3E/quality/90/?url=https%3A%2F%2Fstatic.politico.com%2F25%2Fce%2Fd39e95144ab49d15067a2b5d77f6%2Fcandidates-grid-2320-1546-newcrop.jpg', title: 'Video 4', url: 'https://youtu.be/SnbGD677_u0?si=mTS96xz7bm0-4f1i', publisher: 'Channel4', views_count: '1.1M views' }
    ];

    const imagesContainer = document.getElementById('images-container');
    const videosContainer = document.getElementById('videos-container');

    if (imagesContainer) {
        images.forEach(image => {
            const imgElement = document.createElement('img');
            imgElement.src = image.src;
            imgElement.alt = image.alt;
            imgElement.classList.add('image-item');
            imagesContainer.appendChild(imgElement);
        });
    }

    if (videosContainer) {
        videos.forEach(video => {
            const videoElement = document.createElement('div');
            videoElement.classList.add('video-item');
            videoElement.innerHTML = `
                <img class="video-thumbnail" src="${video.src}" alt="${video.title}">
                <p class="video-title">${video.title}</p>
                <p class="video-publisher">From ${video.publisher}</p>
                <p class="video-views">${video.views_count}</p>
            `;
            videoElement.onclick = () => {
                window.open(video.url, '_blank');
            };
            videosContainer.appendChild(videoElement);
        });
    }
});

function viewMoreImages() {
    // Logic to load more images
    console.log('View more images');
}

function viewMoreVideos() {
    // Logic to load more videos
    console.log('View more videos');
}
