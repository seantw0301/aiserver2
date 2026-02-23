<?php

// 處理 postback event 設置語言
function handleLanguagePostback($line_id, $postback_data, $replyToken) {
    if (strpos($postback_data, 'set_lang=') === 0) {
        $lang_code = substr($postback_data, strlen('set_lang='));
        // 呼叫 API 設置語言
        $api_url = 'http://localhost:5001/line-user/set-language';
        $post = json_encode(['line_user_id' => $line_id, 'language' => $lang_code]);
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => "Content-Type: application/json\r\n",
                'content' => $post,
                'timeout' => 10
            ]
        ]);
        $response = file_get_contents($api_url, false, $context);
        $json = json_decode($response, true);
        $success = $json['success'] ?? false;
        // 回覆訊息
        $msg = $success ? '語言設置成功！' : '語言設置失敗，請稍後再試。';
        return [
            'replyToken' => $replyToken,
            'messages' => [
                [
                    'type' => 'text',
                    'text' => $msg
                ]
            ]
        ];
    }
    return null;
}

// 產生Felix語言選單訊息
function makeFelixLanguageMenu($replyToken) {
    $lang_options = get_language_options();
    $per_bubble = 3;
    $bubbles = [];
    $lang_keys = array_keys($lang_options);
    $lang_labels = array_values($lang_options);
    $total = count($lang_options);
    $bubble_count = ceil($total / $per_bubble);
    for ($i = 0; $i < $bubble_count; $i++) {
        $actions = [];
        for ($j = 0; $j < $per_bubble; $j++) {
            $idx = $i * $per_bubble + $j;
            if ($idx >= $total) break;
            $actions[] = [
                'type' => 'postback',
                'label' => $lang_labels[$idx],
                'data' => 'set_lang=' . $lang_keys[$idx]
            ];
        }
        // 補足 actions 到 3 個
        while (count($actions) < $per_bubble) {
            $actions[] = [
                'type' => 'postback',
                'label' => '-',
                'data' => 'noop'
            ];
        }
        $bubbles[] = [
            'type' => 'buttons',
            'title' => '語言選擇',
            'text' => '請選擇您的語言',
            'actions' => $actions
        ];
    }
        return [
            'replyToken' => $replyToken,
            'messages' => [
                [
                    'type' => 'template',
                    'altText' => '請選擇語言',
                    'template' => [
                        'type' => 'carousel',
                        'columns' => $bubbles
                    ]
                ]
            ]
        ];
}
// 處理語言選單分頁 postback
function handleLanguageMenuPage($replyToken, $postback_data) {
    if (strpos($postback_data, 'lang_page=') === 0) {
        $page = intval(substr($postback_data, strlen('lang_page=')));
        return makeFelixLanguageMenu($replyToken, $page);
    }
    return null;
}
// extra.php
// MySQL 連線設定
function get_db_connection() {
    $host = 'api.ilivecc.com';
    $user = 'seantw';
    $password = 'Aa23885108';
    $database = 'senspa_sch';
    $conn = new mysqli($host, $user, $password, $database);
    if ($conn->connect_error) {
        die('資料庫連線失敗: ' . $conn->connect_error);
    }
    $conn->set_charset('utf8mb4');
    return $conn;
}

// 檢查 LINE user 是否已設置語言
function check_user_language($line_id) {
    $conn = get_db_connection();
    $stmt = $conn->prepare('SELECT language FROM line_users WHERE line_id = ?');
    $stmt->bind_param('s', $line_id);
    $stmt->execute();
    $stmt->bind_result($language);
    $result = null;
    if ($stmt->fetch()) {
        $result = $language;
    }
    $stmt->close();
    $conn->close();
    return $result;
}

// 設置 LINE user 的語言
function set_user_language($line_id, $language) {
    $conn = get_db_connection();
    $stmt = $conn->prepare('UPDATE line_users SET language = ? WHERE line_id = ?');
    $stmt->bind_param('ss', $language, $line_id);
    $success = $stmt->execute();
    $stmt->close();
    $conn->close();
    return $success;
}

// 可選語言列表
function get_language_options() {
    return [
        'zh-TW' => '繁體中文',
        'zh-CN' => '簡體中文',
        'en'    => '英文',
        'ja'    => '日文',
        'ko'    => '韓文',
        'th'    => '泰文',
        'es'    => '西班牙文',
        'ms'    => '馬來文',
        'vi'    => '越南文'
    ];
}
