document.getElementById('bookingForm').addEventListener('submit', function(event) {
  event.preventDefault();  // 防止表单的默认提交行为

  const name = document.getElementById('name').value;
  const age = document.getElementById('age').value;
  const ssn = document.getElementById('ssn').value;
  const phone = document.getElementById('phone').value;
  const tourDate = document.getElementById('tour_date').value;
  const destination = document.getElementById('destination').value;

  // 表单验证
  if (!name || !age || !ssn || !phone || !tourDate || !destination) {
    alert('Please fill all fields.');
    return;
  }

  // 准备要发送的数据
  const formData = {
    name: name,
    age: age,
    ssn: ssn,
    phone: phone,
    tour_date: tourDate,
    destination: destination
  };

  // 发送POST请求
  fetch('/final-project/app/Controller/BookingController.php', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(formData)
  })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('Booking successful!');
        } else {
          alert('Booking failed: ' + data.message);
        }
      })
      .catch(error => {
        alert('Error: ' + error.message);
      });
});
