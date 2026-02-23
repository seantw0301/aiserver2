<?php
/**
 * 診斷 LINE API 連接問題
 */

$channelAccessToken = 'hWtckGsIu0S7MqaHRlwsecLxN1Gg1RsAcClX85MRNdo/3mrVFsc1vXN6iZ6UXZfC3x4fd8/Sil0FjQ2qEBRtSCGj9cNuAF/00qvZqdL6cVZVK2zXWnqg/+nf9duQgxrwfTdqTD6z8mIXhJVJj8TMegdB04t89/1O/w1cDnyilFU=';

echo "==========================================\n";
echo "診斷 LINE API 連接問題\n";
echo "==========================================\n\n";

// 測試 1: 檢查 cURL 支援
echo "測試 1: 檢查 cURL 支援\n";
if (function_exists('curl_version')) {
    $version = curl_version();
    echo "✅ cURL 已安裝\n";
    echo "   版本: {$version['version']}\n";
    echo "   SSL 版本: {$version['ssl_version']}\n";
    echo "   支援協議: " . implode(', ', $version['protocols']) . "\n\n";
} else {
    echo "❌ cURL 未安裝\n\n";
    exit(1);
}

// 測試 2: 測試 LINE API 連接（使用簡單的 GET 請求）
echo "測試 2: 測試 LINE API 基本連接\n";
$ch = curl_init('https://api.line.me/v2/bot/info');
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Authorization: Bearer ' . $channelAccessToken
]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_VERBOSE, false);

$result = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($result === FALSE || !empty($error)) {
    echo "❌ 連接失敗\n";
    echo "   錯誤: $error\n\n";
} else if ($httpCode === 200) {
    echo "✅ 連接成功\n";
    echo "   HTTP Code: $httpCode\n";
    echo "   Bot 資訊: $result\n\n";
} else {
    echo "⚠️  連接成功但認證失敗\n";
    echo "   HTTP Code: $httpCode\n";
    echo "   回應: $result\n\n";
}

// 測試 3: 模擬發送訊息（使用測試 reply token）
echo "測試 3: 測試 LINE Reply API\n";
$testReply = [
    'replyToken' => 'test_invalid_token',
    'messages' => [
        [
            'type' => 'text',
            'text' => '測試訊息'
        ]
    ]
];

$ch = curl_init('https://api.line.me/v2/bot/message/reply');
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($testReply));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Authorization: Bearer ' . $channelAccessToken
]);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$result = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
$info = curl_getinfo($ch);
curl_close($ch);

echo "發送測試請求...\n";
if ($result === FALSE || !empty($error)) {
    echo "❌ 發送失敗 (cURL 錯誤)\n";
    echo "   錯誤: $error\n";
    echo "   連接時間: {$info['connect_time']}s\n";
    echo "   總時間: {$info['total_time']}s\n\n";
} else if ($httpCode === 0) {
    echo "❌ HTTP Code 0 - 連接未建立\n";
    echo "   這表示 cURL 無法連接到 LINE API\n";
    echo "   可能原因:\n";
    echo "   1. 網路連接問題\n";
    echo "   2. SSL 證書問題\n";
    echo "   3. 防火牆阻擋\n";
    echo "   4. DNS 解析問題\n\n";
} else if ($httpCode === 400) {
    echo "✅ API 連接正常 (預期的 400 錯誤)\n";
    echo "   HTTP Code: $httpCode\n";
    echo "   說明: 因為使用了無效的 reply token，所以收到 400 錯誤\n";
    echo "   這證明 API 連接和認證都是正常的\n\n";
} else {
    echo "⚠️  收到非預期的回應\n";
    echo "   HTTP Code: $httpCode\n";
    echo "   回應: $result\n\n";
}

// 測試 4: 檢查實際日誌中的問題
echo "測試 4: 分析日誌檔案\n";
if (file_exists('line_bot_log.txt')) {
    $log = file_get_contents('line_bot_log.txt');
    $lines = explode("\n", $log);
    $lastReply = null;
    
    foreach ($lines as $line) {
        if (strpos($line, 'Reply sent') !== false) {
            $lastReply = $line;
        }
    }
    
    if ($lastReply) {
        echo "最後一次發送記錄:\n";
        echo "  $lastReply\n\n";
        
        if (strpos($lastReply, 'HTTP Code: 0') !== false) {
            echo "⚠️  發現 HTTP Code: 0\n";
            echo "   建議檢查:\n";
            echo "   1. 確認伺服器可以連接到 https://api.line.me\n";
            echo "   2. 檢查 SSL 證書是否正常\n";
            echo "   3. 確認沒有防火牆阻擋\n\n";
        }
    }
} else {
    echo "⚠️  找不到日誌檔案\n\n";
}

echo "==========================================\n";
echo "診斷完成\n";
echo "==========================================\n";
?>
