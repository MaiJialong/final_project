document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("bookingForm"); 
    const resultDiv = document.getElementById("result"); 
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      const name = document.getElementById("name").value.trim();
      const age = parseInt(document.getElementById("age").value.trim(), 10);
      const ssn = document.getElementById("ssn").value.trim();
      const phone = document.getElementById("phone").value.trim();
      const tour_date = document.getElementById("tour_date").value.trim();
      const destination = document.getElementById("destination").value.trim();
  
      // Data validation
      if (!name || !ssn || !phone || !tour_date || !destination) {
        resultDiv.className = "alert alert-danger";
        resultDiv.textContent = "All fields are required, please complete the form and submit!";
        resultDiv.classList.remove("d-none");
        return;
      }
  
      if (isNaN(age) || age <= 0) {
        resultDiv.className = "alert alert-danger";
        resultDiv.textContent = "Please enter a valid age!";
        resultDiv.classList.remove("d-none");
        return;
      }
  
      if (!/^\d{9}$/.test(ssn)) {
        resultDiv.className = "alert alert-danger";
        resultDiv.textContent = "Please enter a valid 9-digit SSN!";
        resultDiv.classList.remove("d-none");
        return;
      }
  
      if (!/^\d{10}$/.test(phone)) {
        resultDiv.className = "alert alert-danger";
        resultDiv.textContent = "Please enter a valid 10-digit cell phone number!";
        resultDiv.classList.remove("d-none");
        return;
      }
  
      if (new Date(tour_date) < new Date()) {
        resultDiv.className = "alert alert-danger";
        resultDiv.textContent = "Travel dates must be future dates!";
        resultDiv.classList.remove("d-none");
        return;
      }
  
        fetch("/final-project/public/index.php?controller=booking&action=create", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name,
                age,
                ssn,
                phone,
                tour_date,
                destination,
            })
      })
        .then((response) => response.json())
        .then((data) => {
            console.log('Server Response:', data);
            console.log(resultDiv);
            if (data.success) {
                resultDiv.className = "alert alert-success";
                resultDiv.textContent = "The booking was successful! Thank you for your submission.";
                form.reset();
            } else {
                resultDiv.className = "alert alert-danger";
                resultDiv.textContent = data.message || "Booking failed, please try again later!";
            }
            resultDiv.classList.remove("d-none");
            })
        .catch((error) => {
            console.error("Fetch error:", error);
            resultDiv.className = "alert alert-danger";
            resultDiv.textContent = "Request failed, please try again later!";
            resultDiv.classList.remove("d-none");
        })
    })
});