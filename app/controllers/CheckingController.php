<?php
require_once "../app/models/BookingModel.php";

class CheckingController {
    public function check() {
        header('Content-Type: application/json; charset=utf-8'); 
        $ssn = $_GET['ssn'] ?? null;
    
        if (!$ssn) {
            echo json_encode(["success" => false, "message" => "SSN is required."]);
            return;
        }
        $booking = new Booking(); 
        $result = $booking->getBookingBySSN($ssn);

        if ($result) {
            echo json_encode(["success" => true, "data" => $result]);
        } else {
            echo json_encode(["success" => false, "message" => "No booking found for the provided SSN."]);
        }
    }

    public function view() {
        require_once "../public/views/checking.php";
    }
}
?>
