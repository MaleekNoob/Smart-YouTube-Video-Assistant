document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('prompt-form');
    const imagesContainer = document.getElementById('images-container');
    const videosContainer = document.getElementById('videos-container');
    const webSourcesContainer = document.getElementById('web-sources-container');
    responseTitle = document.getElementById('welcome')
    YouTubeURLPlaceholder = document.getElementById('youtube-url')

    // Retrieve the YouTube URL from sessionStorage
    let searchQuery = JSON.parse(sessionStorage.getItem('url'));

    fetchImages(searchQuery);

    fetchVideos(searchQuery);

    fetchWebSources(searchQuery);
    
    searchQuery = reduceText(searchQuery, 30)
    responseTitle.innerHTML = searchQuery
    actualURL = sessionStorage.getItem('actual-url')
    YouTubeURLPlaceholder.value = removeQuotes(actualURL)

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission

        const youtubeUrl = document.getElementById('youtube-url').value;

        // Encode the YouTube URL to make it URL-safe
        const encodedYoutubeUrl = encodeURIComponent(youtubeUrl);

        fetch(`/recommendation?query=${encodedYoutubeUrl}`)
        .then(response => response.json())
        .then(data => {
            // Clear previous results
            imagesContainer.innerHTML = '';
            videosContainer.innerHTML = '';
            webSourcesContainer.innerHTML = '';

            searchQuery = data.search_query;
            fetchImages(searchQuery);   
            fetchVideos(searchQuery);
            fetchWebSources(searchQuery);
        })
        .catch(error => console.error('Error fetching recommendation data:', error));
    });

    function reduceText(text, maxLength) {
        if (text.length > maxLength) {
            return text.substring(0, maxLength) + '...';
        }
        return text;
    }

    function removeQuotes(text) {
        return text.replace(/['"]+/g, '');
    }

    document.querySelector('.view-more-images-btn').addEventListener('click', function() {
        fetchMoreImages(searchQuery);
    });

    document.querySelector('.view-more-videos-btn').addEventListener('click', function() {
        fetchMoreVideos(searchQuery);
    });

    function fetchImages(query) {
        fetch(`/fetch_images?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                // Clear the previous images
                imagesContainer.innerHTML = '';

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

    function fetchVideos(query) {
        fetch(`/fetch_videos?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                // Clear the previous videos
                videosContainer.innerHTML = '';

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

    function fetchMoreImages(query) {
        fetch(`/more_images?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                // Clear the previous images
                // imagesContainer.innerHTML = '';

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

    function fetchMoreVideos(query, count=1) {
        fetch(`/more_videos?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                // Clear the previous videos
                // videosContainer.innerHTML = '';

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

    function fetchWebSources(query) {
        fetch(`/web_search_component?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(webSource => {
                    const webSourceElement = document.createElement('div');
                    webSourceElement.classList.add('box');
                    webSourceElement.onclick = () => {
                        window.open(webSource.url, '_blank');
                    };
                    webSourceElement.innerHTML = `
                        <h2 class="title">${webSource.title}</h2>
                        <p class="publisher">${webSource.publisher}</p>
                        <span class="date">${webSource.date}</span>
                    `;
                    webSourcesContainer.appendChild(webSourceElement);
                });
            })
            .catch(error => console.error('Error fetching web sources:', error));
    }
});
