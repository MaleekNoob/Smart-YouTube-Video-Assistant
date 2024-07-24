// const boxes = document.querySelectorAll('.box');

// const searchData = [
//     { title: "$10,000 Every Day You Survive In...'", publisher: "YouTube", date: 'Jun 1, 2024', url: 'https://www.youtube.com/watch?v=U_LlX4t0A9I'},
//     { title: "MrBeast on X: \"Just filmed our bi...", publisher: "Twitter", date: 'Jun 5, 2024', url: 'https://twitter.com/MrBeast/status/1798465522008252438'},
//     { title: "Protect The Yacht, Keep It! ...", publisher: "YouTube", date: 'May 11, 2024', url: 'https://www.youtube.com/watch?v=F6PqxbvOCUI&vl=en'} ,
//     { title: "The new MrBeast video is kind of a s...", publisher: "Reddit", date: 'Apr 20, 2024', url: 'https://www.reddit.com/r/MrBeast/comments/1c8w8j4/the_new_mrbeast_video_is_kind_of_a_sad_reality/'}
// ];


// searchData.forEach((data, index) => {
//     boxes[index].innerHTML = `
//         <h2 class="title">${data.title}</h2>
//         <p class="publisher">${data.publisher}</p>
//         <span class="date">${data.date}</span>
//     `;

//     // Add click event listener to each box
//     boxes[index].addEventListener('click', () => {
//         let targetUrl;
//         switch (index) {
//             case 0:
//                 targetUrl = searchData[0].url;
//                 break;
//             case 1:
//                 targetUrl = searchData[1].url;
//                 break;
//             case 2:
//                 targetUrl = searchData[2].url;
//                 break;
//             case 3:
//                 targetUrl = searchData[3].url;
//                 break;
//             default:
//                 targetUrl = "https://www.google.com/"; // Google (default)
//                 break;
//         }
//         window.location.href = targetUrl;
//     });
// });