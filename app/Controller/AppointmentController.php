<?php
require 'app/model/AppointmentModel.php';

class AppointmentController {
    public function getAppointment() {
        if (isset($_GET['ssn'])) {
            $ssn = $_GET['ssn'];

            $response = getAppointmentBySSN($ssn); 

            echo json_encode($response);
        } else {
            echo json_encode(array("success" => false, "message" => "SSN is required"));
        }
    }

    public function getAppointmentBySSN($ssn)
    {
    }
}
?>
