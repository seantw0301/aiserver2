<?php
    $sname[1]='禪風西門店';
    $sname[2]='禪風延吉店';
    function get_chinese_weekday($datetime)
    {
        $weekday = date('w', strtotime($datetime));
        return "(". ['日', '一', '二', '三', '四', '五', '六'][$weekday].")";
    }
    function make_semiangle($str)
    {
        $arr = array('０' => '0', '１' => '1', '２' => '2', '３' => '3', '４' => '4',
        '５' => '5', '６' => '6', '７' => '7', '８' => '8', '９' => '9',
        'Ａ' => 'A', 'Ｂ' => 'B', 'Ｃ' => 'C', 'Ｄ' => 'D', 'Ｅ' => 'E',
        'Ｆ' => 'F', 'Ｇ' => 'G', 'Ｈ' => 'H', 'Ｉ' => 'I', 'Ｊ' => 'J',
        'Ｋ' => 'K', 'Ｌ' => 'L', 'Ｍ' => 'M', 'Ｎ' => 'N', 'Ｏ' => 'O',
        'Ｐ' => 'P', 'Ｑ' => 'Q', 'Ｒ' => 'R', 'Ｓ' => 'S', 'Ｔ' => 'T',
        'Ｕ' => 'U', 'Ｖ' => 'V', 'Ｗ' => 'W', 'Ｘ' => 'X', 'Ｙ' => 'Y',
        'Ｚ' => 'Z', 'ａ' => 'a', 'ｂ' => 'b', 'ｃ' => 'c', 'ｄ' => 'd',
        'ｅ' => 'e', 'ｆ' => 'f', 'ｇ' => 'g', 'ｈ' => 'h', 'ｉ' => 'i',
        'ｊ' => 'j', 'ｋ' => 'k', 'ｌ' => 'l', 'ｍ' => 'm', 'ｎ' => 'n',
        'ｏ' => 'o', 'ｐ' => 'p', 'ｑ' => 'q', 'ｒ' => 'r', 'ｓ' => 's',
        'ｔ' => 't', 'ｕ' => 'u', 'ｖ' => 'v', 'ｗ' => 'w', 'ｘ' => 'x',
        'ｙ' => 'y', 'ｚ' => 'z', '（' => '(', '）' => ')', '〔' => '[', '〕' => ']', '【' => '[',
        '】' => ']', '〖' => '[', '〗' => ']', '“' => '[', '”' => ']','‘' => '[', '\'' => ']', '｛' => '{', '｝' => '}', '《' => '<',
        '》' => '>', '％' => '%', '＋' => '+', '—' => '-', '－' => '-', '～' => '-',        '：' => ':', '。' => '.', '、' => ',', '，' => '.', '、' => '.',
        '；' => ',', '？' => '?', '！' => '!', '…' => '-', '‖' => '|', '”' => '"', '\'' => '`', '‘' => '`', '｜' => '|', '〃' => '"', '　' => ' ');
        return strtr($str, $arr);
    }


    function isAdmin($db,$storeid,$userid)
    {
                    $isAdmin=false;
                    $sql="Select * from Staffs where `line_userid`='$userid' and `storeid`=$storeid";
                    $result = $db->query( $sql );
                    if( $result->rowCount() === 0 )
                    {
                        return false;
                    }
                    else
                    {
                        $row=$result->fetch(PDO::FETCH_OBJ);
                        $iAdmin=$row->isAdmin;
                        if($iAdmin==1)
                        {
                            return true;
                        } else {
                            return false;
                        }
                    }
    }
    function getMemDB($db,$storeid)
    {
                    $sql="Select * from Store where `id`=$storeid";
                    $result = $db->query( $sql );
                    if( $result->rowCount() === 0 )
                    {
                        return 0;
                    }
                    else
                    {
                        $row=$result->fetch(PDO::FETCH_OBJ);
                        $memdb=$row->memdb;
                        return $memdb;
                    }
    }


    function getPRcount($db,$storeid,$staff_id) //取得剩下的公關次數
    {
	//echo $staff_id;
	$iMax=0;
	$sql = "Select * from Staffs where `storeid`=$storeid and `id`=$staff_id";
	//echo $sql;
 	$result = $db->query( $sql );											 								   
	if($row=$result->fetch(PDO::FETCH_OBJ)){ 	
		$iMax=$row->max_pr;					    
	}
	//echo $iMax;

	$startd=date("Y/m/01 00:00:00");
	$effectiveDate = strtotime("+1 months", strtotime($startd));
	$endd=date("Y/m/01 00:00:00",$effectiveDate);

	$iCnt=0;
	$sql = "Select count(*) as cnt from Tasks where `storeid`=$storeid and `staff_id`=$staff_id and `usetickettype`=2 and `start` >= '$startd' and `start` < '$endd'";
	//echo $sql;
 	$result = $db->query( $sql );
	if($row=$result->fetch(PDO::FETCH_OBJ)){ 	
		$iCnt=$row->cnt;					    
	}
	
        $iRest=$iMax-$iCnt;
	return $iRest;

    }

    function isAdminByStaffid($db,$storeid,$staffid)
    {
                    $isAdmin=false;
                    $sql="Select * from Staffs where `id`=$staffid and `storeid`=$storeid";
                    $result = $db->query( $sql );
                    if( $result->rowCount() === 0 )
                    {
                        return false;
                    }
                    else
                    {
                        $row=$result->fetch(PDO::FETCH_OBJ);
                        $iAdmin=$row->isAdmin;
			if($iAdmin==1)
			{
				return true;
			} else {
				return false;
			}

                    }

    }



    function checkLicense($db,$storekey)
    {
        $sql="Select * from Store where `key`='$storekey'";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

        $row=$result->fetch(PDO::FETCH_OBJ);
        $GLOBALS['storeid']=$row->id;
        $GLOBALS['storename']=$row->name;

        return true;
    };

    function getTags($userid, $lineConfig = null)
    {
        // Use global constants if no config provided
        $ca[1]= 'V8ARZ8gLtvdD8/hbu437US2cTifjmhhg28LaB1rjTpjMAzNOh+fMt0s1Ttn704nrvmoLk/GzjaAJWRcfhgjRm4Oy/WyFkLi/meVu1Ia+A42z/E5441Kg0198ajRmO6HvmEGRQj23+ol9cs0UOwyoewdB04t89/1O/w1cDnyilFU=';

        if (!$lineConfig) {
            $lineConfig = [
                'channel_access_token' => $ca[1]
            ];
        }

        // Validate user ID
        if (empty($userid)) {
            return "Error: User ID is required";
        }

        // Set timeout to avoid script hanging
        $timeout = 10;

        // Use the correct endpoint for getting user tags directly
        $apiUrl = "https://api-data.line.me/v2/bot/user/{$userid}/tag";
        $ch = curl_init($apiUrl);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Authorization: Bearer ' . $lineConfig['channel_access_token']
        ]);
        
        $result = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlError = curl_error($ch);
        curl_close($ch);
        
        // Handle API response
        if ($httpCode == 200) {
            // Successfully got the tags
            $tagData = json_decode($result, true);
            $tags = [];
            
            if (isset($tagData['tags']) && is_array($tagData['tags'])) {
                foreach ($tagData['tags'] as $tag) {
                    if (isset($tag['tag'])) {
                        $tags[] = $tag['tag'];
                    }
                }
            }
            
            return implode(', ', $tags);
        } elseif ($httpCode == 404) {
            // User has no tags, this is a normal case
            return "No tags found for this user";
        } else {
            // Return detailed error for debugging
            $errorMessage = "API Error: HTTP Status {$httpCode}";
            
            if (!empty($curlError)) {
                $errorMessage .= ", cURL Error: {$curlError}";
            }
            
            if (!empty($result)) {
                $errorData = json_decode($result, true);
                if (isset($errorData['message'])) {
                    $errorMessage .= ", Message: {$errorData['message']}";
                } else {
                    $errorMessage .= ", Response: {$result}";
                }
            }
            
            return "Error: " . $errorMessage;
        }
    }

    function regStaff($db,$name,$password,$userid,$storeid)
    {
        $sql="update Staffs set `line_userid`='$userid' where `name`='$name' and `password`='$password' and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        return true;
    };

    function regGroup($db,$groupId)
    {
        $sql="Insert into GroupRoom values(default,'$groupId')";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        return true;
    };

   function getLatestMember($db,$memdb)
   {
	$sql = "Select * from member where `storeid`=$memdb order by memberid desc limit 0,1";
	$result = $db->query( $sql );
	if($row=$result->fetch(PDO::FETCH_OBJ)){ 
		return $row->memberid;
	}
	else
	{
		return 0;
	}
   }

   function addMember($db,$storeid,$memberid,$name)
   {
	$sql = "Select * from member where `storeid`=$storeid and `memberid`=$memberid"; 
	$result = $db->query( $sql );											 								   
	if($row=$result->fetch(PDO::FETCH_OBJ)){ 
		return 0;						    
	}
	else
	{
		$sql = "Insert into member values(default,$storeid,'$memberid','$name','','')"; 
		$result = $db->query( $sql );
		return 1;	
	}


  
      };


    function addMessage($db,$storeid,$message)
    {
        $sql="Insert into PublicMessage values(default,'$message',$storeid)";
        //return $sql; 
        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        return true;
        
    };

    function modMessage($db,$storeid,$message,$id)
    {

        $sql="Update PublicMessage set `message`='$message' where `storeid`=$storeid and id=$id";
        //return $sql;
        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        return true;
    };

    function delMessage($db,$storeid,$id)
    {
        $sql="Delete from PublicMessage where `storeid`=$storeid and id=$id ";
        //return $sql;
        $result = $db->query( $sql );
        return true;
    };

    function over2100($indate) {
	    $appointmentTime = strtotime($indate);
	    $appointmentDate = date('Y-m-d', $appointmentTime);
	    $limitTime = strtotime($appointmentDate . ' 21:00:00');
	    
	    return $appointmentTime >= $limitTime;
	}

    function addBook01($db,$bookdate, $customer_name,$course_id, $name,$note,$storeid,$exdata,$memberid)
    {
        //Get staff data 
        $sql="Select * from Staffs where `name`='$name' and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

        $row=$result->fetch(PDO::FETCH_OBJ);
        $staffid=$row->id;
        $profit=$row->profit;

           //Get Course Type data
        $sql="Select * from Course where `id`=$course_id and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

        $row=$result->fetch(PDO::FETCH_OBJ);
        $c_name=$row->name;
        $c_price=$row->price;
        $c_masseur= round( $c_price * $profit / 100 );
        //如果超過21:00則會加150元
        if(over2100($bookdate)){
            if ($row->mins == 60){
                $c_masseur = $c_masseur + 100;
            } else {
                $c_masseur = $c_masseur + 150;
            }
        }


        $c_company=$row->price - $c_masseur;
        $c_mins=$row->mins;


        $starttime=strtotime("$bookdate");
        $endtime = strtotime("$bookdate + $c_mins minutes");
        $st=date("Y-m-d H:i:s",$starttime);
        $et=date("Y-m-d H:i:s",$endtime);
        $sql="Insert into Tasks values(default,'$customer_name','$st','$et',$staffid,$course_id,$c_price,0,$c_masseur,$c_company,'',0,$c_mins,$storeid,'$name','$note','$c_name','$exdata','','$memberid','',0,0,0,0,0)";

        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        $taskId=$db->lastInsertId();
        sendNewTaskMessage($db, $taskId);
        return true;
    };

    function modBook01($db,$bookdate, $customer_name,$course_id, $name,$note,$storeid,$id,$exdata,$history,$memberid,$history_pri)
    {
        //Get Old Book data
        $sql="Select * from Tasks where id=$id";
        $result = $db->query( $sql );
        $row=$result->fetch(PDO::FETCH_OBJ);
        $oldname=$row->staff_name;
        if($oldname != $name) //如果修改了師傅
        {
            sendDelTaskMessage($db,$id);
        }

        //Get staff id 
        $sql="Select * from Staffs where `name`='$name' and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

        $row=$result->fetch(PDO::FETCH_OBJ);
        $staffid=$row->id;
        $profit=$row->profit;

        //Get Course Type data
        $sql="Select * from Course where `id`=$course_id and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

        $row=$result->fetch(PDO::FETCH_OBJ);
        $c_name=$row->name;
        $c_price=$row->price;
        $c_masseur= round( $c_price * $profit / 100 );
        //如果超過21:00則會加150元
        if(over2100($bookdate)){
            if ($row->mins == 60){
                $c_masseur = $c_masseur + 100;
            } else {
                $c_masseur = $c_masseur + 150;
            }
        }
        $c_company=$row->price - $c_masseur;
        $c_mins=$row->mins;


        $starttime=strtotime("$bookdate");
        $endtime = strtotime("$bookdate + $c_mins minutes");
        $st=date("Y-m-d H:i:s",$starttime);
        $et=date("Y-m-d H:i:s",$endtime);
        $sql="Update Tasks set `customer_name`='$customer_name',`start`='$st',`end`='$et',`staff_id`=$staffid,`course_id`=$course_id,`price`=$c_price,`master_income`=$c_masseur,`company_income`=$c_company,`mins`=$c_mins,`staff_name`='$name',`note`='$note',`exdata`='$exdata',`history`='$history',`memberid`='$memberid',`history_pri`='$history_pri',`is_confirmed`=0 where `storeid`=$storeid and id=$id";
        //return $sql;

        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        sendEditTaskMessage($db,$id);
        return true;
    };


    function addBook($db,$date, $customer_name, $start, $mins, $name,$note,$storeid)
    {
    	 //Get staff id 
    	$sql="Select * from Staffs where `name`='$name' and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

        $row=$result->fetch(PDO::FETCH_OBJ);
        $staffid=$row->id;


        $starttime=strtotime("$date $start");
        $endtime = strtotime("$date $start + $mins minutes");
        $st=date("Y-m-d H:i:s",$starttime);
        $et=date("Y-m-d H:i:s",$endtime);
        $sql="Insert into Tasks values(default,'$customer_name','$st','$et',$staffid,0,0,0,0,0,'',0,$mins,$storeid,'$name','$note',default)";

        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        return true;
    };

    function addPreBook($db)
    {
        foreach ($_POST as $key => $value) {
            $$key=$value;  
        }

        $sql="Select * from prebook where line_userid='$line_userid' and process_status <> -1";
        $result = $db->query( $sql );
        if( $result->rowCount() > 0)
        {
            return false;
        }



        $sql="Insert into prebook values(default,'$line_userid','$line_name',$total_user,'$book_date','$course','$masseur0_0','$masseur1_0','$masseur2_0','$oiltype0','','$masseur0_1','$masseur1_1','$masseur2_1','$oiltype1','','$masseur0_2','$masseur1_2','$masseur2_2','$oiltype2','','$masseur0_3','$masseur1_3','$masseur2_3','$oiltype3','',default,0)";

        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        return true;
    };


    function modBook($db,$date, $customer, $start, $mins, $name,$note, $id,  $storeid)
    {
        //Get staff id 
    	$sql="Select * from Staffs where `name`='$name' and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

        $row=$result->fetch(PDO::FETCH_OBJ);
        $staffid=$row->id;


        $starttime=strtotime("$date $start");
        $endtime = strtotime("$date $start + $mins minutes");
        $st=date("Y-m-d H:i:s",$starttime);
        $et=date("Y-m-d H:i:s",$endtime);
        $sql="Update Tasks set `customer_name`='$customer',`start`='$st',`end`='$et',`staff_id`=$staffid,`mins`=$mins,`staff_name`='$name',`note`='$note' where `storeid`=$storeid and id=$id";
        //return $sql;

        $result = $db->query( $sql );
        if( $result->rowCount() === 0)
        {
            return false;
        }
        return true;
    };

    function delBook($db,$id, $storeid)
    {
        sendDelTaskMessage($db,$id);
        $sql="Delete from Tasks where `storeid`=$storeid and id=$id ";
       
        $result = $db->query( $sql );

        return true;
    };

    function getBook($db,$storeid,$where='',$showsn=false,$isAdmin=false,$showvip=false)
    {
        $income_company=0;
        $income_staff=0;
        
        //$isAdmin=false;
    	//$nowdate = date("Y-m-d 00:00:00");
    	$sql = "Select * from Tasks where `storeid`=$storeid and ".$where; //and `start` >= '$nowdate'";
    	//if( $where != '')
    	//{
    	//	$sql = $sql . " and $where";
    	//}

    	$sql = $sql . " order by `start`";
    	//return $sql;



        //$sql="Select * from Staffs where `storeid`=$storeid and `enable`=1";
        $oldday="";
        $addSpace=true;
        $result = $db->query( $sql );
        $reply="[".$GLOBALS['storename']."預約]\r\n";
        while($row=$result->fetch(PDO::FETCH_OBJ)){   

            $starttime=strtotime($row->start);
        	$st1=date("n/j",$starttime);
        	$st2=date("H:i",$starttime);
        	if( $oldday !== $st1) {
        		$oldday=$st1;
        		$reply .=$st1."\r\n";
		}
		//if($oldday !== $st1 && $addSpace){
                //	$addSpace=false;
        	//}

            $customer_name=$row->customer_name;
            if(!$isAdmin)
            {
                $customer_name=mb_substr($customer_name,0,1,"UTF-8")."**";
            }

            if($showvip)
            {
                $customer_name=$customer_name."($row->memberid)";
            }
            $price=0;
            $income_company_tmp =  0;
            $income_staff_tmp = 0;
            try{
                    $price=$row->price; //價格
                    $tmp_c=($price * 0.5 - 70);
                    $tmp_s=($price * 0.5 + 70);
                    $income_company = $income_company + $tmp_c;
                    $income_staff = $income_staff + $tmp_s;
                    $income_company_tmp = $tmp_c;
                    $income_staff_tmp = $tmp_s;
            }
            catch(Exception $e){
                
            }
            
            if($showsn)
            {
                $reply .= "[".$row->id."] ".$st2 ." " .$customer_name." " .$row->mins." ".$row->staff_name." ".$row->note."\r\n"; //."($income_staff_tmp/$income_company_tmp)\r\n";
            }
            else
            {
                $reply .= $st2 ." " .$customer_name." ".$row->mins." ".$row->staff_name." ".$row->note."($income_staff_tmp/$income_company_tmp)\r\n";

            }
        }

        $sql="Select * from PublicMessage where `storeid`=$storeid order by message";
        $result = $db->query( $sql );
        $reply.="\r\n[".$GLOBALS['storename']."備註]";
        while($row=$result->fetch(PDO::FETCH_OBJ)){   
            if($showsn==true)
            {
                $reply .= "\r\n[".$row->id."] ". $row->message ;
            }
            else
            {
                $reply .= "\r\n".$row->message ;
            }
        }
	$reply .="\r\n公司($income_company)師傅($income_staff)";

        return $reply;
    };

    function getNotConfirmedTasks($db){
        $sql = "SELECT * FROM Tasks WHERE is_confirmed = 0 and `start` > now() ORDER BY start";
        $result = $db->query($sql);
        $tasks = [];
        
        while ($row = $result->fetch(PDO::FETCH_OBJ)) {
            $tasks[] = $row;
        }
        $strMsg = "以下是所有未確認的預約：\n\n";
        foreach ($tasks as $task) {
            $startDate = date('Y/m/d', strtotime($task->start));
            $startTime = date('H:i', strtotime($task->start));
            $storeId = $task->storeid;
            $storeName = $GLOBALS['sname'][$storeId] ?? '未知店鋪';
            
            $strMsg .= "日期：{$startDate}\n店家：{$storeName}\n時間：{$startTime} ({$task->mins}分鐘)\n客戶：{$task->customer_name}\n師傅：{$task->staff_name}\n備註:{$task->note}\n\n";
        }
        if (empty($tasks)) {
            $strMsg = "目前沒有未確認的預約。";
        }
        
        return $strMsg;
    }

    function getBookA($db,$mainstoreid,$where='',$showsn=false,$isAdmin=false,$showvip=false)
    {
        $income_company=0;
        $income_staff=0;
        $mainstoreid=1;
        
        //$isAdmin=false;
        //$nowdate = date("Y-m-d 00:00:00");
        $sql = "Select * from Tasks where `storeid` in (Select id from Store where mainstore=$mainstoreid) and ".$where; //and `start` >= '$nowdate'";
        //if( $where != '')
        //{
        //  $sql = $sql . " and $where";
        //}
        //return $sql;

        $sql = $sql . " order by `start`";
        //return $sql;



        //$sql="Select * from Staffs where `storeid`=$storeid and `enable`=1";
        $oldday="";
        $addSpace=true;
        $result = $db->query( $sql );
        $reply="[".$GLOBALS['storename']."預約]\r\n";
        $iCustomers=0;
        while($row=$result->fetch(PDO::FETCH_OBJ)){   
        	/*
            $starttime=strtotime($row->start);
            $st1=date("n/j",$starttime);
            $st2=date("H:i",$starttime);
            if( $oldday !== $st1) {
                $oldday=$st1;
                $reply .=$st1."\r\n";
            }
        //if($oldday !== $st1 && $addSpace){
                //  $addSpace=false;
            //}

            $customer_name=$row->customer_name;
            if(!$isAdmin)
            {
                $customer_name=mb_substr($customer_name,0,1,"UTF-8")."**";
            }

            if($showvip)
            {
                $customer_name=$customer_name."($row->memberid)";
            }
            */

            $price=0;
            $income_company_tmp =  0;
            $income_staff_tmp = 0;
            try{
                    $price=$row->price; //價格
                    $tmp_c=$row->company_income;
                    $tmp_s=$row->master_income;
                    $income_company = $income_company + $tmp_c;
                    $income_staff = $income_staff + $tmp_s;
                    $income_company_tmp = $tmp_c;
                    $income_staff_tmp = $tmp_s;
            }
            catch(Exception $e){
                
            }
            /*
            if($showsn)
            {
                $reply .= "[".$row->id."] ".$st2 ." " .$customer_name." " .$row->mins." ".$row->staff_name." ".$row->note."\r\n"; //."($income_staff_tmp/$income_company_tmp)\r\n";
            }
            else
            {
                $reply .= "[".$row->storeid."]". $st2 ." " .$customer_name." ".$row->mins." ".$row->staff_name." ".$row->note."($income_staff_tmp/$income_company_tmp)\r\n";

            } */
            $iCustomers++;
        }

        
    $reply .="\r\n共:".$iCustomers."人\r\n公司($income_company)師傅($income_staff)";//.$sql;

        return $reply;
    };

    function addTickets($db,$storeid,$tickettypeid,$staff_name,$customer_name,$ticket0,$ticket1,$ticket2,$ticket3){
         $sql="Select count(*) as cnt from Tickets where tickettypeid=$tickettypeid and (ticketno=$ticket0 or ticketno=$ticket1 or ticketno=$ticket2 or ticketno=$ticket3) and `storeid`=$storeid";
         //echo $sql;
        $result = $db->query( $sql );
        $row=$result->fetch(PDO::FETCH_OBJ);
        $cnt=$row->cnt;
        //echo "數量:$cnt";
        if($cnt >0)
        {
            return false;
        } 

        $sql="Select * from TicketType where id=$tickettypeid";
         //echo $sql;
        $result = $db->query( $sql );
        $row=$result->fetch(PDO::FETCH_OBJ);
        $ticketname=$row->name;
        $expdays=$row->expdays;


        $sql="Select * from Staffs where `name`='$staff_name' and storeid=$storeid";
         //echo $sql;
        $result = $db->query( $sql );
        $row=$result->fetch(PDO::FETCH_OBJ);
        $staff_id=$row->id;
        
        for($i=0;$i<4;$i++)
        {
            $tname="ticket".$i;
            $sql="Insert into Tickets value(default,$tickettypeid,'$ticketname',".$$tname.",-1,'$customer_name',now(),DATE_ADD(now(),interval $expdays day),'0000-00-00 00:00:00',$staff_id,'$staff_name',0,'',0,$storeid,0)";
            //echo $sql;
            $db->query( $sql );
        }
        return true;

    }

    function useTicket($db,$storeid, $tickettype, $ticketno, $staff_name,$taskid){

	if($tickettype != 2 && trim($ticketno)=="")
	{
		return false;
	}

	//echo "1";

        $sql="Select * from Staffs where `name`='$staff_name' and `storeid`=$storeid";
        $result = $db->query( $sql );
        if( $result->rowCount() === 0 )
        {
            return false;
        }

	//echo "2";	

        $row=$result->fetch(PDO::FETCH_OBJ);
        $staff_id=$row->id;
	$affect=1;

	if($tickettype==2) //公關票
	{
		$iRest=getPRcount($db,$storeid,$staff_id);
		if($iRest <= 0) //票數不足
		{
			return false;
		}
	}

	//echo "3";

	$isAdmin=isAdminByStaffid($db,$storeid,$staff_id);
	if($isAdmin)
	{
		$sql="Update Tasks set usetickettype=$tickettype where `storeid`=$storeid and `id`=$taskid";        
	}
	else
	{
		$sql="Update Tasks set usetickettype=$tickettype where `storeid`=$storeid and `id`=$taskid and `staff_id`=$staff_id";
	}
        $result=$db->query( $sql );
	
	if($tickettype!=2) //2為公關券
	{
        	$sql="Update Tickets set isused=1,usedate=now(),use_staff_id=$staff_id,use_staff_name='$staff_name',`use_task_id`=$taskid where `storeid`=$storeid and ticketno=$ticketno and tickettypeid=$tickettype and isused=0";
        	//echo $sql;
        	$result=$db->query( $sql );
        	$affect = $result->rowCount();
        	//echo "test:$affect";
	}

        if(  $affect=== 0)
        {
            return false;
        }
        return true;
    }

    function buildAskMenu($storeid,$staff_name,$userid,$days) {
        //return "test";
        $myfile = fopen("ask_menu.txt", "r") or die("Unable to open file!");
        $data= fread($myfile,filesize("ask_menu.txt"));
        fclose($myfile);
        //return $data;

        $title1="預約";
        $ask1_1="新增預約";
        $url1_1="https://www.twn.pw/line/spa/addBook.php?storeid=$storeid&userid=$userid";
        $ask1_2="修改預約";
        $url1_2="https://www.twn.pw/line/spa/modBook.php?storeid=$storeid&days=$days&userid=$userid";
        $ask1_3="刪除預約";
        $url1_3="https://www.twn.pw/line/spa/delBook.php?storeid=$storeid&days=0&userid=$userid";

        $title2="備註";
        $ask2_1="新增備註";
        $url2_1="https://www.twn.pw/line/spa/addNote.php?storeid=$storeid";
        $ask2_2="修改備註";
        $url2_2="https://www.twn.pw/line/spa/modNote.php?storeid=$storeid&days=0";
        $ask2_3="刪除備註";
        $url2_3="https://www.twn.pw/line/spa/delNote.php?storeid=$storeid&days=0";

        $title3="票券";
        $ask3_1="售出登記";
        $url3_1="https://www.twn.pw/line/spa/addTicket.php?storeid=$storeid&userid=$userid&staff_name=".urlencode($staff_name);
        $ask3_2="使用登記";
        $url3_2="https://www.twn.pw/line/spa/useTicket.php?storeid=$storeid&userid=$userid&staff_name=".urlencode($staff_name);
        $ask3_3="使用狀況";
        $url3_3="https://www.twn.pw/line/spa/statusTicket.php?storeid=$storeid&days=1&userid=$userid&staff_name=".urlencode($staff_name);

        $title4="排休";
        $ask4_1="本日房況";
	$url4_1="https://www.twn.pw/line/spa/timeline.php?storeid=$storeid&userid=$userid&staff_name=".urlencode($staff_name);
        //$url4_1="https://www.twn.pw/line/spa/restToday.php?storeid=$storeid&staff_name=".urlencode($staff_name);
        $ask4_2="一週排休";
        $url4_2="https://www.twn.pw/line/spa/sch2025.php?storeid=$storeid&userid=$userid&staff_name=".urlencode($staff_name);
        $ask4_3="排休狀況";
        $url4_3="https://www.twn.pw/line/spa/restStatus.php?storeid=$storeid&days=1";

	$title5="其它";
        $ask5_1="查詢客戶";
	$url5_1="https://www.twn.pw/line/spa/queryvip.php?storeid=$storeid&userid=$userid&staff_name=".urlencode($staff_name);
        $ask5_2="結帳試算";
        $url5_2="https://www.twn.pw/line/spa/mySalary.php?storeid=$storeid&userid=$userid&staff_name=".urlencode($staff_name);
        $ask5_3="(未指定)";
        $url5_3="https://www.twn.pw/line/spa/temp.php?target=ex_book&storeid=$storeid&userid=$userid&staff_name=".urlencode($staff_name);


        $data=str_replace("%title1%", $title1, $data);
        $data=str_replace("%ask1_1%", $ask1_1, $data);
        $data=str_replace("%url1_1%", $url1_1, $data);
        $data=str_replace("%ask1_2%", $ask1_2, $data);
        $data=str_replace("%url1_2%", $url1_2, $data);
        $data=str_replace("%ask1_3%", $ask1_3, $data);
        $data=str_replace("%url1_3%", $url1_3, $data);

        $data=str_replace("%title2%", $title2, $data);
        $data=str_replace("%ask2_1%", $ask2_1, $data);
        $data=str_replace("%url2_1%", $url2_1, $data);
        $data=str_replace("%ask2_2%", $ask2_2, $data);
        $data=str_replace("%url2_2%", $url2_2, $data);
        $data=str_replace("%ask2_3%", $ask2_3, $data);
        $data=str_replace("%url2_3%", $url2_3, $data);

        $data=str_replace("%title3%", $title3, $data);
        $data=str_replace("%ask3_1%", $ask3_1, $data);
        $data=str_replace("%url3_1%", $url3_1, $data);
        $data=str_replace("%ask3_2%", $ask3_2, $data);
        $data=str_replace("%url3_2%", $url3_2, $data);
        $data=str_replace("%ask3_3%", $ask3_3, $data);
        $data=str_replace("%url3_3%", $url3_3, $data);

        $data=str_replace("%title4%", $title4, $data);
        $data=str_replace("%ask4_1%", $ask4_1, $data);
        $data=str_replace("%url4_1%", $url4_1, $data);
        $data=str_replace("%ask4_2%", $ask4_2, $data);
        $data=str_replace("%url4_2%", $url4_2, $data);
        $data=str_replace("%ask4_3%", $ask4_3, $data);
        $data=str_replace("%url4_3%", $url4_3, $data);

        $data=str_replace("%title5%", $title5, $data);
        $data=str_replace("%ask5_1%", $ask5_1, $data);
        $data=str_replace("%url5_1%", $url5_1, $data);
        $data=str_replace("%ask5_2%", $ask5_2, $data);
        $data=str_replace("%url5_2%", $url5_2, $data);
        $data=str_replace("%ask5_3%", $ask5_3, $data);
        $data=str_replace("%url5_3%", $url5_3, $data);


        //$myobj = json_decode($data);
        return $data;
        //return "test1232";
    };

    function buildAskBox($title,$ask1,$url1,$ask2,$url2,$ask3,$url3) {
        $myfile = fopen("ask_3.txt", "r") or die("Unable to open file!");
        $data= fread($myfile,filesize("ask_3.txt"));
        fclose($myfile);
        $data=str_replace("%title%", $title, $data);
        $data=str_replace("%ask1%", $ask1, $data);
        $data=str_replace("%url1%", $url1, $data);
        $data=str_replace("%ask2%", $ask2, $data);
        $data=str_replace("%url2%", $url2, $data);
        $data=str_replace("%ask3%", $ask3, $data);
        $data=str_replace("%url3%", $url3, $data);
        //$myobj = json_decode($data);
        return $data;
    };

    /**
     * Send a message to a LINE user
     * 
     * @param string $userId LINE user ID to send message to
     * @param string $message Message text to send
     * @param string $confirmUrl Optional URL for confirmation button
     * @param array $lineConfig LINE API configuration array with channel_access_token and channel_secret
     * @return bool|string Success (true) or error message (string)
     */
    function sendLineMessage($userId, $message, $confirmUrl = null, $lineConfig = null) {
        try {
            // Use global constants if no config provided
            //$ca[1]= 'V8ARZ8gLtvdD8/hbu437US2cTifjmhhg28LaB1rjTpjMAzNOh+fMt0s1Ttn704nrvmoLk/GzjaAJWRcfhgjRm4Oy/WyFkLi/meVu1Ia+A42z/E5441Kg0198ajRmO6HvmEGRQj23+ol9cs0UOwyoewdB04t89/1O/w1cDnyilFU=';
            //$cs[1] = 'fa3d301981cc06f2e8a75fe8680f8518';
            $ca[1] = 'hWtckGsIu0S7MqaHRlwsecLxN1Gg1RsAcClX85MRNdo/3mrVFsc1vXN6iZ6UXZfC3x4fd8/Sil0FjQ2qEBRtSCGj9cNuAF/00qvZqdL6cVZVK2zXWnqg/+nf9duQgxrwfTdqTD6z8mIXhJVJj8TMegdB04t89/1O/w1cDnyilFU=';
            $cs[1] = '1799e40b51b185889b986a728f6e4d8c';

            if (!$lineConfig) {
                $lineConfig = [
                    'channel_access_token' => $ca[1],
                    'channel_secret' => $cs[1]
                ];
            }
            
            // Validate required parameters
            if (empty($userId)) {
                return "Error: User ID is required";
            }
            
            if (empty($message)) {
                return "Error: Message is required";
            }
            
            // Prepare the message content
            $data = [
                'to' => $userId,
                'messages' => [
                    [
                        'type' => 'text',
                        'text' => $message
                    ]
                ]
            ];
            
            // Add confirmation button if URL is provided
            if ($confirmUrl) {
                $data['messages'][] = [
                    'type' => 'template',
                    'altText' => '請確認預約',
                    'template' => [
                        'type' => 'buttons',
                        'text' => '請點擊下方按鈕確認此預約',
                        'actions' => [
                            [
                                'type' => 'uri',
                                'label' => '確認預約',
                                'uri' => $confirmUrl
                            ]
                        ]
                    ]
                ];
            }
            //echo "Start to send";
            // Initialize cURL with timeout
            $ch = curl_init('https://api.line.me/v2/bot/message/push');
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_TIMEOUT, 30); // Set a reasonable timeout
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $lineConfig['channel_access_token']
            ]);
            
            // Execute the request
            $result = curl_exec($ch);
            //echo "Send result: $result";

            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $curlError = curl_error($ch);
            $curlErrno = curl_errno($ch);
            curl_close($ch);
            
            // Check for cURL errors
            if ($curlError) {
                return "cURL Error ({$curlErrno}): {$curlError}";
            }
            
            // Check for LINE API errors
            if ($httpCode !== 200) {
                $errorDetail = "HTTP Status: {$httpCode}";
                
                // Try to extract error message from response
                if (!empty($result)) {
                    $responseData = json_decode($result, true);
                    if (isset($responseData['message'])) {
                        $errorDetail .= ", Message: {$responseData['message']}";
                    } else {
                        $errorDetail .= ", Response: {$result}";
                    }
                }
                
                return "LINE API Error: {$errorDetail}";
            }
            
            return true; // Success
            
        } catch (Exception $e) {
            return "Exception: " . $e->getMessage();
        }
    }

    function sendLineMessageToGroup($db, $all_message, $lineConfig) {
        try {
            // Get task information
            $stmt = $db->prepare("SELECT * From GroupRoom Limit 0,1");
            $stmt->execute();
            $task = $stmt->fetch(PDO::FETCH_OBJ);
            if (!$task) {
                return false;
            }
            $groupId = $task->groupId;
            //開始送訊息出去Line Message Group
            return sendLineMessage($groupId, $all_message, null, $lineConfig);
        } catch (Exception $e) {
            echo "Error sending message to group: " . $e->getMessage();
            exit;
            return false;
        }
    }

    /**
     * Send notification about new task to staff
     * 
     * @param object $db Database connection
     * @param int $taskId Task ID
     * @param array $lineConfig LINE API configuration array
     * @return bool Success or failure
     */
    function sendNewTaskMessage($db, $taskId, $lineConfig = null) {
        try {
            // Get task information
            $stmt = $db->prepare("
                SELECT t.id, t.customer_name, t.start, t.end, t.mins, t.staff_id, 
                       t.staff_name, t.note, t.course_name, t.storeid 
                FROM Tasks t 
                WHERE t.id = ?
            ");
            $stmt->execute([$taskId]);
            $task = $stmt->fetch(PDO::FETCH_OBJ);
            
            if (!$task) {
                return false;
            }
            
            // Get staff LINE user ID
            $stmt = $db->prepare("SELECT line_userid FROM Staffs WHERE id = ? ");
            $stmt->execute([$task->staff_id]);
            $staff = $stmt->fetch(PDO::FETCH_OBJ);
            
            if (!$staff || empty($staff->line_userid)) {
                return false;
            }
            
            $lineUserId = $staff->line_userid;
            $startDate = date('Y/m/d', strtotime($task->start));
            $startTime = date('H:i', strtotime($task->start));
            
            // Get store name
            $storeId = $task->storeid;
            $storeName = "未知店鋪";
            if (isset($GLOBALS['sname'][$storeId])) {
                $storeName = $GLOBALS['sname'][$storeId];
            } else {
                switch($storeId) {
                    case 1:
                        $storeName = '西門店';
                        break;
                    case 2:
                        $storeName = '延吉店';
                        break;
                }
            }
            
            // Create notification message
            $currentDateTime = date('Y/m/d H:i:s');
            $message = "新預約通知：\n日期：{$startDate}\n店家：{$storeName}\n時間：{$startTime} ({$task->mins}分鐘)\n客戶：{$task->customer_name}\n師傅：{$task->staff_name}\n備註:{$task->note}\n\n請確認此預約！";
            $confirmUrl = "https://www.twn.pw/line/spa/confirm_task.php?id={$task->id}";
            
            return sendLineMessage($lineUserId, $message, $confirmUrl, $lineConfig);
            
        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Send notification about edited task to staff
     * 
     * @param object $db Database connection
     * @param int $taskId Task ID
     * @param array $lineConfig LINE API configuration array
     * @return bool Success or failure
     */
    function sendEditTaskMessage($db, $taskId, $lineConfig = null) {
        try {
            echo "Sending edit task message for task ID: $taskId\n";
            // Get task information
            $stmt = $db->prepare("
                SELECT t.id, t.customer_name, t.start, t.end, t.mins, t.staff_id, 
                       t.staff_name, t.note, t.course_name, t.storeid 
                FROM Tasks t 
                WHERE t.id = ?
            ");
            $stmt->execute([$taskId]);
            $task = $stmt->fetch(PDO::FETCH_OBJ);
            
            if (!$task) {
                return false;
            }
            
            // Get staff LINE user ID
            $stmt = $db->prepare("SELECT line_userid FROM Staffs WHERE id = ? ");
            $stmt->execute([$task->staff_id]);
            $staff = $stmt->fetch(PDO::FETCH_OBJ);
            
            if (!$staff || empty($staff->line_userid)) {
                return false;
            }
            
            $lineUserId = $staff->line_userid;
            $startDate = date('Y/m/d', strtotime($task->start));
            $startTime = date('H:i', strtotime($task->start));
            
            // Get store name
            $storeId = $task->storeid;
            $storeName = "未知店鋪";
            if (isset($GLOBALS['sname'][$storeId])) {
                $storeName = $GLOBALS['sname'][$storeId];
            } else {
                switch($storeId) {
                    case 1:
                        $storeName = '西門店';
                        break;
                    case 2:
                        $storeName = '延吉店';
                        break;
                }
            }
            
            // Create notification message
            $currentDateTime = date('Y/m/d H:i:s');
            $message = "預約變更通知：\n日期：{$startDate}\n店家：{$storeName}\n時間：{$startTime} ({$task->mins}分鐘)\n客戶：{$task->customer_name}\n師傅：{$task->staff_name}\n備註:{$task->note}\n\n此預約已被修改，請確認變更內容！";
            $confirmUrl = "https://www.twn.pw/line/spa/confirm_task.php?id={$task->id}";
            echo "Message to send: $message\n$lineUserId\n$confirmUrl\n$lineConfig\n";
            return sendLineMessage($lineUserId, $message, $confirmUrl, $lineConfig);
            echo "Message sent successfully to LINE user ID: $lineUserId\n";
        } catch (Exception $e) {
            echo $e->getMessage();
            exit(1);
            return false;
        }
    }

    /**
     * Send notification about deleted task to staff
     * 
     * @param string $lineUserId LINE user ID of staff
     * @param object $task Task data before deletion
     * @param array $lineConfig LINE API configuration array
     * @return bool Success or failure
     */
    function sendDelTaskMessage($db , $taskId, $lineConfig = null) {
        try {

            $stmt = $db->prepare("
                SELECT t.id, t.customer_name, t.start, t.end, t.mins, t.staff_id, 
                       t.staff_name, t.note, t.course_name, t.storeid 
                FROM Tasks t 
                WHERE t.id = ?
            ");
            $stmt->execute([$taskId]);
            $task = $stmt->fetch(PDO::FETCH_OBJ);
            
            if (!$task) {
                return false;
            }

            // Get staff LINE user ID
            $stmt = $db->prepare("SELECT line_userid FROM Staffs WHERE id = ? ");
            $stmt->execute([$task->staff_id]);
            $staff = $stmt->fetch(PDO::FETCH_OBJ);
            
            if (!$staff || empty($staff->line_userid)) {
                return false;
            }
            
            $lineUserId = $staff->line_userid;


            $startDate = date('Y/m/d', strtotime($task->start));
            $startTime = date('H:i', strtotime($task->start));
            
            // Get store name
            $storeId = $task->storeid;
            $storeName = "未知店鋪";
            if (isset($GLOBALS['sname'][$storeId])) {
                $storeName = $GLOBALS['sname'][$storeId];
            } else {
                switch($storeId) {
                    case 1:
                        $storeName = '西門店';
                        break;
                    case 2:
                        $storeName = '延吉店';
                        break;
                }
            }
            
            // Create notification message
            $currentDateTime = date('Y/m/d H:i:s');
            $message = "預約取消通知：\n日期：{$startDate}\n店家：{$storeName}\n時間：{$startTime} ({$task->mins}分鐘)\n客戶：{$task->customer_name}\n師傅：{$task->staff_name}\n\n此預約已被取消！";
            
            return sendLineMessage($lineUserId, $message, null, $lineConfig);
            
        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Get the ID of the last inserted task
     * 
     * @param object $db Database connection
     * @param int $storeid Store ID to filter by (optional)
     * @return int|false Returns the last task ID or false if not found
     */
    function getLastTaskId($db, $storeid = null) {
        try {
            $sql = "SELECT id FROM Tasks ORDER BY id DESC LIMIT 1";
            
            // Add storeid filter if provided
            if ($storeid !== null) {
                $sql = "SELECT id FROM Tasks WHERE storeid = ? ORDER BY id DESC LIMIT 1";
                $stmt = $db->prepare($sql);
                $stmt->execute([$storeid]);
            } else {
                $stmt = $db->query($sql);
            }
            
            $result = $stmt->fetch(PDO::FETCH_OBJ);
            
            return ($result) ? $result->id : false;
        } catch (Exception $e) {
            return false;
        }
    }
?>
