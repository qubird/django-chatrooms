/* jQuery client side script to make the chatrooms app work out of the box
*/

$(function(){
    var Context = getContext();
    var latest_message_id;

    $.ajax({
            url: "/chat/get_latest_msg_id/",
            async: false,
            dataType: 'json',
            data: {'room_id': Context.room_id},
            success: function(data) {
                    latest_message_id = data.id;
            }
        });

    var getEscapedText = function(text_to_escape){
        return $('<dummy>').text(text_to_escape).html();
    };

    var compareDates = function(dateObj1, dateObj2){
        /*returns True if dateObj1 >= dateObj2 */
        if ((dateObj1.hour >= dateObj2.hour && 
            dateObj1.minute >= dateObj2.minute && 
            dateObj1.second == dateObj2.second && 
            dateObj1.microsecond > dateObj2.microsecond) 
            || 
            (dateObj1.hour >= dateObj2.hour && 
            dateObj1.minute >= dateObj2.minute && 
            dateObj1.second > dateObj2.second)){
                return 1;
            }
    };
    
    
    var parseDateTime = function(timeString){
        //capture time string fields thru regexp 2010-10-01T12:07:31:768227
        var parse_time = /([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2}):([0-9]*)/;
        var resultsArr = parse_time.exec(timeString);
        var resultsObj;
        if(resultsArr.length === 8){
            resultsObj = {
                fullString: resultsArr[0],
                year: resultsArr[1],
                month:resultsArr[2],
                day: resultsArr[3],
                hour: resultsArr[4],
                minute: resultsArr[5],
                second: resultsArr[6],
                microsecond: resultsArr[7]
            };
            return resultsObj;
        }else return undefined;
    };
    
    var chatSendAction = function (event) {
        if($('#chatSendText').val() !== ""){
            var data_to_send = {
                "username": Context.username,
                "room_id": Context.room_id,
                //escape quotes and special chars to avoid html injection
                "message": escape(getEscapedText($('#chatSendText').val()))
            };
            $.post('/chat/send_message/', data_to_send, function(data){
                $('#chatSendText').attr('value', "");
            });
        }
    };

    var getChatText = function(data){
        var to_append = [];
        for (var i = 0; i < data.length; i++){
            if (latest_message_id < data[i].message_id){
                latest_message_id = data[i].message_id;

                var msgTime = parseDateTime(data[i].date);

                if (Context.username === data[i].username){
                    to_append.push(
                '<div class="chatMessage myMessage"><div class="messageDate">');
                }
                else {
                    to_append.push(
                '<div class="chatMessage"><div class="messageDate">');
                }

                to_append.push(msgTime.hour + ':' + msgTime.minute +
                               ':' + msgTime.second);
                to_append.push('</div> <div class="messageUsername">');
                if (Context.username === data[i].username){
                    to_append.push('You wrote:');
                }
                else {
                    to_append.push(data[i].username + ' wrote:');
                }

                to_append.push('</div><div class="messageContent">');
                to_append.push(unescape(data[i].content));
                to_append.push('</div>' + '</div>');
            }
        }
        return to_append.join("");
    };

    var chatGetMessages = function(){
        $.ajax({
            url: "/chat/get_messages/",
            cache: false,
            dataType: "json",
            data: {'room_id': Context.room_id,
                   'latest_message_id': latest_message_id},
            type: "GET",
            success: function(data) {
                var chatText = getChatText(data)
                $('#chatText').append(chatText);
                $("#chatText").attr({
                    scrollTop: $("#chatText").attr("scrollHeight")});
                window.setTimeout(chatGetMessages, 0);
            },
            error: function(jqXHR, textStatus, errorThrown){
                if (textStatus === 'timeout'){
                    window.setTimeout(chatGetMessages, 0);
                }
            }});
    };
    var notifyConnection = function(){
        $.ajax({
            url: "/chat/notify_users_list/",
            cache: false,
            data: {'room_id': Context.room_id},
            type: 'POST',
            success: function(data){
                // window.setTimeout(usersListGet, 0);
            }
            
        });
    };
    
    var usersListGet = function(){
        $.ajax({
            url: "/chat/get_users_list/",
            cache: false,
            dataType: "json",
            data: {'room_id': Context.room_id},
            type: "GET",
            success: function(data){
                $('#connectedUsersList').empty();
                var now = parseDateTime(data.now);
                var date = new Date(now.year, now.month, now.day,
                                    now.hour, now.minute, now.second);
                $('#connectedUsersList').empty();
                date = date.valueOf();
                var users = data.users;
                for (var i = 0; i < users.length; i++){
                    var userdate = parseDateTime(users[i].date);
                    var userJsDate = new Date(
                            userdate.year,
                            userdate.month,
                            userdate.day,
                            userdate.hour,
                            userdate.minute,
                            userdate.second);
                    userJsDate = userJsDate.valueOf();
                    if (date - userJsDate < (data.refresh * 2) * 1000){
                        if (Context.username == users[i].username){
                            $('#connectedUsersList').append(
                                '<li>You</li>');    
                        } else{
                            $('#connectedUsersList').append(
                                '<li>'+ users[i].username + '</li>');}
                    }
                }
                window.setTimeout(usersListGet, 0);
            }
        });
    };

    $('#chatSendButton').bind("click", chatSendAction);

    $('#chatSendText').keydown(function(e){
        if (e.keyCode == '13' && !e.shiftKey){
            $('#chatSendButton').addClass("pressed");
        }
        if (e.keyCode == '13' && e.shiftKey){
            $('#chatSendText').val($('#chatSendText').val() + '\r\n');
        }
    });
    $('#chatSendText').keyup(function(e){
        if (e.keyCode == '13' && !e.shiftKey){
            $('#chatSendButton').removeClass("pressed");
            $('#chatSendButton').click();
        }
    });
    
    
    window.setTimeout(chatGetMessages, 0);
    window.setTimeout(usersListGet, 0);
    window.setTimeout(notifyConnection, 0);
});
