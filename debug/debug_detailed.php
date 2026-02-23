<?php
/**
 * 詳細調試 API 請求問題
 */

// 啟用錯誤報告
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "=== 詳細 API 調試 ===\n";

$url = 'http://localhost:5001/appointments/query';
$queryData = [
    'branch' => '西門',
    'masseur' => [],
    'date' => '2025/08/22',
    'time' => '15:00',
    'project' => 90,
    'count' => 1
];

$postData = json_encode($queryData, JSON_UNESCAPED_UNICODE);
echo "請求 URL: $url\n";
echo "請求數據: $postData\n\n";

// 使用 cURL 進行更詳細的調試
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Content-Length: ' . strlen($postData)
]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 45);
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
curl_setopt($ch, CURLOPT_VERBOSE, true);

// 捕獲詳細輸出
$verboseOutput = fopen('php://temp', 'w+');
curl_setopt($ch, CURLOPT_STDERR, $verboseOutput);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);

rewind($verboseOutput);
$verboseLog = stream_get_contents($verboseOutput);
fclose($verboseOutput);

curl_close($ch);

echo "HTTP 狀態碼: $httpCode\n";

if ($error) {
    echo "❌ cURL 錯誤: $error\n";
} else {
    echo "✅ cURL 執行成功\n";
}

if ($response !== false) {
    echo "✅ 收到響應:\n";
    $result = json_decode($response, true);
    if ($result) {
        echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
    } else {
        echo "原始響應: $response\n";
    }
} else {
    echo "❌ 沒有收到響應\n";
}

echo "\n--- 詳細連接日誌 ---\n";
echo $verboseLog;

// 也測試 file_get_contents 方法
echo "\n=== 測試 file_get_contents 方法 ===\n";

$context = stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\n",
        'content' => $postData,
        'timeout' => 45
    ]
]);

$startTime = microtime(true);
$response2 = @file_get_contents($url, false, $context);
$endTime = microtime(true);
$duration = $endTime - $startTime;

echo "執行時間: " . number_format($duration, 2) . " 秒\n";

if ($response2 === FALSE) {
    echo "❌ file_get_contents 失敗\n";
    $error = error_get_last();
    if ($error) {
        echo "錯誤: " . $error['message'] . "\n";
    }
    
    if (isset($http_response_header)) {
        echo "HTTP 響應頭:\n";
        foreach ($http_response_header as $header) {
            echo "  $header\n";
        }
    }
} else {
    echo "✅ file_get_contents 成功\n";
    echo "響應: " . substr($response2, 0, 200) . "...\n";
}
?>
