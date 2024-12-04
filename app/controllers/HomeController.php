<?php
class HomeController {
    public function index() {

        $viewPath = realpath(__DIR__ . "/../../public/views/home.php");

        if (!$viewPath || !file_exists($viewPath)) {
            echo "View file not found at: $viewPath<br>";
            exit;
        }

        require_once $viewPath;
    }
}
?>
