import deviantart, re, mysql.connector, time

class Shop:
    def __init__(self, da, cnx, cursor):
        self.da = da
        self.cnx = cnx
        self.cursor = cursor

    def create_reply_buy(self, type, commands_result, meanings, comment_id):
        is_hr = False
        hr = ""
        bot_add = ""
        if(type == 0):
            for i in range(len(commands_result)):
                if(commands_result[i] == '0'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id='+str(meanings[i][0])+'"'
                    hr = "<hr><small>Your current balance: "+str(meanings[i][1])+" NP<br><a href="+str(href)+">Check your profile</a></small>"
                    hr_hr = ""
                    if(bot_add != ""):
                        hr_hr = "<hr />"
                    href1 = '"' + str(meanings[i][4]) + '"'
                    bot_add = bot_add + hr_hr + ":bulletgreen: Your purchase is successful! Thanks for buying!<br><a href="+href1+">"+str(meanings[i][2])+"</a> x"+str(meanings[i][3])+" was added to your inventory."
                if(commands_result[i] == '1'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                    hr = "<hr><small>Your current balance: " + str(meanings[i][1]) + " NP<br><a href=" + str(href) + ">Check your profile</a></small>"
                    hr_hr = ""
                    if(bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr + ":bulletorange: <i>Ooops!</i> Sorry, but I can't sell you this.<br>You haven't enough of <b>Nyam Points!</b>"
                if(commands_result[i] == '2'):
                    hr_hr = ""
                    if(bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr+":bulletorange: <i>Hmm, let's check... *maybe here? or there...*</i><br>Nnope! I can't find "+str(meanings[i][2])+".<br>"
            if(is_hr):
                bot_add = bot_add + hr
            self.da.post_comment(target='B147125B-6E0B-D409-9D20-04F55F5BF453', body=bot_add, comment_type='deviation', commentid=comment_id)
            time.sleep(5)

    def create_reply_sell(self, type, commands_result, meanings, comment_id):
        is_hr = False
        hr = ""
        bot_add = ""
        if (type == 1):
            for i in range(len(commands_result)):
                if (commands_result[i] == '0'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                    hr = "<hr>You received <b>"+str(meanings[i][3]*meanings[i][4])+" NP</b><br /><small>Your current balance: " + str(meanings[i][1]) + " NP<br><a href=" + str(href) + ">Check your profile</a></small>"
                    hr_hr = ""
                    if(bot_add != ""):
                        hr_hr = "<hr />"
                    href = '"'+str(meanings[i][5])+'"'
                    bot_add = bot_add + hr_hr +":bulletgreen: <i>I'll take this!~</i><br>You've successfully sold <a href="+href+">"+ str(meanings[i][2]) + "</a> x" + str(meanings[i][3]) + ""
                if (commands_result[i] == '1'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                    hr = "<hr><small>Your current balance: " + str(meanings[i][1]) + " NP<br><a href=" + str(href) + ">Check your profile</a></small>"
                    hr_hr = ""
                    if (bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr + ":bulletorange: Thank you, bud! I'll ta- ... <i>stop!</i><br>You have no "+str(meanings[i][2])+" in your inventory :<i></i>("
                if (commands_result[i] == '2'):
                    hr_hr = ""
                    if (bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr + ":bulletorange: <i>Hmm, let's check... *maybe here? or there...*</i><br>Nnope! I can't find " + str(meanings[i][2]) + ".<br>"
            if (is_hr):
                bot_add = bot_add + hr
            self.da.post_comment(target='B147125B-6E0B-D409-9D20-04F55F5BF453', comment_type='deviation', body=bot_add, commentid=comment_id)
            time.sleep(5)

    def message_sell(self, comments):
        for i in range(len(comments)):
            cursor = self.cursor
            cnx = self.cnx
            commands_result = []
            meanings = []
            ignoring = False
            if (comments[i].replies == 0 and comments[i].hidden == None):
                comments[i].body = re.sub(r"(\w+)'s", r"\\\'s", comments[i].body)
                comments[i].body = re.sub(r'(\w+)"s', r'\\\"s', comments[i].body)
                list = re.findall('Sell\s(?<=Sell\s).*?(?=<br />|$)', re.sub('&nbsp;', ' ', comments[i].body), re.IGNORECASE)
                for j in range(len(list)):
                    list[j] = re.sub('</span>|<span>|<b>|</b>|<hr>|<hr />|</a>|</hr>', '', list[j])
                    list[j] = re.sub('<a\s(?<=<a\s).*?(?=>)>', '', list[j])
                    list[j] = re.sub('&nbsp;', ' ', list[j])
                    c = int(re.search('(100000)|(0*\d{1,6})', list[j]).group(0))
                    b = re.search('(?<=Sell\s).*?(?='+str(c)+')', list[j], re.IGNORECASE)
                    if(b.group(0) != ""):
                        ignoring = True
                        break
                    b = re.search('(?<=Sell\s'+str(c)+').*?(?=\s)', list[j], re.IGNORECASE)
                    if (b.group(0) != ""):
                        ignoring = True
                        break
                    g = re.search('(?<=Sell\s' + str(c) + '\s).*?(?=$)$', list[j], re.IGNORECASE)
                    old_name = g.group(0)
                    g = re.sub('\s', '', g.group(0))
                    print(g)
                    sql = ("SELECT id, cost_sell, name, type, thumb, href_id FROM items WHERE text_id='" + g + "'")
                    cursor.execute(sql)
                    if (cursor.rowcount > 0):
                        for (item_id, cost, item_name, type, thumb, href_id) in cursor:
                            sql = ("SELECT count FROM inventory WHERE owner='" + comments[i].user.username + "' AND item_id='"+str(item_id)+"'")
                            cursor.execute(sql)
                            for (count) in cursor:
                                user_id = None
                                balance = None
                                if (cursor.rowcount > 0 and count[0] > 0):
                                    sql = ("UPDATE inventory SET count=count-'" + str(c) + "' WHERE owner='" + comments[i].user.username + "' AND item_id='"+str(item_id)+"'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE users SET balance=balance+'" + str(cost * c) + "' WHERE username='" +comments[i].user.username + "'")
                                    cursor.execute(sql)
                                    commands_result.append('0')
                                    sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + comments[i].user.username + "', '" + str(item_name) + "', '" + str(c) + "', 'Selling', now())")
                                    cursor.execute(sql)
                                    sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('" + comments[i].user.username + "', '" + str(cost * c) + "', 'Buying " + str(c) + " " + str(item_name) + "', now())")
                                    cursor.execute(sql)
                                    sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" +comments[i].user.username + "'")
                                    cursor.execute(sql)
                                    sql = ("SELECT user_id, balance FROM users WHERE username='"+comments[i].user.username+"'")
                                    cursor.execute(sql)
                                    for (user_id, balance) in cursor:
                                        user_id = user_id
                                        balance = balance
                                    meanings.append([user_id, balance, item_name, c, cost, href_id])
                                else:
                                    user_id = None
                                    balance = None
                                    commands_result.append('1')
                                    sql = ("SELECT user_id, balance FROM users WHERE username='"+comments[i].user.username+"'")
                                    cursor.execute(sql)
                                    for (user_id, balance) in cursor:
                                        user_id = user_id
                                        balance = balance
                                    meanings.append([user_id, balance, item_name, c])
                    else:
                        user_id = None
                        balance = None
                        commands_result.append('2')
                        sql = ("SELECT user_id, balance FROM users WHERE username='" + comments[i].user.username + "'")
                        cursor.execute(sql)
                        for (user_id, balance) in cursor:
                            user_id = user_id
                            balance = balance
                        meanings.append([user_id, balance, old_name, c])
                if(len(list) > 0 and ignoring == False):
                    self.create_reply_sell(type=1, commands_result=commands_result, meanings=meanings,comment_id=comments[i].commentid)


    def message_buy(self, comments):
       for i in range(len(comments)):
           cursor = self.cursor
           cnx = self.cnx
           commands_result = []
           meanings = []
           ignoring = False
           if (comments[i].replies == 0 and comments[i].hidden == None):
                comments[i].body = re.sub(r"(\w+)'s", r"\\\'s", comments[i].body)
                comments[i].body = re.sub(r'(\w+)"s', r'\\\"s', comments[i].body)
                list = re.findall('Buy\s(?<=Buy\s).*?(?=<br />|$)', re.sub('&nbsp;', ' ', comments[i].body), re.IGNORECASE)
                for j in range(len(list)):
                    list[j] = re.sub('</span>|<span>|<b>|</b>|<hr>|<hr />|</a>|</hr>', '', list[j])
                    list[j] = re.sub('<a\s(?<=<a\s).*?(?=>)>', '', list[j])
                    list[j] = re.sub('&nbsp;', ' ', list[j])
                    c = re.search('(100000)|(0*\d{1,6})', list[j])
                    c = c.group(0)
                    c = int(c)
                    b = re.search('(?<=Buy\s).*?(?='+str(c)+')', list[j], re.IGNORECASE)
                    if(b.group(0) != ""):
                        ignoring = True
                        break
                    b = re.search('(?<=Buy\s'+str(c)+').*?(?=\s)', list[j], re.IGNORECASE)
                    if (b.group(0) != ""):
                        ignoring = True
                        break
                    g = re.search('(?<=Buy\s'+str(c)+'\s).*?(?=$)$', list[j], re.IGNORECASE)
                    old_name = g.group(0)
                    g = re.sub('\s', '', g.group(0))
                    sql = ("SELECT id, cost, name, type, thumb, href_id FROM items WHERE text_id='" + g + "'")
                    cursor.execute(sql)
                    if(cursor.rowcount > 0):
                        for (item_id, cost, item_name, type, thumb, href_id) in cursor:
                            if(type == 0):
                                sql = ("SELECT balance FROM users WHERE username='" + comments[i].user.username + "'")
                                cursor.execute(sql)
                                for balance in cursor:
                                    balance = balance[0]
                                    if(balance-(cost*c) >= 0):
                                        sql = ("SELECT count FROM inventory WHERE owner='" + comments[i].user.username + "' AND item_id='"+str(item_id)+"'")
                                        cursor.execute(sql)
                                        if(cursor.rowcount > 0):
                                            sql = ("UPDATE inventory SET count=count+'"+str(c)+"' WHERE owner='" + comments[i].user.username + "' AND item_id='"+str(item_id)+"'")
                                            cursor.execute(sql)
                                        else:
                                            sql = ("INSERT INTO inventory(item_id, owner, count) VALUES ('"+str(item_id)+"', '"+comments[i].user.username+"', '"+str(c)+"')")
                                            cursor.execute(sql)
                                        sql = ("UPDATE users SET balance=balance-'"+str(cost*c)+"' WHERE username='"+comments[i].user.username+"'")
                                        cursor.execute(sql)
                                        sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('"+comments[i].user.username+"', '-"+str(cost*c)+"', 'Buying "+str(c)+" "+str(item_name)+"', now())")
                                        cursor.execute(sql)
                                        sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" +comments[i].user.username + "'")
                                        cursor.execute(sql)
                                        sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('"+comments[i].user.username+"', '"+str(item_name)+"', '"+str(c)+"', 'Buying', now())")
                                        cursor.execute(sql)
                                        commands_result.append('0')
                                        sql = ("SELECT user_id, balance FROM users WHERE username='"+comments[i].user.username+"'")
                                        cursor.execute(sql)
                                        user_id = None
                                        balance = None
                                        for (user_id, balance) in cursor:
                                            user_id = user_id
                                            balance = balance
                                        meanings.append([user_id, balance, item_name, c, href_id])
                                    else:
                                        user_id = None
                                        balance = None
                                        commands_result.append('1')
                                        sql = ("SELECT user_id, balance FROM users WHERE username='"+comments[i].user.username+"'")
                                        cursor.execute(sql)
                                        for (user_id, balance) in cursor:
                                            user_id = user_id
                                            balance = balance
                                        meanings.append([user_id, balance, item_name, c, href_id])
                    else:
                        user_id = None
                        balance = None
                        commands_result.append('2')
                        sql = ("SELECT user_id, balance FROM users WHERE username='" + comments[i].user.username + "'")
                        cursor.execute(sql)
                        for (user_id, balance) in cursor:
                            user_id = user_id
                            balance = balance
                        meanings.append([user_id, balance, old_name])
                if(len(list) > 0 and ignoring == False):
                    self.create_reply_buy(type=0, commands_result=commands_result, meanings=meanings, comment_id=comments[i].commentid)


