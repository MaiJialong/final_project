<?php
require __DIR__ . "/../app/controllers/HomeController.php";
require __DIR__ . "/../app/controllers/CheckingController.php";
require __DIR__ . "/../app/controllers/BookingController.php";

$controller = $_GET['controller'] ?? 'home';
$action = $_GET['action'] ?? 'index';

try {
    switch ($controller) {
        case 'home':
            $controllerInstance = new HomeController();
            break;
        case 'checking':
            $controllerInstance = new CheckingController();
            break;
        case 'booking':
            $controllerInstance = new BookingController();
            break;
        default:
            throw new Exception("Controller '$controller' not found");
    }

    if (!method_exists($controllerInstance, $action)) {
        throw new Exception("Action '$action' not found in controller '$controller'");
    }
    
    $controllerInstance->$action();
} catch (Exception $e) {
    http_response_code(500);
    echo "Internal Server Error: " . $e->getMessage();
}
?>