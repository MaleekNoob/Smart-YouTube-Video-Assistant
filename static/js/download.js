document.addEventListener('DOMContentLoaded', function () {
    const videoUrlInput = document.getElementById('videoUrl');
    const downloadVideoBtn = document.getElementById('downloadVideo');
    const loadingIndicator = document.getElementById('loading');

    downloadVideoBtn.addEventListener('click', () => {
        const url = videoUrlInput.value;
        console.log('Downloading video:', url);
        if (url) {
            loadingIndicator.classList.remove('loading-hidden');
            fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            })
            .then(response => response.json())
            .then(data => {
                loadingIndicator.classList.add('loading-hidden');
                if (data.success) {
                    console.log('Video downloaded successfully:', data.filename);
                } else {
                    console.error('Error downloading video:', data.error);
                }
            })
            .catch(error => {
                loadingIndicator.classList.add('loading-hidden');
                console.error('Error downloading video:', error);
            });
        }
    });
});
