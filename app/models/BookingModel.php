<?php
require_once "db.php";

class Booking {
    private $conn;

    public function __construct() {
        $database = new Database();
        $this->conn = $database->connect();
    }

    public function createBooking($data) {
        $query = "INSERT INTO booking (name, age, ssn, phone, tour_date, destination) VALUES (:name, :age, :ssn, :phone, :tour_date, :destination)";
        $stmt = $this->conn->prepare($query);
        $stmt->execute($data);
        return $stmt->rowCount();
    }

    public function getBookingBySSN($ssn) {
        $query = "SELECT * FROM booking WHERE ssn = :ssn";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':ssn', $ssn);
        $stmt->execute();
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }
}
?>
