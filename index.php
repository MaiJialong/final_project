<?php
// Include the controller
require './app/Controller/MainPageController.php';
require './app/Controller/AppointmentController.php';
require './app/Controller/BookingController.php';

// Routing logic
$controller = new MainPageController();
$controller->showMainPage();

$model = new BookingModel();
$bookings = $model->getAllBookings();

?>

