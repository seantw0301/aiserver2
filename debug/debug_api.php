<?php
/**
 * 調試 API 請求
 */

// 模擬 spabot_demo.php 中的查詢
$url = 'http://localhost:5001/appointments/query';

$queryData = [
    'branch' => '西門',
    'masseur' => [],
    'date' => '2025/08/22',
    'time' => '15:00',
    'project' => 90,
    'count' => 1
];

echo "=== 調試 API 請求 ===\n";
echo "URL: $url\n";
echo "查詢資料:\n";
echo json_encode($queryData, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n\n";

$postData = json_encode($queryData, JSON_UNESCAPED_UNICODE);
echo "POST Data: $postData\n\n";

$context = stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\n",
        'content' => $postData,
        'timeout' => 60
    ]
]);

// 捕獲錯誤
$response = @file_get_contents($url, false, $context);

if ($response === FALSE) {
    echo "❌ 請求失敗\n";
    $error = error_get_last();
    echo "錯誤詳情: " . $error['message'] . "\n";
    
    // 檢查 HTTP 響應頭
    if (isset($http_response_header)) {
        echo "HTTP 響應頭:\n";
        foreach ($http_response_header as $header) {
            echo "  $header\n";
        }
    }
} else {
    echo "✅ 請求成功\n";
    $result = json_decode($response, true);
    echo "響應結果:\n";
    echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
}
?>
