<?php
require_once '../model/BookingModel.php';

// 查看请求方法和请求内容
var_dump($_POST);
var_dump(file_get_contents('php://input'));
exit();
// 引入Model文件
require_once '../model/BookingModel.php';

header('Content-Type: application/json');

$input = json_decode(file_get_contents('php://input'), true);

// 如果没有数据或数据不完整，返回错误
if (empty($input['name']) || empty($input['age']) || empty($input['ssn']) || empty($input['phone']) || empty($input['tour_date']) || empty($input['destination'])) {
    echo json_encode(['success' => false, 'message' => 'Missing required fields']);
    exit();
}

// 创建BookingModel实例
$model = new BookingModel();

// 调用model的addBooking方法将数据插入数据库
$result = $model->addBooking($input);

if ($result) {
    echo json_encode(['success' => true]);
} else {
    echo json_encode(['success' => false, 'message' => 'Database error']);
}
?>
