<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "travel_website";

$conn = new mysqli($servername, $username, $password, $dbname);

if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}
echo "Connected successfully! ";  

$name = $_POST['name'];
$age = $_POST['age'];
$ssn = $_POST['ssn'];
$phone = $_POST['phone'];
$tour_date = $_POST['tour_date'];
$destination = $_POST['destination'];


if (strlen($phone) != 10) {
  echo "Please enter 10-digits phone number";
  exit;
}

$sql = "SELECT * FROM booking WHERE ssn='$ssn'";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
  echo "This SSN is booked, please enter another SSN.";
  exit;
}

$sql = "INSERT INTO booking (name, age, ssn, phone, tour_date, destination) VALUES ('$name', '$age', '$ssn', '$phone', '$tour_date', '$destination')";

if ($conn->query($sql) === TRUE) {
  echo "Appointment made!";
} else {
  echo "Error: " . $sql . "<br>" . $conn->error;
}

$conn->close();
?>
