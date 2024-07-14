const boxes = document.querySelectorAll('.box');

const searchData = [
    { title: "China's AI 'war of a hundred models'", publisher: "Reuters" },
    { title: "Baidu's CEO slams China's 'war for a...", publisher: "Forbes" },
    { title: "A price war breaks out between Chin...", publisher: "The Economist" } 
];

boxes[3].innerHTML = `
    <h2 class="title"> + View <br>More</h2>
    <p class="publisher"></p>
`;

searchData.forEach((data, index) => {
    boxes[index].innerHTML = `
        <h2 class="title">${data.title}</h2>
        <p class="publisher">${data.publisher}</p>
    `;

    // Add click event listener to each box
    boxes[index].addEventListener('click', () => {
        let targetUrl;
        switch (index) {
            case 0:
                targetUrl = "https://www.reuters.com/"; // Reuters
                break;
            case 1:
                targetUrl = "https://www.forbes.com/"; // Forbes
                break;
            case 2:
                targetUrl = "https://www.economist.com/"; // The Economist
                break;
            default:
                targetUrl = "https://www.google.com/"; // Google (default)
                break;
        }
        window.location.href = targetUrl;
    });
});