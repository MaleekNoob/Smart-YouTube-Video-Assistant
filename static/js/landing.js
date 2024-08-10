
document.addEventListener("DOMContentLoaded", function() {
    function adjustLayout() {
      const screenWidth = window.innerWidth;
      const robotImage = document.querySelector('.robot-removebg-preview-1-icon');
      
      if (screenWidth < 576) {
        robotImage.style.width = '100%';
        robotImage.style.height = 'auto';
      } else if (screenWidth < 768) {
        robotImage.style.width = '70%';
        robotImage.style.height = 'auto';
      } else {
        robotImage.style.width = '50%';
        robotImage.style.height = 'auto';
      }
    }
  
    adjustLayout();
    window.addEventListener('resize', adjustLayout);
  });
  