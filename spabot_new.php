<?php
/**
 * LINE Bot Echo Application
 * 
 * This script creates a LINE bot that echoes messages back to the client.
 * It uses the LINE Messaging API to receive and send messages.
 */

// Set error reporting for debugging
ini_set('display_errors', 1);
error_reporting(E_ALL);

// 引用資料庫與語言相關函數
require_once __DIR__ . '/extra.php';

// LINE API credentials For text
//$channelAccessToken = 'wHKonwJZTrxYwh4xEKlTTywpESD41VIg9ntG4LLfhewJJ0lNcS6E0CqLDDKnL+nX84h42MxBz7ZAYzgL4DvMk/5SMoXigRhjlZP8gBVuM9zupqBuw4PCDKedG72J4r30pbxHQOc8hDguc4BAqzEIAQdB04t89/1O/w1cDnyilFU=';
//$channelSecret = 'U9e1ef6b25db771f44e7cd8c579bdfe2a';
// LINE Bot 設定
$channelAccessToken = 'hWtckGsIu0S7MqaHRlwsecLxN1Gg1RsAcClX85MRNdo/3mrVFsc1vXN6iZ6UXZfC3x4fd8/Sil0FjQ2qEBRtSCGj9cNuAF/00qvZqdL6cVZVK2zXWnqg/+nf9duQgxrwfTdqTD6z8mIXhJVJj8TMegdB04t89/1O/w1cDnyilFU=';
$channelSecret = '1799e40b51b185889b986a728f6e4d8c';

// Debug mode configuration - 開發階段設為 true
// 設為 true 時會在回應中顯示完整的自然語言解析結果，方便開發除錯
// 正式環境請設為 false 以避免向用戶顯示技術細節
$debug = false;

/**
 * Call natural language parsing API
 * 調用自然語言解析 API，返回包含 line_messages 的完整結果
 * 
 * @param string $line_key LINE user ID used as session key
 * @param string $userMessage User's message text
 * @return array API response with line_messages
 */
function callNaturalLanguageAPI($line_key, $userMessage) {
    // 使用遠端 API
    $url = 'http://172.105.229.197:5001/parse';
    
    $data = [
        'key' => $line_key,
        'message' => $userMessage
    ];
    
    $postData = json_encode($data);
    
    // 使用 cURL 進行 API 請求，更穩定
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($postData)
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($response === FALSE || !empty($error)) {
        // 記錄錯誤到日誌
        file_put_contents('line_bot_log.txt', 
            date('Y-m-d H:i:s') . " API Call Failed: " . $error . PHP_EOL, 
            FILE_APPEND
        );
        return [
            'error' => 'Failed to call API: ' . $error,
            'line_messages' => [
                [
                    'type' => 'text',
                    'text' => '抱歉，系統暫時無法處理您的請求，請稍後再試。'
                ]
            ]
        ];
    }
    
    if ($httpCode !== 200) {
        // 記錄 HTTP 錯誤到日誌
        file_put_contents('line_bot_log.txt', 
            date('Y-m-d H:i:s') . " API HTTP Error: $httpCode, Response: " . substr($response, 0, 500) . PHP_EOL, 
            FILE_APPEND
        );
        return [
            'error' => "HTTP Error: $httpCode",
            'line_messages' => [
                [
                    'type' => 'text',
                    'text' => '抱歉，系統暫時無法處理您的請求，請稍後再試。'
                ]
            ]
        ];
    }
    
    $result = json_decode($response, true);
    
    // 檢查 JSON 解析是否成功
    if ($result === null && json_last_error() !== JSON_ERROR_NONE) {
        file_put_contents('line_bot_log.txt', 
            date('Y-m-d H:i:s') . " JSON Parse Error: " . json_last_error_msg() . ", Response: " . substr($response, 0, 500) . PHP_EOL, 
            FILE_APPEND
        );
        return [
            'error' => 'Invalid JSON response',
            'line_messages' => [
                [
                    'type' => 'text',
                    'text' => '抱歉，系統暫時無法處理您的請求，請稍後再試。'
                ]
            ]
        ];
    }
    
    // 返回結果，由前端判斷是否有訊息要發送
    return $result;
}

/**
 * 將 LINE Messages 格式化為 LINE SDK Reply 格式
 * 
 * @param string $replyToken LINE reply token
 * @param array $lineMessages line_messages 陣列（從 API 返回）
 * @return array LINE SDK reply format
 */
function formatLineReply($replyToken, $lineMessages) {
    // 確保 lineMessages 是陣列
    if (!is_array($lineMessages)) {
        $lineMessages = [];
    }
    
    // 如果沒有任何訊息，返回空的訊息列表
    if (empty($lineMessages)) {
        return [
            'replyToken' => $replyToken,
            'messages' => []
        ];
    }
    
    // LINE SDK 一次最多發送 5 個訊息
    $messages = array_slice($lineMessages, 0, 5);
    
    return [
        'replyToken' => $replyToken,
        'messages' => $messages
    ];
}

/**
 * 發送 LINE 回覆訊息
 * 
 * @param array $reply LINE reply data
 * @param string $channelAccessToken LINE channel access token
 * @return array Response info with httpCode and result
 */
function sendLineReply($reply, $channelAccessToken) {
    // 檢查是否有訊息要發送
    if (empty($reply['messages'])) {
        file_put_contents('line_bot_log.txt', 
            date('Y-m-d H:i:s') . " No messages to send, skipping LINE reply" . PHP_EOL, 
            FILE_APPEND
        );
        return [
            'httpCode' => 0,
            'result' => 'No messages to send'
        ];
    }
    
    // 記錄即將發送的內容
    file_put_contents('line_bot_log.txt', 
        date('Y-m-d H:i:s') . " Sending to LINE: " . json_encode($reply, JSON_UNESCAPED_UNICODE) . PHP_EOL, 
        FILE_APPEND
    );
    
    $ch = curl_init('https://api.line.me/v2/bot/message/reply');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($reply));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $channelAccessToken
    ]);
    // 禁用 SSL 驗證以避免證書問題（僅在必要時使用）
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
    
    $curl_result = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);
    
    // 詳細記錄發送結果
    if ($curl_result === FALSE || !empty($curl_error)) {
        file_put_contents('line_bot_log.txt', 
            date('Y-m-d H:i:s') . " LINE Reply FAILED - cURL Error: $curl_error" . PHP_EOL, 
            FILE_APPEND
        );
    } else if ($httpCode !== 200) {
        file_put_contents('line_bot_log.txt', 
            date('Y-m-d H:i:s') . " LINE Reply FAILED - HTTP Code: $httpCode, Response: $curl_result" . PHP_EOL, 
            FILE_APPEND
        );
    } else {
        file_put_contents('line_bot_log.txt', 
            date('Y-m-d H:i:s') . " LINE Reply SUCCESS - HTTP Code: $httpCode" . PHP_EOL, 
            FILE_APPEND
        );
    }
    
    return [
        'httpCode' => $httpCode,
        'result' => $curl_result,
        'error' => $curl_error
    ];
}

// Get request content
$content = file_get_contents('php://input');
$events = json_decode($content, true);

// Log received data for debugging
file_put_contents('line_bot_log.txt', date('Y-m-d H:i:s') . " Received: " . $content . PHP_EOL, FILE_APPEND);

// Process each event
if (!empty($events['events'])) {
    foreach ($events['events'] as $event) {
        // 處理語言切換 postback（set_lang=）
        if ($event['type'] == 'postback' && isset($event['postback']['data'])) {
            $line_key = $event['source']['userId'];
            $replyToken = $event['replyToken'];
            $postback_data = $event['postback']['data'];
            $reply = handleLanguagePostback($line_key, $postback_data, $replyToken);
            if ($reply) {
                sendLineReply($reply, $channelAccessToken);
            }
            continue;
        }
        
        // 處理 message event 指令顯示語言選單 menu
        if ($event['type'] == 'message' && $event['message']['type'] == 'text') {
            $userMessage = $event['message']['text'];
            $replyToken = $event['replyToken'];
            $line_key = $event['source']['userId'];
            
            // 檢查是否為語言設置指令
            $command_keywords = ['set lang', 'set language', '語言設置', 'setup lang', 'setup language'];
            $is_lang_command = false;
            foreach ($command_keywords as $kw) {
                if (stripos($userMessage, $kw) === 0) {
                    $is_lang_command = true;
                    break;
                }
            }
            
            if ($is_lang_command) {
                $reply = makeFelixLanguageMenu($replyToken);
                sendLineReply($reply, $channelAccessToken);
                continue;
            }
            
            // ==========================================
            // 簡化流程：直接調用 API 並使用返回的 line_messages
            // ==========================================
            
            // 記錄收到的訊息
            file_put_contents('line_bot_log.txt', 
                date('Y-m-d H:i:s') . " User: $line_key, Message: $userMessage" . PHP_EOL, 
                FILE_APPEND
            );
            
            // 1. 調用自然語言解析 API（包含六階段處理）
            $apiResult = callNaturalLanguageAPI($line_key, $userMessage);
            
            // 記錄 API 返回結果
            file_put_contents('line_bot_log.txt', 
                date('Y-m-d H:i:s') . " API Result: " . json_encode($apiResult, JSON_UNESCAPED_UNICODE) . PHP_EOL, 
                FILE_APPEND
            );
            
            // 2. 直接使用 API 返回的 line_messages
            $lineMessages = $apiResult['line_messages'] ?? [];
            
            // 若沒有任何訊息，則直接忽略（不回應垃圾訊息）
            if (empty($lineMessages)) {
                file_put_contents('line_bot_log.txt', 
                    date('Y-m-d H:i:s') . " Empty response, no reply sent." . PHP_EOL, 
                    FILE_APPEND
                );
                continue;
            }
            
            // 3. 格式化並發送 LINE 回覆
            $reply = formatLineReply($replyToken, $lineMessages);
            sendLineReply($reply, $channelAccessToken);
        }
    }
}
?>
