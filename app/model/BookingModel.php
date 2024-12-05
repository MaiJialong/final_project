<?php
class BookingModel {
    private $host = 'localhost';
    private $db = 'booking_db';  // 请根据实际情况修改数据库名称
    private $user = 'root';       // 请根据实际情况修改数据库用户名
    private $pass = '';           // 请根据实际情况修改数据库密码
    private $conn;

    public function __construct() {
        $this->conn = new mysqli($this->host, $this->user, $this->pass, $this->db);

        if ($this->conn->connect_error) {
            die("Connection failed: " . $this->conn->connect_error);
        }
    }

    public function addBooking($data) {
        // 防止SQL注入
        $name = $this->conn->real_escape_string($data['name']);
        $age = (int)$data['age'];
        $ssn = $this->conn->real_escape_string($data['ssn']);
        $phone = $this->conn->real_escape_string($data['phone']);
        $tourDate = $this->conn->real_escape_string($data['tour_date']);
        $destination = $this->conn->real_escape_string($data['destination']);

        $sql = "INSERT INTO bookings (name, age, ssn, phone, tour_date, destination) VALUES ('$name', $age, '$ssn', '$phone', '$tourDate', '$destination')";

        if ($this->conn->query($sql) === TRUE) {
            return true;
        } else {
            return false;
        }
    }
    public function getAllBookings() {
        $sql = "SELECT * FROM bookings";
        $result = $this->conn->query($sql);

        $bookings = [];
        if ($result->num_rows > 0) {
            while ($row = $result->fetch_assoc()) {
                $bookings[] = $row;
            }
        }

        return $bookings;
    }
}
?>
