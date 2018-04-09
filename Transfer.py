import deviantart, re, mysql.connector, time
from deviantart.api import DeviantartError

class Transfer:
    def __init__(self, da, cnx, cursor):
        self.da = da
        self.cnx = cnx
        self.cursor = cursor
        self.temp_comments = None
    def create_reply(self, commands_result, meanings, comment_id):
        is_hr = False
        hr = ""
        bot_add = ""
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                is_hr = True
                if(hr == ""):
                    hr = "<hr><small>Your current balance: <b>" + str(meanings[i][1]) + " NP</b><br>" + str(meanings[i][0]) + "'s current balance: " + str(meanings[i][2]) + " NP</small>"
                else:
                    hr = re.sub('</small>', "<br />"+ str(meanings[i][0]) + "'s current balance: " + str(meanings[i][2]) + " NP</small>", hr)
                hr_hr = ""
                if(bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ":bulletgreen: The transfer is successful!<br>Thanks for using tori-services~ ♪<br><i><small>(This is an automated message, <u>don't reply</u>!)</small></i>"
            if (commands_result[i] == '1'):
                is_hr = True
                href = '"http://last2424.ru/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                hr = "<hr><small>Your current balance: " + str(meanings[i][1]) + " NP<br><a href=" + str(href) + ">Check your profile</a></small>"
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ":bulletorange: <i>Ooops!</i> Sorry, but we can't do this.<br>You haven't enough of <b>Nyam Points!</b>"
            if (commands_result[i] == '2'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ":bulletorange: <i>Aaaa!!~ we have some problems with your request!</i><br>User <i>"+meanings[i][0]+"</i> <b>wasn't found</b> in our databank."
        if (is_hr):
            bot_add = bot_add + hr
        self.da.post_comment(target='DBD5B182-144E-A81A-13D5-9696D522391B', comment_type='deviation', body=bot_add, commentid=comment_id)
        time.sleep(5)


    def message(self):
       comments = self.da.get_comments(endpoint='deviation', deviationid='DBD5B182-144E-A81A-13D5-9696D522391B', limit=25)
       comments = comments['thread']
       if(self.temp_comments != comments):
            for i in range(len(comments)):
                cursor = self.cursor
                cnx = self.cnx
                commands_result = []
                meanings = []
                ignoring = False
                if (comments[i].replies == 0 and comments[i].hidden == None):
                    list = re.findall('NP\sTransfer\sto\s(?<=NP\sTransfer\sto\s).*?(?=<br />|$)', re.sub('&nbsp;', ' ', comments[i].body), re.IGNORECASE)
                    sql = ("SELECT balance FROM users WHERE username='"+str(comments[i].user.username)+"'")
                    cursor.execute(sql)
                    if(cursor.rowcount > 0):
                        for j in range(len(list)):
                            list[j] = re.sub('</span>|<span>|<b>|</b>|<hr>|<hr />|</hr>|</a>|<sub>|</sub>|<i>|</i>', '', list[j])
                            list[j] = re.sub('<a\s(?<=<a\s).*?(?=>)>', '', list[j])
                            list[j] = re.sub('&nbsp;', ' ', list[j])
                            c = re.search('\s((100000)|(0*\d{1,6}))', list[j])
                            if(c == None):
                                ignoring = True
                                break
                            else:
                                if(c.group(0) == ""):
                                    ignoring = True
                                    break
                                else:
                                    c = c.group(0)
                                    c = int(c)
                            g = re.search('(?<=NP Transfer to\s).*?(?='+str(c)+')', list[j], re.IGNORECASE)
                            g = re.sub('\s', '', g.group(0))
                            sql = ("SELECT balance FROM users WHERE username='" + str(g) + "'")
                            cursor.execute(sql)
                            if (cursor.rowcount > 0):
                                user_id1 = 0
                                balance = 0
                                user_id2 = 0
                                balance2 = 0
                                sql = ("SELECT user_id, balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                cursor.execute(sql)
                                for (user_id1, balance1) in cursor:
                                    balance = balance1
                                    user_id1 = user_id1
                                if(balance - c >= 0):
                                    sql = ("UPDATE users SET balance=balance-'"+str(c)+"' WHERE username='"+str(comments[i].user.username)+"'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE users SET balance=balance+'" + str(c) + "' WHERE username='" + str(g) + "'")
                                    cursor.execute(sql)
                                    sql = ("INSERT INTO `transfers` (`from`, `to`, `count`) VALUES ('"+str(comments[i].user.username)+"', '"+str(g)+"', '"+str(c)+"')")
                                    cursor.execute(sql)
                                    sql = ("SELECT user_id, balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                    cursor.execute(sql)
                                    for (user_id1, balance1) in cursor:
                                        balance = balance1
                                        user_id1 = user_id1
                                    sql = ("SELECT user_id, balance FROM users WHERE username='" + str(g) + "'")
                                    cursor.execute(sql)
                                    for (user_id2, balance2) in cursor:
                                        user_id2 = user_id2
                                        balance2 = balance2
                                    t_id = 0
                                    sql = ("SELECT `id` FROM `transfers` WHERE `from`='" + str(comments[i].user.username) + "' AND `to`='"+str(g)+"' ORDER BY `id` DESC")
                                    cursor.execute(sql)
                                    for(id) in cursor:
                                        t_id = id
                                    href = '<a href="https://torimori.info/index.php?page=balance_info&id='+str(user_id2)+'">'+str(g)+'</a>'
                                    sql = ("INSERT INTO transaction (username, count, note, transfer_id, date) VALUES ('" + str(comments[i].user.username) + "', '-" + str(c) + "', 'To "+href+"', '" + str(t_id) + "', now())")
                                    cursor.execute(sql)
                                    href = '<a href="https://torimori.info/index.php?page=balance_info&id='+str(user_id1)+'">'+str(comments[i].user.username)+'</a>'
                                    sql = ("INSERT INTO transaction (username, count, note, transfer_id, date) VALUES ('" + str(g) + "', '" + str(c) + "', 'From "+href+"', '" + str(t_id) + "', now())")
                                    cursor.execute(sql)
                                    sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + comments[i].user.username + "'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + str(g) + "'")
                                    cursor.execute(sql)
                                    commands_result.append('0')
                                    meanings.append([g, balance, balance2])
                                else:
                                    balance = 0
                                    user_id = 0
                                    sql = ("SELECT user_id, balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                    cursor.execute(sql)
                                    for (user_id, balance) in cursor:
                                        balance = balance
                                        user_id = user_id
                                    commands_result.append('1')
                                    meanings.append([user_id, balance])
                            else:
                                try:
                                    u = self.da.get_user(username=str(g), ext_galleries=False, ext_collections=False)
                                except DeviantartError:
                                    u = ""
                                if(u != ""):
                                    sql = ("SELECT username FROM users ORDER BY user_id ASC")
                                    cursor.execute(sql)
                                    for username in cursor:
                                        try:
                                            user = self.da.get_user(username=username[0])
                                        except DeviantartError:
                                            user = ""
                                        if (user != "" and user != None):
                                            if (str(user) == str(u)):
                                                sql = ("UPDATE users SET username='" + u.username + "' WHERE username='" + username[0] + "'")
                                                cursor.execute(sql)
                                                sql = ("UPDATE inventory SET owner='" + u.username + "' WHERE owner='" + username[0] + "'")
                                                cursor.execute(sql)
                                                sql = ("UPDATE transaction SET username='" + u.username + "' WHERE username='" + username[0] + "'")
                                                cursor.execute(sql)
                                                sql = ("UPDATE inventorylog SET username='" + u.username + "' WHERE username='" + username[0] + "'")
                                                cursor.execute(sql)
                                                sql = ("SELECT `id` FROM `transfers` WHERE `from`='"+username[0]+"'")
                                                cursor.execute(sql)
                                                for(id) in cursor:
                                                    sql = ("UPDATE `transfers` SET `from`='" + u.username + "' WHERE `id`='" + id[0] + "'")
                                                    cursor.execute(sql)
                                                sql = ("SELECT `id` FROM `transfers` WHERE `to`='" + username[0] + "'")
                                                cursor.execute(sql)
                                                for (id) in cursor:
                                                    sql = ("UPDATE `transfers` SET `to`='" + u.username + "' WHERE `id`='" +id[0] + "'")
                                                    cursor.execute(sql)
                                                break
                                    sql = ("SELECT username FROM users WHERE username='" + g + "'")
                                    cursor.execute(sql)
                                    if (cursor.rowcount > 0):
                                        user_id1 = 0
                                        balance = 0
                                        user_id2 = 0
                                        balance2 = 0
                                        sql = ("SELECT user_id, balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                        cursor.execute(sql)
                                        for (user_id1, balance1) in cursor:
                                            balance = balance1
                                            user_id1 = user_id1
                                        if (balance - c >= 0):
                                            sql = ("UPDATE users SET balance=balance-'" + str(c) + "' WHERE username='" + str(comments[i].user.username) + "'")
                                            cursor.execute(sql)
                                            sql = ("UPDATE users SET balance=balance+'" + str(c) + "' WHERE username='" + str(g) + "'")
                                            cursor.execute(sql)
                                            sql = ("INSERT INTO `transfers` (`from`, `to`, `count`) VALUES ('" + str(comments[i].user.username) + "', '" + str(g) + "', '" + str(c) + "')")
                                            cursor.execute(sql)
                                            sql = ("SELECT user_id, balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                            cursor.execute(sql)
                                            for (user_id1, balance1) in cursor:
                                                balance = balance1
                                                user_id1 = user_id1
                                            sql = ("SELECT user_id, balance FROM users WHERE username='" + str(g) + "'")
                                            cursor.execute(sql)
                                            for (user_id2, balance2) in cursor:
                                                user_id2 = user_id2
                                                balance2 = balance2
                                            t_id = 0
                                            sql = ("SELECT `id` FROM `transfers` WHERE `from`='" + str(comments[i].user.username) + "' AND `to`='" + str(g) + "' ORDER BY `id` DESC")
                                            cursor.execute(sql)
                                            for (id) in cursor:
                                                t_id = id
                                            href = '<a href="http://last2424.ru/index.php?page=balance_info&id=' + str(user_id1) + '">' + str(comments[i].user.username) + '</a>'
                                            sql = ("INSERT INTO transaction (username, count, note, transfer_id, date) VALUES ('" + str(comments[i].user.username) + "', '-" + str(c) + "', 'To " + href + "', '" + str(t_id) + "', now())")
                                            cursor.execute(sql)
                                            href = '<a href="https://torimori.info/index.php?page=balance_info&id=' + str(user_id2) + '">' + str(g) + '</a>'
                                            sql = ("INSERT INTO transaction (username, count, note, transfer_id, date) VALUES ('" + str(g) + "', '" + str(c) + "', 'From " + href + "', '" + str(t_id) + "', now())")
                                            cursor.execute(sql)
                                            sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + comments[i].user.username + "'")
                                            cursor.execute(sql)
                                            sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + str(g) + "'")
                                            cursor.execute(sql)
                                            commands_result.append('0')
                                            meanings.append([g, balance, balance2])
                                        else:
                                            balance = 0
                                            user_id = 0
                                            sql = ("SELECT user_id, balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                            cursor.execute(sql)
                                            for (user_id, balance) in cursor:
                                                balance = balance
                                                user_id = user_id
                                            commands_result.append('1')
                                            meanings.append([user_id, balance])
                                else:
                                    balance = 0
                                    user_id = 0
                                    sql = ("SELECT user_id, balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                    cursor.execute(sql)
                                    for (user_id, balance) in cursor:
                                        balance = balance
                                        user_id = user_id
                                    commands_result.append('2')
                                    meanings.append([g, user_id, balance])
                        if (len(list) > 0 and ignoring == False):
                            self.create_reply(commands_result=commands_result, meanings=meanings, comment_id=comments[i].commentid)
                    else:
                        sql = ("SELECT username FROM users ORDER BY user_id ASC")
                        cursor.execute(sql)
                        for username in cursor:
                            try:
                                user = self.da.get_user(username=username[0])
                            except DeviantartError:
                                user = ""
                            if(user != "" and user != None):
                                if (str(user) == str(comments[i].user.username)):
                                    sql = ("UPDATE users SET username='" + str(comments[i].user.username) + "' WHERE username='" + str(username[0]) + "'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE inventory SET owner='" + str(comments[i].user.username) + "' WHERE owner='" + str(username[0]) + "'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE transaction SET username='" + str(comments[i].user.username) + "' WHERE username='" +str(username[0]) + "'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE inventorylog SET username='" + str(comments[i].user.username) + "' WHERE username='" +str(username[0]) + "'")
                                    cursor.execute(sql)
                                    sql = ("SELECT id FROM transfers WHERE from='" + str(username[0]) + "'")
                                    cursor.execute(sql)
                                    for id in cursor:
                                        sql = ("UPDATE transfers SET from='" + str(comments[i].user.username) + "' WHERE id='" + str(id[0]) + "'")
                                        cursor.execute(sql)
                                    sql = ("SELECT id FROM transfers WHERE to='" + str(username[0]) + "'")
                                    cursor.execute(sql)
                                    for id in cursor:
                                        sql = ("UPDATE transfers SET to='" + str(comments[i].user.username) + "' WHERE id='" + str(id[0]) + "'")
                                        cursor.execute(sql)
                                    break
                        sql = ("SELECT username FROM users WHERE username='" + str(comments[i].user.username) + "'")
                        cursor.execute(sql)
                        if (cursor.rowcount == 0):
                            sql = ("INSERT INTO users (username, balance) VALUES ('" + str(comments[i].user.username) + "', '0')")
                            cursor.execute(sql)

            self.temp_comments = comments
            time.sleep(20)