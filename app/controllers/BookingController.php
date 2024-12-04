<?php
require_once "../app/models/BookingModel.php";
class BookingController {
    public function create() {
        header('Content-Type: application/json; charset=utf-8'); 
        $input = file_get_contents("php://input");
        $data = json_decode($input, true);
    
        $name = trim($_POST['name'] ?? '');
        $age = intval($_POST['age'] ?? 0);
        $ssn = trim($_POST['ssn'] ?? '');
        $phone = trim($_POST['phone'] ?? '');
        $tour_date = trim($_POST['tour_date'] ?? '');
        $destination = trim($_POST['destination'] ?? '');
          

        if (empty($data['name']) || empty($data['ssn']) || empty($data['phone']) || empty($data['tour_date']) || empty($data['destination'])) 
        {
            echo json_encode(["success" => false, "message" => "All fields are required!"]);
            exit;
        }
        $booking = new Booking();
        $result = $booking->createBooking($data);
    
        if ($result) {
            echo json_encode(["success" => true, "message" => "Booking successful!"]);
        } else {
            echo json_encode(["success" => false, "message" => "Failed to create booking."]);
        }
    }

    public function view() {
        require_once "../public/views/booking.php";
    }
}
?>
