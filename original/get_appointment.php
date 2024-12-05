<?php

$servername = "localhost";
$username = "root";  
$password = "";  
$dbname = "travel_website";  


$conn = new mysqli($servername, $username, $password, $dbname);


if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

$ssn = $_GET['ssn'];


$sql = "SELECT * FROM booking WHERE ssn = '$ssn'";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
  $row = $result->fetch_assoc();
  $response = array(
    "success" => true,
    "name" => $row['name'],
    "age" => $row['age'],
    'phone' => $row['phone'],
    "tour_date" => $row['tour_date'],
    "destination" => $row['destination']
  );
} else {

  $response = array("success" => false);
}


header('Content-Type: application/json');


echo json_encode($response);

$conn->close();
?>
