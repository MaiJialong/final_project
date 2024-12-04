<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Find Your Trip</title> 
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="/final-project/public/js/checking.js"></script>
    <style>
        body {
            background-image: url('../images/富士山.jpg');
            background-size: cover;
            background-position: center;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
    <h1 class="text-center">Check Your Trip</h1>
    <form id="checkingForm">
        <div class="mb-3">
            <label for="ssn" class="form-label">SSN</label>
            <input type="text" id="ssn" class="form-control" placeholder="Enter your SSN">
        </div>
        <div>
            <button type="submit" id="submitBtn" class="btn btn-primary">Check</button>
        </div>
        </form>
    <div id="result" class="result"></div>
    </div>
</body>
</html>

