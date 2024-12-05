document.addEventListener('DOMContentLoaded', function () {

    function checkAppointment() {
      const ssn = document.getElementById("ssn").value;
      const resultDiv = document.getElementById("result");
  
      if (!ssn) {
        resultDiv.innerHTML = "Please Enter SSN！";
        resultDiv.classList.remove("d-none");
        resultDiv.classList.add("alert-danger");
        return;
      }
  
      const xhr = new XMLHttpRequest();
      xhr.open("GET", `index.php?action=getAppointment&ssn=${encodeURIComponent(ssn)}`, true);

      xhr.onload = function () {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText); 
          if (response.success) {
            resultDiv.innerHTML = `<p><strong>Name:</strong> ${response.name}</p>
                                   <p><strong>Age:</strong> ${response.age}</p>
                                   <p><strong>Phone Number:</strong> ${response.phone}</p>
                                   <p><strong>Traveling Date:</strong> ${response.tour_date}</p>
                                   <p><strong>Destination:</strong> ${response.destination}</p>`;
            resultDiv.classList.remove("d-none");
            resultDiv.classList.add("alert-success");
          } else {
            resultDiv.innerHTML = "No related trips were found!";
            resultDiv.classList.remove("d-none");
            resultDiv.classList.add("alert-danger");
          }
        } else {
          resultDiv.innerHTML = "Somethings Went wrong. Try it later";
          resultDiv.classList.remove("d-none");
          resultDiv.classList.add("alert-danger");
        }
      };
  
      xhr.send();
    }
    const submitBtn = document.getElementById("submitBtn");
    submitBtn.addEventListener("click", checkAppointment);
  });