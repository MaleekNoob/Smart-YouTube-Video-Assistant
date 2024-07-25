document.addEventListener("DOMContentLoaded", function() {
    const imagesContainer = document.getElementById('images-container');
    const videosContainer = document.getElementById('videos-container');
    const searchQuery = "YOUR_SEARCH_QUERY";  // Update this with the actual search query

    document.querySelector('.view-more-images-btn').addEventListener('click', function() {
        fetchMoreImages(searchQuery);
    });

    document.querySelector('.view-more-videos-btn').addEventListener('click', function() {
        fetchMoreVideos(searchQuery);
    });

    function fetchMoreImages(query) {
        fetch(`/more_images?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(image => {
                    const imgElement = document.createElement('img');
                    imgElement.src = image.url;
                    imgElement.alt = 'Related Image';
                    imgElement.classList.add('image-item');
                    imagesContainer.appendChild(imgElement);
                });
            })
            .catch(error => console.error('Error fetching more images:', error));
    }

    function fetchMoreVideos(query) {
        fetch(`/more_videos?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(video => {
                    const videoElement = document.createElement('div');
                    videoElement.classList.add('video-item');
                    videoElement.innerHTML = `
                        <img src="${video.thumbnail}" alt="${video.title}">
                        <div class="video-info">
                            <p class="video-title">${video.title}</p>
                        </div>
                    `;
                    videoElement.onclick = () => {
                        window.open(video.url, '_blank');
                    };
                    videosContainer.appendChild(videoElement);
                });
            })
            .catch(error => console.error('Error fetching more videos:', error));
    }
});
