document.addEventListener('DOMContentLoaded', () => {
    const spinnerEl = document.querySelector('.spinner-wrapper');
    const MIN_DISPLAY_TIME = 400; // Minimum spinner display time in ms
  
    if (!spinnerEl) return;
  
    const startTime = Date.now();
  
    window.addEventListener('load', () => {
        const elapsed = Date.now() - startTime;
        const remainingTime = Math.max(0, MIN_DISPLAY_TIME - elapsed);
  
        setTimeout(() => {
            spinnerEl.style.opacity = '0';
            setTimeout(() => {
                spinnerEl.style.display = 'none';
            }, 200);
        }, remainingTime);
    });
  });
  
  
  function submitForm() {
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btnText');
    const form = document.getElementById('myForm');
  
    // Disable the button to prevent multiple submissions
    submitBtn.disabled = true;
    
    // Show the spinner and hide the button text
    spinner.style.display = 'inline-block';
    btnText.style.display = 'none';
  
    // Create a FormData object to capture the form data
    const formData = new FormData(form);
  
    // Fetch API to submit the form data via AJAX
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value, // CSRF token
        },
    })
    .then(response => response.json()) // Assuming the server returns JSON
    .then(data => {
        // Handle success (you can display a success message here)
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        btnText.style.display = 'inline-block';
        alert('Form submitted successfully!');
        console.log('Success:', data);
    })
    .catch((error) => {
        // Handle error (you can display an error message here)
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        btnText.style.display = 'inline-block';
        alert('An error occurred. Please try again.');
        console.error('Error:', error);
    });
  }
  
  document.addEventListener('DOMContentLoaded', function () {
          var toastElements = document.querySelectorAll('.toast');
          toastElements.forEach(function (toastElement) {
              var toast = new bootstrap.Toast(toastElement);
              toast.show();
      
      });
      });