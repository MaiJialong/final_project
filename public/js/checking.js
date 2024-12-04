document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("checkingForm");
    const resultDiv = document.getElementById("result");

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const ssn = document.getElementById("ssn").value.trim();

        if (!ssn) {
            resultDiv.className = "alert alert-danger";
            resultDiv.textContent = "SSN is required!";
            resultDiv.classList.remove("d-none");
            return;
        }

        fetch(`/final-project/public/index.php?controller=checking&action=check&ssn=${ssn}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    resultDiv.className = "alert alert-success";
                    resultDiv.innerHTML = `
                        <p><strong>Name:</strong> ${data.data.name}</p>
                        <p><strong>Age:</strong> ${data.data.age}</p>
                        <p><strong>Tour Date:</strong> ${data.data.tour_date}</p>
                        <p><strong>Phone:</strong> ${data.data.phone}</p>
                        <p><strong>Destination:</strong> ${data.data.destination}</p>
                    `;
                } else {
                    resultDiv.className = "alert alert-danger";
                    resultDiv.textContent = data.message;
                }
                resultDiv.classList.remove("d-none"); //
            })
            .catch((error) => {
                console.error("Fetch error:", error);
                resultDiv.className = "alert alert-danger";
                resultDiv.textContent = "An error occurred while fetching the data.";
                resultDiv.classList.remove("d-none");
            });
    });
});
