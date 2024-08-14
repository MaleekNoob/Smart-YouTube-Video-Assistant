function toggleSearch() {
    const searchBar = document.querySelector('.search-bar');
    searchBar.classList.toggle('visible');
    if (searchBar.classList.contains('visible')) {
        searchBar.focus();
    }
}

function openJobDetails(jobTitle) {
    alert('You clicked on ' + jobTitle);
}
