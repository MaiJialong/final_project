<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Book Your Trip</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" />
  <script src="/final-project/public/js/booking.js"></script>
  <style>
        body {
            background-image: url('../images/富士山.jpg');
            background-size: cover;
            background-position: center;
        }
    </style>
</head>
<body>
  <header class="bg-primary text-white p-4">
    <h1>Book Your Trip</h1>
  </header>

  <div class="container mt-5">
    <form id="bookingForm" method="POST">
      <div class="mb-3">
        <label for="name" class="form-label">Name</label>
        <input type="text" class="form-control" id="name" name="name" required />
        <div class="invalid-feedback">Name cannot be empty.</div>
      </div>

      <div class="mb-3">
        <label for="age" class="form-label">Age</label>
        <input type="number" class="form-control" id="age" name="age" required />
        <div class="invalid-feedback">Age cannot be empty.</div>
      </div>

      <div class="mb-3">
        <label for="ssn" class="form-label">SSN</label>
        <input type="text" class="form-control" id="ssn" name="ssn" required />
        <div class="invalid-feedback">SSN cannot be empty.</div>
      </div>

      <div class="mb-3">
        <label for="phone" class="form-label">Phone Number</label>
        <input type="text" class="form-control" id="phone" name="phone" required />
        <div class="invalid-feedback">Phone Number must be 10 digits.</div>
      </div>

      <div class="mb-3">
        <label for="tour_date" class="form-label">Traveling Date</label>
        <input type="date" class="form-control" id="tour_date" name="tour_date" required />
        <div class="invalid-feedback">Please choose your traveling date.</div>
      </div>

      <div class="mb-3">
        <label for="destination" class="form-label">Destination</label>
        <input type="text" class="form-control" id="destination" name="destination" required />
        <div class="invalid-feedback">Destination cannot be empty.</div>
      </div>

      <button type="submit" class="btn btn-primary" id="submitBtn">Submit</button>
    </form>
    <div id="result" class="d-none"></div>
  </div>
</body>
</html>
