import deviantart, mysql.connector, sys, sshtunnel, time, re, random, traceback, requests
from mysql.connector.constants import ClientFlag
from pathlib import Path
from sshtunnel import SSHTunnelForwarder
from deviantart.api import DeviantartError
from mysql.connector.errors import InterfaceError
from mysql.connector.errors import OperationalError
from datetime import datetime, date
from urllib.error import HTTPError

class Bot:
    def ssh_reconnect(self):
        self.server = SSHTunnelForwarder(('212.117.189.3', 22), ssh_pkey='id_rsa', ssh_private_key_password='LA66atituf', ssh_password='O0qa726dwG', ssh_username='torimori', remote_bind_address=('localhost', 3306))
        self.server.start()
        self.mysql_connect()

    def mysql_connect(self):
        self.cnx = mysql.connector.connect(user='torimori_info', password='LA66atituf', host='localhost', port=self.server.local_bind_port, database='torimori_info')
        self.cursor = self.cnx.cursor(buffered=True, dictionary=True)

    def da_connect(self):
        self.da = deviantart.Api("7771", "c8ec5442fe785741b2e5cbad0a7391a9", redirect_uri="https://torimori.info/answer.php", standard_grant_type="authorization_code")
        auth_uri = self.da.auth_uri
        print("Please authorize app: {}".format(auth_uri))

        code = input("Enter code:")

        try:
            self.da.auth(code=code)
        except deviantart.api.DeviantartError as e:
            print("Couldn't authorize user. Error: {}".format(e))
        return self.da.access_token

    def da_reconnect(self):
        self.da.auth(refresh_token=self.da.refresh_token)

    def buy_messages(self, comments):
        for comment in comments:
            commands_result = []
            meanings = []
            ignoring = False
            if (comment.replies == 0 and comment.hidden == None):
                list = re.findall('Buy\s(?<=Buy\s).*?(?=<br />|$)', re.sub('&nbsp;', ' ', comment.body), re.IGNORECASE)
                for stroke in list:
                    stroke = self.tags(stroke)
                    c = re.search('(100000)|(0*\d{1,6})', stroke)
                    if (c == None):
                        ignoring = True
                        break
                    else:
                        if (c.group(0) == ""):
                            ignoring = True
                            break
                        else:
                            c = c.group(0)
                            c = int(c)

                    b = re.search('(?<=Buy\s).*?(?=' + str(c) + ')', stroke, re.IGNORECASE)
                    if (b.group(0) != ""):
                        ignoring = True
                        break
                    b = re.search('(?<=Buy\s' + str(c) + ').*?(?=\s)', stroke, re.IGNORECASE)
                    if (b.group(0) != ""):
                        ignoring = True
                        break
                    g = re.search('(?<=Buy\s' + str(c) + '\s).*?(?=$)$', stroke, re.IGNORECASE)
                    old_name = g.group(0)
                    g = re.sub('\s', '', g.group(0))
                    g = re.sub('\'', '\\\'', g)
                    g = re.sub("\"", "\\\"", g)
                    sql = ("SELECT * FROM users WHERE username='" + comment.user.username + "'")
                    self.cursor.execute(sql)
                    rows_user = self.cursor.fetchall()
                    for row_user in rows_user:
                        sql = ("SELECT * FROM items WHERE text_id='" + g + "'")
                        self.cursor.execute(sql)
                        if (self.cursor.rowcount > 0):
                            rows_item = self.cursor.fetchall()
                            for row_item in rows_item:
                                if (row_item['type'] == 0):
                                    if (row_user['balance'] - (row_item['cost'] * c) >= 0):
                                        commands_result.append('0')
                                        meanings.append([row_user, row_item, c, comment.user.username])
                                    else:
                                        commands_result.append('1')
                                        meanings.append([row_user, row_item])
                        else:
                            commands_result.append('2')
                            meanings.append([row_user, old_name])
                if (len(list) > 0 and ignoring == False):
                    self.create_reply_buy(type=0, commands_result=commands_result, meanings=meanings, comment_id=comment.commentid)

    def create_reply_buy(self, type, commands_result, meanings, comment_id):
        is_hr = False
        hr = ""
        bot_add = ""
        if (type == 0):
            for i in range(len(commands_result)):
                if (commands_result[i] == '0'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]['user_id']) + '"'
                    hr = "<hr><small>Your current balance: " + str(meanings[i][0]['balance']-(meanings[i][1]['cost']*meanings[i][2])) + " NP<br><a href=" + str(href) + ">Check your profile</a></small>"
                    hr_hr = ""
                    if (bot_add != ""):
                        hr_hr = "<hr />"
                    href1 =  str(meanings[i][1]['thumb'])
                    #bot_add = bot_add + hr_hr + ":bulletgreen: Your purchase is successful! Thanks for buying!<br><a href=" + href1 + ">" + str(meanings[i][1]['name']) + "</a> x" + str(meanings[i][2]) + " was added to your inventory."
                    bot_add = bot_add + hr_hr + ":bulletgreen: Your purchase is successful! Thanks for buying!<br> " + href1 +" x" + str(meanings[i][2]) + " was added to your inventory."
                if (commands_result[i] == '1'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]['user_id']) + '"'
                    hr = "<hr><small>Your current balance: " + str(meanings[i][0]['balance']) + " NP<br><a href=" + str(
                        href) + ">Check your profile</a></small>"
                    hr_hr = ""
                    if (bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr + ":bulletorange: <i>Ooops!</i> Sorry, but I can't sell you this.<br>You haven't enough of <b>Nyam Points!</b>"
                if (commands_result[i] == '2'):
                    hr_hr = ""
                    if (bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr + ":bulletorange: <i>Hmm, let's check... *maybe here? or there...*</i><br>Nnope! I can't find " + str(meanings[i][1]) + ".<br>"
            if (is_hr):
                bot_add = bot_add + hr
            self.da.post_comment(target='B147125B-6E0B-D409-9D20-04F55F5BF453', comment_type='deviation', body=bot_add, commentid=comment_id)
            time.sleep(5)
            self.buy(commands_result, meanings)

    def buy(self, commands_result, meanings):
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                sql = ("SELECT * FROM inventory WHERE owner='" + meanings[i][3] + "' AND item_id='" + str(meanings[i][1]['id']) + "'")
                self.cursor.execute(sql)
                if (self.cursor.rowcount > 0):
                    sql = ("UPDATE inventory SET count=count+'" + str(meanings[i][2]) + "' WHERE owner='" + meanings[i][3] + "' AND item_id='" + str(meanings[i][1]['id']) + "'")
                    self.cursor.execute(sql)
                else:
                    sql = ("INSERT INTO inventory(item_id, owner, count) VALUES ('" + str(meanings[i][1]['id']) + "', '" + meanings[i][3] + "', '" + str(meanings[i][2]) + "')")
                    self.cursor.execute(sql)
                sql = ("UPDATE users SET balance=balance-'" + str(meanings[i][1]['cost'] * meanings[i][2]) + "' WHERE username='" + meanings[i][3] + "'")
                self.cursor.execute(sql)
                itemName = re.sub('\'', '\\\'', meanings[i][1]['name'])
                itemName = re.sub("\"", '\\\"', itemName)
                sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('" + meanings[i][3] + "', '-" + str(meanings[i][1]['cost'] * meanings[i][2]) + "', 'Buying " + str(meanings[i][2]) + " " + itemName + "', now())")
                self.cursor.execute(sql)
                sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + meanings[i][3] + "'")
                self.cursor.execute(sql)
                sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + meanings[i][3] + "', '" + itemName + "', '" + str(meanings[i][2]) + "', 'Buying', now())")
                self.cursor.execute(sql)


    def sell_messages(self, comments):
        for comment in comments:
            commands_result = []
            meanings = []
            ignoring = False
            if (comment.replies == 0 and comment.hidden == None):
                list = re.findall('Sell\s(?<=Sell\s).*?(?=<br />|$)', re.sub('&nbsp;', ' ', comment.body), re.IGNORECASE)
                for stroke in list:
                    stroke = self.tags(stroke)
                    c = re.search('(100000)|(0*\d{1,6})', stroke)
                    if (c == None):
                        ignoring = True
                        break
                    else:
                        if (c.group(0) == ""):
                            ignoring = True
                            break
                        else:
                            c = c.group(0)
                            c = int(c)
                    b = re.search('(?<=Sell\s).*?(?='+str(c)+')', stroke, re.IGNORECASE)
                    if(b.group(0) != ""):
                        ignoring = True
                        break
                    b = re.search('(?<=Sell\s'+str(c)+').*?(?=\s)', stroke, re.IGNORECASE)
                    if (b.group(0) != ""):
                        ignoring = True
                        break
                    g = re.search('(?<=Sell\s' + str(c) + '\s).*?(?=$)$', stroke, re.IGNORECASE)
                    old_name = g.group(0)
                    g = re.sub('\s', '', g.group(0))
                    g = re.sub('\'', '\\\'', g)
                    g = re.sub("\"", "\\\"", g)

                    sql = ("SELECT * FROM users WHERE username='" + comment.user.username + "'")
                    self.cursor.execute(sql)
                    rows_user = self.cursor.fetchall()
                    for row_user in rows_user:
                        sql = ("SELECT * FROM items WHERE text_id='" + g + "'")
                        self.cursor.execute(sql)
                        if (self.cursor.rowcount > 0):
                            rows_item = self.cursor.fetchall()
                            for row_item in rows_item:
                                sql = ("SELECT * FROM inventory WHERE owner='" + comment.user.username + "' AND item_id='" + str(row_item['id']) + "'")
                                self.cursor.execute(sql)
                                if (self.cursor.rowcount > 0):
                                    rows_inventory = self.cursor.fetchall()
                                    for row_inventory in rows_inventory:
                                        if (row_inventory['count'] - c >= 0):
                                            commands_result.append('0')
                                            meanings.append([row_user, row_item, c, comment.user.username])
                                        else:
                                            commands_result.append('1')
                                            meanings.append([row_user, row_item, c])
                                else:
                                    commands_result.append('1')
                                    meanings.append([row_user, row_item, c])
                        else:
                            commands_result.append('2')
                            meanings.append([row_user, old_name, c])
                if (len(list) > 0 and ignoring == False):
                    self.create_reply_sell(type=1, commands_result=commands_result, meanings=meanings, comment_id=comment.commentid)

    def create_reply_sell(self, type, commands_result, meanings, comment_id):
        sum = 0
        balance = 0
        is_hr = False
        hr = ""
        bot_add = ""
        if (type == 1):
            for i in range(len(commands_result)):
                if (commands_result[i] == '0'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]['user_id']) + '"'
                    sum = sum + meanings[i][1]['cost_sell']*meanings[i][2]
                    hr = "<small>Your current balance: bal_ance NP<br><a href=" + str(href) + ">Check your profile</a></small>"
                    hr_hr = ""
                    if(bot_add != ""):
                        hr_hr = "<hr />"
                    href = '"'+str(meanings[i][1]['href_id'])+'"'
                    bot_add = bot_add + hr_hr +":bulletgreen: <i>I'll take this!~</i><br>You've successfully sold <a href="+href+">"+ str(meanings[i][1]['name']) + "</a> x" + str(meanings[i][2]) + ""
                if (commands_result[i] == '1'):
                    is_hr = True
                    href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]['user_id']) + '"'
                    hr = "<small>Your current balance: bal_ance NP<br><a href=" + str(href) + ">Check your profile</a></small>"
                    hr_hr = ""
                    if (bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr + ":bulletorange: Thank you, bud! I'll ta- ... <i>stop!</i><br>You have no "+str(meanings[i][1]['name'])+" x"+str(meanings[i][2])+" in your inventory :<i></i>("
                if (commands_result[i] == '2'):
                    hr_hr = ""
                    if (bot_add != ""):
                        hr_hr = "<hr />"
                    bot_add = bot_add + hr_hr + ":bulletorange: <i>Hmm, let's check... *maybe here? or there...*</i><br>Nnope! I can't find " + str(meanings[i][1]) + ".<br>"
                balance = meanings[i][0]['balance']
            if(sum > 0):
                hr = "<hr>You received <b>"+str(sum)+" NP</b><br />"+hr
                hr = re.sub('bal_ance', str(balance+sum), hr)
            else:
                hr = re.sub('bal_ance', str(balance), hr)
                hr = "<hr>"+hr
            if (is_hr):
                bot_add = bot_add + hr
            self.da.post_comment(target='B147125B-6E0B-D409-9D20-04F55F5BF453', comment_type='deviation',body=bot_add, commentid=comment_id)
            time.sleep(5)
            self.sell(commands_result, meanings)

    def sell(self, commands_result, meanings):
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                sql = ("UPDATE inventory SET count=count-'" + str(meanings[i][2]) + "' WHERE owner='" + meanings[i][3] + "' AND item_id='" + str(meanings[i][1]['id']) + "'")
                self.cursor.execute(sql)
                sql = ("UPDATE users SET balance=balance+'" + str(meanings[i][1]['cost_sell'] * meanings[i][2]) + "' WHERE username='" + meanings[i][3] + "'")
                self.cursor.execute(sql)
                commands_result.append('0')
                itemName = re.sub('\'', '\\\'', meanings[i][1]['name'])
                itemName = re.sub("\"", '\\\"', itemName)
                sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + meanings[i][3] + "', '" + itemName + "', '-" + str(meanings[i][2]) + "', 'Selling', now())")
                self.cursor.execute(sql)
                sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('" + meanings[i][3] + "', '" + str(meanings[i][1]['cost_sell'] * meanings[i][2]) + "', 'Selling " + str(meanings[i][2]) + " " + itemName + "', now())")
                self.cursor.execute(sql)
                sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + meanings[i][3] + "'")
                self.cursor.execute(sql)


    def shop(self):
        if (self.server.is_active == True):
            comments = self.da.get_comments(endpoint='deviation', deviationid='B147125B-6E0B-D409-9D20-04F55F5BF453', limit=25)
        else:
            self.ssh_reconnect()
            comments = self.da.get_comments(endpoint='deviation', deviationid='B147125B-6E0B-D409-9D20-04F55F5BF453', limit=25)

        time.sleep(60)
        comments = comments['thread']
        for comment in comments:
            if (comment.replies == 0 and comment.hidden == None):
                self.check_users(comment.user.username)
        self.buy_messages(comments)
        self.sell_messages(comments)


    def check_users(self, username):
                username = self.tags(username)
                is_update = False
                f_time = None
                s_time = None
                sql = ("SELECT * FROM users WHERE username='" + username + "'")
                self.cursor.execute(sql)
                if (self.cursor.rowcount == 0):
                    f_time = str(datetime.today())
                    sql = ("SELECT * FROM users ORDER BY user_id ASC")
                    self.cursor.execute(sql)
                    rows = self.cursor.fetchall()
                    for i, row in enumerate(rows):
                        response = requests.get('https://'+str(row['username'])+'.deviantart.com/')
                        user = response.url
                        user = re.sub('https://|http://|www\.', '', user)
                        user = re.sub('deviantart.com/', '', user)
                        user = re.sub('\?(?<=\?).*?(?=$)$', '', user)
                        user = re.sub('</span>|<b>|</b>|<hr>|<hr />|</a>|</hr>|<sub>|</sub>|<i>|</i>|#|:|@', '', user)
                        user = re.sub('<a\s(?<=<a\s).*?(?=>)>', '', user)
                        user = re.sub('<span\s(?<=<span\s).*?(?=>)>', '', user)
                        user = re.sub('<span>', '', user)
                        user = re.sub('&nbsp;', ' ', user)
                        print(user)
                        if(user == username):
                            if(is_update == False):
                                sql = ("UPDATE users SET username='"+ str(username) +"' WHERE username='"+str(row['username'])+"'")
                                self.cursor.execute(sql)
                                sql = ("UPDATE inventory SET owner='"+str(username)+"' WHERE owner='"+str(row['username'])+"'")
                                self.cursor.execute(sql)
                                sql = ("UPDATE inventorylog SET username='" + str(username) + "' WHERE username='" + str(row['username']) + "'")
                                self.cursor.execute(sql)
                                sql = ("UPDATE transaction SET username='" + str(username) + "' WHERE username='" + str(row['username']) + "'")
                                self.cursor.execute(sql)
                                sql = ("UPDATE `transfers` SET `from`='" + str(username) + "' WHERE `from`='" + str(row['username']) + "'")
                                self.cursor.execute(sql)
                                sql = ("UPDATE `transfers` SET `to`='" + str(username) + "' WHERE `to`='" + str(row['username']) + "'")
                                self.cursor.execute(sql)
                                is_update = True
                                s_time = str(datetime.today())
                                self.save_check(username, f_time, s_time, 1, user)
                                break
                    if(is_update == False):
                        s_time = str(datetime.today())
                        self.save_check(username, f_time, s_time, 0)
                        try:
                            user = self.da.get_user(username=username)
                            time.sleep(10)
                            sql = ("INSERT INTO users (username, balance) VALUES ('" + str(username) + "', '0')")
                            self.cursor.execute(sql)
                        except DeviantartError:
                            return 1
                return 0

    def fountain(self):
        self.items = ["Shiny Coin", "Refresh Water M", "Potion of Change", "Ancient Potion M", "Beast Potion M", "Tailor Potion M", "Sage Potion M", "Prismatic Potion M", "Aura Potion M"]
        self.chances = {
            "Shiny Coin": 2,
            "Refresh Water M": 15,
            "Potion of Change": 7,
            "Ancient Potion M": 3,
            "Beast Potion M": 3,
            "Tailor Potion M": 3,
            "Sage Potion M": 3,
            "Prismatic Potion M": 3,
            "Aura Potion M": 3
        }
        self.answers = {
            "Nothing": "<br><i>And... nothing more happened.</i>",
            "Shiny Coin": "<br><i>What a luck! You noticed a gold coin lying in the fountain. Now Shiny Coin x1 is in your inventory.</i><br>",
            "Refresh Water M": "<br><i>You decided to get water from the fountain and got Refresh Water M x1!</i><br>",
            "Potion of Change": "<br><i>Nothing happened more until you decided to draw water from the fountain. This water looks unusual! You got Potion of Change x1</i><br>",
            "Ancient Potion M": "<br><i>When you came to the fountain - you felt the power, like something very large and ancient was just here. You've got Ancient Potion M x1!</i><br>",
            "Beast Potion M": "<br><i>You just got the water from the fountain but noticed the hair in it. \"Eww, I will not drink it!\" - your first thought was. However, later you notice that the hair is pretty... magical. And the water too. You got a Beast Potion x1!</i><br>",
            "Tailor Potion M": "<br><i>You notice a cotton candy in the fountain... It is barbarism!! But, hmm, maybe someone was cooking the potions here and leave here this piece? Let's check the water!.. Oh, it was right. You just got a Tailor Potion x1!</i><br>",
            "Sage Potion M": "<br><i>Looking into the water of the fountain, you feel how you are filled with knowledge. You look through the water and see your past and near future. The water in the magic fountain is truly magical today! You see how you are getting a Sage Potion x1!</i><br>",
            "Prismatic Potion M": "<br><i>There is a slight rain around a fountain, but you can't find the clouds. However, you see the beautiful rainbows everywhere. The water in the fountain constantly changes its color and even its taste. You decide to collect some water from the fountain. The vessel becomes an unusual shape and almost shines... How beautiful! You just got a Prismatic Potion x1!</i><br>",
            "Aura Potion M": "<br><i>The water in the fountain radiates the glowing steam, and the water shines as if filled with small sparks. Inside the fountain, something flickers like lightning... You took your vessel and fill it with water. You've got an Aura Potion x1!</i><br>"
        }


        if (self.server.is_active == True):
            comments = self.da.get_comments(endpoint='deviation', deviationid='E4BD00A0-98EC-65C7-0BFC-43C2833B498F', limit=25)
        else:
            self.ssh_reconnect()
            comments = self.da.get_comments(endpoint='deviation', deviationid='E4BD00A0-98EC-65C7-0BFC-43C2833B498F', limit=25)
        time.sleep(60)
        comments = comments['thread']
        for comment in comments:
            if (comment.replies == 0 and comment.hidden == None):
                result = self.check_users(comment.user.username)
        self.generate_message(comments)

    def generate_message(self, comments):
        for comment in comments:
            commands_result = []
            meanings = []
            if (comment.replies == 0 and comment.hidden == None):
                list = re.search('Try\sthe\sluck', comment.body, re.IGNORECASE)
                if (list != None):
                    list = list.group(0)
                    sql = ("SELECT * FROM users WHERE username='" + str(comment.user.username) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount > 0):
                        rows_user = self.cursor.fetchall()
                        for row_user in rows_user:
                            if (row_user['balance'] > 0):
                                list = self.tags(list);
                                sql = ("SELECT * FROM transaction WHERE username='" + comment.user.username + "' AND note='Magic Fountain' AND count='-1' ORDER BY id DESC LIMIT 1")
                                self.cursor.execute(sql)
                                if (self.cursor.rowcount > 0):
                                    rows_transaction = self.cursor.fetchall()
                                    for row_transaction in rows_transaction:
                                        transaction_date = row_transaction['date']
                                        transaction_date = re.split('-', str(transaction_date))
                                        if (datetime.now().date() - date(int(transaction_date[0]), int(transaction_date[1]), int(transaction_date[2]))).days >= 7:
                                            current_answers = self.random(username=comment.user.username)
                                            commands_result.append('0')
                                            meanings.append([row_user['user_id'], row_user['balance'], current_answers])
                                        else:
                                            commands_result.append('2')
                                            meanings.append([(datetime.now().date() - date(int(transaction_date[0]), int(transaction_date[1]), int(transaction_date[2]))).days])
                                else:
                                    current_answers = self.random(username=comment.user.username)
                                    commands_result.append('0')
                                    meanings.append([row_user['user_id'], row_user['balance'], current_answers])
                            else:
                                commands_result.append('1')
                                meanings.append([row_user['user_id'], row_user['balance']])
                    self.create_reply_fountain(commands_result=commands_result, meanings=meanings, comment_id=comment.commentid)

    def random(self, username):
        answer = ["", []]
        randNP = random.randint(10, 25)
        answer.append(randNP)
        answer.append(username)
        for i in range(len(self.items)):
            randChange = 1 + random.random() * 99
            if (randChange <= self.chances[self.items[i]]):
                sql = ("SELECT * FROM items WHERE name='" + str(self.items[i]) + "'")
                self.cursor.execute(sql)
                if (self.cursor.rowcount > 0):
                    for row_item in self.cursor:
                        answer[1].append(row_item)
                        answer[0] = answer[0] + self.answers[self.items[i]] + row_item['thumb']
        if (answer[0] == ""):
            answer[0] = answer[0] + self.answers['Nothing']
        answer[0] = "You received " + str(randNP) + " NP! " + answer[0]
        return answer

    def create_reply_fountain(self, commands_result, meanings, comment_id):
        is_hr = False
        hr = ""
        bot_add = ""
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                is_hr = True
                href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                if (hr == ""):
                    hr = "<hr><small>Your current balance: <b>" + str(meanings[i][1]-1+meanings[i][2][2]) + " NP</b><br><a href=" + str(
                        href) + ">Check your profile</a></small>"
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + "" + str(meanings[i][2][0])
            if (commands_result[i] == '1'):
                is_hr = True
                href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                hr = "<hr><small>Your current balance: " + str(meanings[i][1]) + " NP<br><a href=" + str(
                    href) + ">Check your profile</a></small>"
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + "<i>You feel like you have to do something before you will be blessed by this fountain... oh, right! At least one Nyam Point will be enough!</i>"
            if (commands_result[i] == '2'):
                is_hr = False
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ""
                if (meanings[i][0] == 6 or meanings[i][0] == 5):
                    bot_add = bot_add + "<i>Not now! The Fountain isn't ready for you.</i><br>Please, wait for a new day to get a new try!"
                elif (meanings[i][0] <= 2):
                    bot_add = bot_add + "<i>It seems that you checked this place recently and don't ready for another try...</i><br>Come back in a week!"
                elif (meanings[i][0] <= 4 and meanings[i][0] > 2):
                    bot_add = bot_add + "<i>You don't ready for another try!</i><br>Come back in a couple of days~"
        if (is_hr):
            bot_add = bot_add + hr
        self.da.post_comment(target='E4BD00A0-98EC-65C7-0BFC-43C2833B498F', body=bot_add, comment_type='deviation', commentid=str(comment_id))
        time.sleep(5)
        self.fountain_db(commands_result, meanings)


    def fountain_db(self, commands_result, meanings):
        for i in range(len(commands_result)):
            if(commands_result[i] == '0'):
                sql = ("UPDATE users SET balance=balance-1 WHERE user_id='" + str(meanings[i][0]) + "'")
                self.cursor.execute(sql)
                sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('" + str(meanings[i][2][3]) + "', '-1', 'Magic Fountain', now())")
                self.cursor.execute(sql)
                sql = ("UPDATE users SET balance=balance+'" + str(meanings[i][2][2]) + "' WHERE user_id='" + str(meanings[i][0]) + "'")
                self.cursor.execute(sql)
                sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('" + str(meanings[i][2][3]) + "', '" + str(meanings[i][2][2]) + "', 'Magic Fountain', now())")
                self.cursor.execute(sql)
                for row_item in meanings[i][2][1]:
                    sql = ("SELECT * FROM inventory WHERE item_id='" + str(row_item['id']) + "' AND owner='" + str(meanings[i][2][3]) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount == 0):
                        sql = ("INSERT INTO inventory (item_id, owner, count) VALUES ('" + str(row_item['id']) + "', '" + meanings[i][2][3] + "', '1')")
                        self.cursor.execute(sql)
                    else:
                        rows_inventory = self.cursor.fetchall()
                        for row_inventory in rows_inventory:
                            sql = ("UPDATE inventory SET count=count+1 WHERE id='" + str(row_inventory['id']) + "'")
                            self.cursor.execute(sql)
                    sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + meanings[i][2][3] + "', '" + row_item['name'] + "', '1', 'Magic Fountain', now())")
                    self.cursor.execute(sql)

    def bank(self):
        if (self.server.is_active == True):
            comments = self.da.get_comments(endpoint='deviation', deviationid='DBD5B182-144E-A81A-13D5-9696D522391B', limit=25)
        else:
            self.ssh_reconnect()
            comments = self.da.get_comments(endpoint='deviation', deviationid='DBD5B182-144E-A81A-13D5-9696D522391B', limit=25)

        time.sleep(60)
        comments = comments['thread']
        for comment in comments:
            if (comment.replies == 0 and comment.hidden == None):
                self.check_users(comment.user.username)
        self.bank_messages(comments)

    def bank_messages(self, comments):
        user_exist = 0
        for comment in comments:
            commands_result = []
            meanings = []
            ignoring = False
            if (comment.replies == 0 and comment.hidden == None):
                list = re.findall('NP\sTransfer\sto\s(?<=NP\sTransfer\sto\s).*?(?=<br />|$)', re.sub('&nbsp;', ' ', comment.body), re.IGNORECASE)
                for stroke in list:
                    stroke = re.sub('</span>|<b>|</b>|<hr>|<hr />|</a>|</hr>|<sub>|</sub>|<i>|</i>|#|:|@', '', stroke)
                    stroke = re.sub('<a\s(?<=<a\s).*?(?=>)>', '', stroke)
                    stroke = re.sub('<span\s(?<=<span\s).*?(?=>)>', '', stroke)
                    stroke = re.sub('<span>', '', stroke)
                    stroke = re.sub('&nbsp;', ' ', stroke)
                    c = re.search('\s((100000)|(0*\d{1,6}))', stroke)
                    if (c == None):
                        ignoring = True
                        break
                    else:
                        if (c.group(0) == ""):
                            ignoring = True
                            break
                        else:
                            c = c.group(0)
                            c = int(c)
                    g = re.search('(?<=NP Transfer to\s).*?(?=' + str(c) + ')', stroke, re.IGNORECASE)
                    g = re.sub('\s', '', g.group(0))
                    g = re.sub('\'', '\\\'', g)
                    g = re.sub("\"", "\\\"", g)
                    sql = ("SELECT * FROM users WHERE username='" + str(g) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount <= 0):
                        user_exist = self.check_users(str(g))
                        print(user_exist)
                        if(user_exist == 1):
                            commands_result.append('2')
                            meanings.append([g])
                            continue
                    rows_user_recipient = self.cursor.fetchall()
                    for row_user_recipient in rows_user_recipient:
                        sql = ("SELECT * FROM users WHERE username='" + str(comment.user.username) + "'")
                        self.cursor.execute(sql)
                        rows_user = self.cursor.fetchall()
                        for row_user in rows_user:
                            if (row_user['balance'] - c >= 0):
                                commands_result.append('0')
                                meanings.append([g, row_user, row_user_recipient, comment.user.username, c])
                            else:
                                commands_result.append('1')
                                meanings.append([row_user['user_id'], row_user['balance']])
                if (len(list) > 0 and ignoring == False):
                    self.create_reply_bank(commands_result=commands_result, meanings=meanings,comment_id=comment.commentid)

    def create_reply_bank(self, commands_result, meanings, comment_id):
        is_hr = False
        hr = ""
        bot_add = ""
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                is_hr = True
                if (hr == ""):
                    hr = "<hr><small>Your current balance: <b>" + str(meanings[i][1]['balance']-meanings[i][4]) + " NP</b><br>" + str(
                        meanings[i][0]) + "'s current balance: " + str(meanings[i][2]['balance']+meanings[i][4]) + " NP</small>"
                else:
                    hr = re.sub('</small>', "<br />" + str(meanings[i][0]) + "'s current balance: " + str(
                        meanings[i][2]['balance']+meanings[i][4]) + " NP</small>", hr)
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ":bulletgreen: The transfer is successful!<br>Thanks for using tori-services~ ♪<br><i><small>(This is an automated message, <u>don't reply</u>!)</small></i>"
            if (commands_result[i] == '1'):
                is_hr = True
                href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                hr = "<hr><small>Your current balance: " + str(meanings[i][1]) + " NP<br><a href=" + str(
                    href) + ">Check your profile</a></small>"
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ":bulletorange: <i>Ooops!</i> Sorry, but we can't do this.<br>You haven't enough of <b>Nyam Points!</b>"
            if (commands_result[i] == '2'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ":bulletorange: <i>Aaaa!!~ we have some problems with your request!</i><br>User <i>" + meanings[i][0] + "</i> <b>wasn't found</b> in our databank."
        if (is_hr):
            bot_add = bot_add + hr
        self.da.post_comment(target='DBD5B182-144E-A81A-13D5-9696D522391B', comment_type='deviation', body=bot_add,commentid=comment_id)
        time.sleep(10)
        self.transfer(commands_result, meanings)

    def transfer(self, commands_result, meanings):
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                sql = ("UPDATE users SET balance=balance-'" + str(meanings[i][4]) + "' WHERE username='" + str(meanings[i][3]) + "'")
                self.cursor.execute(sql)
                sql = ("UPDATE users SET balance=balance+'" + str(meanings[i][4]) + "' WHERE username='" + str(meanings[i][0]) + "'")
                self.cursor.execute(sql)
                sql = ("INSERT INTO `transfers` (`from`, `to`, `count`) VALUES ('" + str(meanings[i][3]) + "', '" + str(meanings[i][0]) + "', '" + str(meanings[i][4]) + "')")
                self.cursor.execute(sql)
                sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + meanings[i][3] + "'")
                self.cursor.execute(sql)
                sql = ("UPDATE users SET last_transaction_time=now() WHERE username='" + str(meanings[i][0]) + "'")
                self.cursor.execute(sql)
                sql = ("SELECT * FROM `transfers` WHERE `from`='" + str(meanings[i][3]) + "' AND `to`='" + str(meanings[i][0]) + "' ORDER BY `id` DESC")
                self.cursor.execute(sql)
                last_transfers = self.cursor.fetchall()
                for last_transfer in last_transfers:
                    href = '<a href="https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][2]['user_id']) + '">' + str(meanings[i][0]) + '</a>'
                    sql = ("INSERT INTO transaction (username, count, note, transfer_id, date) VALUES ('" + str(meanings[i][3]) + "', '-" + str(meanings[i][4]) + "', 'To " + href + "', '" + str(last_transfer['id']) + "', now())")
                    self.cursor.execute(sql)
                    href = '<a href="https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][1]['user_id']) + '">' + str(meanings[i][3]) + '</a>'
                    sql = ("INSERT INTO transaction (username, count, note, transfer_id, date) VALUES ('" + str(meanings[i][0]) + "', '" + str(meanings[i][4]) + "', 'From " + href + "', '" + str(last_transfer['id']) + "', now())")
                    self.cursor.execute(sql)

    def logging(self, e):
        file = Path("log.txt")
        if(file.exists()):
            file = open('log.txt', 'a')
        else:
            file = open('log.txt', 'w')
        form = ""
        form = str(form + "---------------------------------------------------------------------------------------------\n")
        form = str(form + "[" +str(datetime.today())+ "]\n")
        form = str(form + str(e) + "\n")
        form = str(form + "---------------------------------------------------------------------------------------------\n")

        file.write(str(form))

    def save_check(self, name, f_time, s_time, result, name2=""):
        file = Path("log.txt")
        if(file.exists()):
            file = open('log.txt', 'a')
        else:
            file = open('log.txt', 'w')
        form = ""
        form = str(form + "---------------------------------------------------------------------------------------------\n")
        form = str(form + "[" +str(datetime.today())+ "]\n")
        form = str(form + "Start check user with name " + str(name) + " "+  str(f_time) + "\n")
        if(result == 0):
            form = str(form + "Result is not found! "+ str(s_time) +"\n")
        if(result == 1):
            form = str(form + "Result is found. " + str(name2) + "is " + str(name) + " " + str(s_time) + "\n")
        form = str(form + "---------------------------------------------------------------------------------------------\n")

        file.write(str(form))


    def start_method(self, method):
        try:
            if(method == 0):
                self.shop()
            if(method == 1):
                self.fountain()
            if(method == 2):
                self.bank()
            if(method == 3):
                self.forest_ivent()
            if(method == 4):
                self.shovel_ivent()
            if(method == 5):
                self.chest_ivent()
        except DeviantartError as e:
            print(e.message)
            self.logging(traceback.format_exc())
            self.da_reconnect()
        except InterfaceError as e:
            print(e.msg)
            self.cnx.close()
            self.cursor.close()
            self.logging(traceback.format_exc())
            self.mysql_connect()
        except OperationalError as e:
            print(e.msg)
            self.cnx.close()
            self.cursor.close()
            self.logging(traceback.format_exc())
            self.mysql_connect()
        except HTTPError as e:
            print(e.message)
            self.logging(traceback.format_exc())
            self.da_reconnect()

    def inventory_restore(self):
        sql = ("SELECT * FROM inventorylog ORDER BY id ASC")
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        oneprocent = self.cursor.rowcount/100
        for i, row in enumerate(rows):
            item = row['item']
            item = re.sub('\'', '\\\'', item)
            item = re.sub("\"", "\\\"", item)
            sql = ("SELECT * FROM items WHERE name='"+str(item)+"'")
            self.cursor.execute(sql)
            row_item = self.cursor.fetchone()
            sql = ("SELECT * FROM inventory WHERE owner='" + str(row['username']) + "' AND item_id='"+str(row_item['id'])+"'")
            self.cursor.execute(sql)
            if(self.cursor.rowcount <= 0):
                sql = ("INSERT INTO inventory(item_id, owner, count) VALUES ('"+str(row_item['id'])+"', '"+str(row['username'])+"', '"+str(row['count'])+"')")
                self.cursor.execute(sql)
            else:
                sql = ("UPDATE inventory SET count=count+'"+str(row['count'])+"' WHERE owner='" + str(row['username']) + "' AND item_id='"+str(row_item['id'])+"'")
                self.cursor.execute(sql)
            print((i+1)/oneprocent)

    def tags(self, text):
        stroke = re.sub('</div>|</span>|<b>|</b>|<hr>|<hr />|</hr>|</a>|<sub>|</sub>|<i>|</i>|#|@|:', '', text)
        stroke = re.sub('<a\s(?<=<a\s).*?(?=>)>', '', stroke)
        stroke = re.sub('<span\s(?<=<span\s).*?(?=>)>', '', stroke)
        stroke = re.sub('<span>', '', stroke)
        stroke = re.sub('<div\s(?<=<div\s).*?(?=>)>', '', stroke)
        stroke = re.sub('<div>', '', stroke)
        stroke = re.sub('&nbsp;', ' ', stroke)
        stroke = re.sub('<br>|<br/>|<br />|</br>', ' ', stroke)
        return stroke


#Forest
    def forest_ivent(self):
        self.items_forest = ["Leaves", "Acorn", "Unknown Seeds", "Orange Banana", "Shovel",
                      "Ancient Mossy Tori Charm", "Twisted Wooden Scepter"]
        self.chances_forest = {
            "Leaves": 100,
            "Acorn": 70,
            "Unknown Seeds": 25,
            "Orange Banana": 25,
            "Shovel": 10,
            "Ancient Mossy Tori Charm": 5,
            "Twisted Wooden Scepter": 5
        }
        self.counts_forest = {
            "Leaves": [1, 1],
            "Acorn": [1, 1],
            "Unknown Seeds": [1, 1],
            "Orange Banana": [1, 1],
            "Shovel": [1, 1],
            "Ancient Mossy Tori Charm": [1, 1],
            "Twisted Wooden Scepter": [1, 1]
        }

        if (self.server.is_active == True):
            comments = self.da.get_comments(endpoint='deviation', deviationid='3AC75D03-4A7B-6FE0-937C-A83E7302F4A5', limit=25)
        else:
            self.ssh_reconnect()
            comments = self.da.get_comments(endpoint='deviation', deviationid='3AC75D03-4A7B-6FE0-937C-A83E7302F4A5', limit=25)
        time.sleep(60)
        comments = comments['thread']
        for comment in comments:
            if (comment.replies == 0 and comment.hidden == None):
                self.check_users(comment.user.username)
        self.forest_messages(comments)

    def forest_messages(self, comments):
        for comment in comments:
            commands_result = []
            meanings = []
            comment.body = self.tags(comment.body)
            comment.body = re.sub('\s', '', comment.body)
            if (comment.replies == 0 and comment.hidden == None):
                list = re.search('^Explore$', comment.body, re.IGNORECASE)
                if (list != None):
                    list = list.group(0)
                    sql = ("SELECT * FROM users WHERE username='" + str(comment.user.username) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount > 0):
                        rows_user = self.cursor.fetchall()
                        for row_user in rows_user:
                            transaction_date = row_user['forest_time']
                            if(transaction_date != None):
                                transaction_date = re.split('-', str(transaction_date))
                                transaction_date[1] = re.sub('0', '', str(transaction_date[1]))
                                transaction_date[2] = re.sub('0', '', str(transaction_date[2]))
                                if (datetime.now().date() - date(int(transaction_date[0]), int(transaction_date[1]), int(transaction_date[2]))).days >= 1:
                                    current_answers = self.new_random(username=comment.user.username, items=self.items_forest, chances=self.chances_forest, counts=self.counts_forest)
                                    commands_result.append('0')
                                    meanings.append([row_user['user_id'], row_user['balance'], current_answers])
                                else:
                                    commands_result.append('2')
                            else:
                                current_answers = self.new_random(username=comment.user.username, items=self.items_forest, chances=self.chances_forest, counts=self.counts_forest)
                                commands_result.append('0')
                                meanings.append([row_user['user_id'], row_user['balance'], current_answers])
                    self.create_reply_forest(commands_result=commands_result, meanings=meanings, comment_id=comment.commentid)

    def create_reply_forest(self, commands_result, meanings, comment_id):
        bot_add = ""
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + "<i>You decided to go through the forest...</i><br><br><hr>" + str(meanings[i][2][0])
            if (commands_result[i] == '2'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ':bulletorange: <i>"aaa... what? forest? yaaawn~"<br>You are so tired to explore this place today. Try again tomorrow!</i>'
        self.da.post_comment(target='3AC75D03-4A7B-6FE0-937C-A83E7302F4A5', body=bot_add, comment_type='deviation', commentid=str(comment_id))
        time.sleep(5)
        self.forest_db(commands_result, meanings)

    def forest_db(self, commands_result, meanings):
        for i in range(len(commands_result)):
            if(commands_result[i] == '0'):
                sql = ("UPDATE users SET forest_time=now() WHERE username='" + str(meanings[i][2][2]) + "'")
                self.cursor.execute(sql)
                for j, row_item in enumerate(meanings[i][2][1]):
                    sql = ("SELECT * FROM inventory WHERE item_id='" + str(row_item['id']) + "' AND owner='" + str(meanings[i][2][2]) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount == 0):
                        sql = ("INSERT INTO inventory (item_id, owner, count) VALUES ('" + str(row_item['id']) + "', '" + str(meanings[i][2][2]) + "', '" + str(meanings[i][2][3][j]) + "')")
                        self.cursor.execute(sql)
                    else:
                        rows_inventory = self.cursor.fetchall()
                        for row_inventory in rows_inventory:
                            sql = ("UPDATE inventory SET count=count+" + str(meanings[i][2][3][j]) + " WHERE id='" + str(row_inventory['id']) + "'")
                            self.cursor.execute(sql)
                    sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + str(meanings[i][2][2]) + "', '" + str(row_item['name']) + "', '" + str(meanings[i][2][3][j]) + "', 'Treasure Hunt Event: Exploring', now())")
                    self.cursor.execute(sql)

#Shovel pt. 1

    def shovel_ivent(self):
        self.items_shovel = ["Sand", "Bottle Cap", "Empty Can", "Common Seashell", "Sea Chest",
                      "Unicorn Seashell", "Pearl", "Rainbow Glass Shard"]
        self.chances_shovel = {
            "Sand": 100,
            "Bottle Cap": 80,
            "Empty Can": 70,
            "Common Seashell": 50,
            "Sea Chest": 40,
            "Unicorn Seashell": 15,
            "Pearl": 5,
            "Rainbow Glass Shard": 5,
        }

        self.counts_shovel = {
            "Sand": [2, 5],
            "Bottle Cap": [1, 2],
            "Empty Can": [1, 2],
            "Common Seashell": [1, 2],
            "Sea Chest": [1, 1],
            "Unicorn Seashell": [1, 1],
            "Pearl": [1, 1],
            "Rainbow Glass Shard": [1, 1],
        }

        if (self.server.is_active == True):
            comments = self.da.get_comments(endpoint='deviation', deviationid='3AC75D03-4A7B-6FE0-937C-A83E7302F4A5', limit=25)
        else:
            self.ssh_reconnect()
            comments = self.da.get_comments(endpoint='deviation', deviationid='3AC75D03-4A7B-6FE0-937C-A83E7302F4A5', limit=25)

        time.sleep(60)
        comments = comments['thread']
        for comment in comments:
            if (comment.replies == 0 and comment.hidden == None):
                self.check_users(comment.user.username)
        self.shovel_messages(comments)

    def shovel_messages(self, comments):
        for comment in comments:
            commands_result = []
            meanings = []
            comment.body = self.tags(comment.body)
            if (comment.replies == 0 and comment.hidden == None):
                list = re.findall('^Dig$', comment.body, re.IGNORECASE)
                if (list != None and len(list) > 0):
                    for stroke in list:
                        sql = ("SELECT * FROM users WHERE username='" + str(comment.user.username) + "'")
                        self.cursor.execute(sql)
                        if (self.cursor.rowcount > 0):
                            rows_user = self.cursor.fetchall()
                            for row_user in rows_user:
                                sql = ("SELECT * FROM inventory WHERE owner='"+str(comment.user.username)+"' and item_id='112' and count>'0'")
                                self.cursor.execute(sql)
                                if (self.cursor.rowcount > 0):
                                    current_answers = self.new_random(username=comment.user.username, items=self.items_shovel, chances=self.chances_shovel, counts=self.counts_shovel)
                                    commands_result.append('0')
                                    meanings.append([row_user['user_id'], row_user['balance'], current_answers])
                                else:
                                    commands_result.append('2')
                    self.create_reply_shovel(commands_result=commands_result, meanings=meanings, comment_id=comment.commentid)

#Random v. 2
    def new_random(self, username, items, chances, counts, loop=False, surely=1):
        temp_items = items.copy()
        answer = ["", []]
        answer.append(username)
        answer.append([])
        if(loop):
            while len(answer[1]) < surely:
                for item in temp_items:
                        randCount = 0
                        randChange = 1 + random.random() * 99
                        if (randChange <= chances[item]):
                            randCount += random.randint(counts[item][0], counts[item][1])
                            sql = ("SELECT * FROM items WHERE name='" + str(item) + "'")
                            self.cursor.execute(sql)
                            if (self.cursor.rowcount > 0):
                                rows_item = self.cursor.fetchall()
                                for row_item in rows_item:
                                    if (randCount > 0):
                                        answer[1].append(row_item)
                                        answer[3].append(randCount)
                                        answer[0] = answer[0] + row_item['thumb'] + " x" + str(randCount) + " "
                                        temp_items.remove(item)
        else:
            for i in range(len(items)):
                randCount = 0
                randChange = 1 + random.random() * 99
                if (randChange <= chances[items[i]]):
                    randCount += random.randint(counts[items[i]][0], counts[items[i]][1])
                    sql = ("SELECT * FROM items WHERE name='" + str(items[i]) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount > 0):
                        rows_item = self.cursor.fetchall()
                        for row_item in rows_item:
                            if (randCount > 0):
                                answer[1].append(row_item)
                                answer[3].append(randCount)
                                answer[0] = answer[0] + row_item['thumb'] + " x" + str(randCount) + " "
        if (answer[0] == ""):
            answer[0] = "<i>Nothing interesting...</i>"
        else:
            answer[0] = "You've found:<br>" + answer[0]
        return answer

#Shovel pt. 2
    def create_reply_shovel(self, commands_result, meanings, comment_id):
        bot_add = ""
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                href = '<a href="http://fav.me/dcgour3">Shovel</a>'
                bot_add = bot_add + hr_hr + "<i>You used a shovel until it broke...</i><br><hr>"+href+" x1 has been removed from your inventory!<br><br>" + str(meanings[i][2][0])
            if (commands_result[i] == '2'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                href = '<a href="http://fav.me/dcgour3">Shovel</a>'
                bot_add = bot_add + hr_hr + ":bulletorange: <i>Oops! You have no "+href+" in your inventory!</i>"
        self.da.post_comment(target='3AC75D03-4A7B-6FE0-937C-A83E7302F4A5', body=bot_add, comment_type='deviation', commentid=str(comment_id))
        time.sleep(5)
        self.shovel_db(commands_result, meanings)

    def shovel_db(self, commands_result, meanings):
        for i in range(len(commands_result)):
            if(commands_result[i] == '0'):
                sql = ("SELECT * FROM inventory WHERE item_id='112' AND owner='" + str(meanings[i][2][2]) + "'")
                self.cursor.execute(sql)
                rows_shovel = self.cursor.fetchall()
                for row_shovel in rows_shovel:
                    sql = ("UPDATE inventory SET count=count-1 WHERE id='" + str(row_shovel['id']) + "'")
                    self.cursor.execute(sql)
                sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + str(meanings[i][2][2]) + "', 'Shovel', '-1', 'Treasure Hunt Event: Dig', now())")
                self.cursor.execute(sql)
                for j, row_item in enumerate(meanings[i][2][1]):
                    sql = ("SELECT * FROM inventory WHERE item_id='" + str(row_item['id']) + "' AND owner='" + str(meanings[i][2][2]) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount == 0):
                        sql = ("INSERT INTO inventory (item_id, owner, count) VALUES ('" + str(row_item['id']) + "', '" + str(meanings[i][2][2]) + "', '" + str(meanings[i][2][3][j]) + "')")
                        self.cursor.execute(sql)
                    else:
                        rows_inventory = self.cursor.fetchall()
                        for row_inventory in rows_inventory:
                            sql = ("UPDATE inventory SET count=count+" + str(meanings[i][2][3][j]) + " WHERE id='" + str(row_inventory['id']) + "'")
                            self.cursor.execute(sql)
                    sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + str(meanings[i][2][2]) + "', '" + str(row_item['name']) + "', '" + str(meanings[i][2][3][j]) + "', 'Treasure Hunt Event: Dig', now())")
                    self.cursor.execute(sql)

#Open Chest
    def chest_ivent(self):
        self.items_chests = { "Sea": ["Common Seashell", "Sea Star", "Fir Seaweed", "Unicorn Seashell", "Plushy Octopie Charm",
                      "Pearl", "Torimori Figurine - In Balance", "Mystery Rune 4", "Water Potion M", "Water Potion S"]}
        self.chances_chests = {
            "Sea": {
                "Common Seashell": 80,
                "Sea Star": 70,
                "Fir Seaweed": 50,
                "Unicorn Seashell": 20,
                "Plushy Octopie Charm": 20,
                "Pearl": 20,
                "Torimori Figurine - In Balance": 20,
                "Mystery Rune 4": 20,
                "Water Potion M": 5,
                "Water Potion S": 10
            }
        }

        self.counts_chests = {
            "Sea": {
                "Common Seashell": [1, 2],
                "Sea Star": [1, 1],
                "Fir Seaweed": [1, 2],
                "Unicorn Seashell": [1, 1],
                "Plushy Octopie Charm": [1, 1],
                "Pearl": [1, 1],
                "Torimori Figurine - In Balance": [1, 1],
                "Mystery Rune 4": [1, 1],
                "Water Potion M": [1, 1],
                "Water Potion S": [1, 1]
            }
        }

        if (self.server.is_active == True):
            comments = self.da.get_comments(endpoint='deviation', deviationid='53DBF35E-5567-A12A-9B50-FD7556DFAC3B', limit=25)
        else:
            self.ssh_reconnect()
            comments = self.da.get_comments(endpoint='deviation', deviationid='53DBF35E-5567-A12A-9B50-FD7556DFAC3B', limit=25)

        time.sleep(60)
        comments = comments['thread']
        for comment in comments:
            if (comment.replies == 0 and comment.hidden == None):
                self.check_users(comment.user.username)
        self.chest_messages(comments)

    def chest_messages(self, comments):
        for comment in comments:
            commands_result = []
            meanings = []
            comment.body = self.tags(comment.body)
            if (comment.replies == 0 and comment.hidden == None):
                list = re.findall('^Open\s(?<=^Open\s).*?(?=\sChest$)\sChest$', comment.body, re.IGNORECASE)
                if (list != None and len(list) > 0):
                    for stroke in list:
                        chest_type = re.search('(?<=^Open\s).*?(?=\sChest$)', stroke, re.IGNORECASE)
                        chest_type = chest_type.group(0)
                        chest_type.capitalize()
                        sql = ("SELECT * FROM users WHERE username='" + str(comment.user.username) + "'")
                        self.cursor.execute(sql)
                        if (self.cursor.rowcount > 0):
                            rows_user = self.cursor.fetchall()
                            for row_user in rows_user:
                                sql = ("SELECT * FROM items WHERE name='" + str(chest_type.capitalize()) + " Chest'")
                                self.cursor.execute(sql)
                                rows_chest = self.cursor.fetchall()
                                for row_chest in rows_chest:
                                    sql = ("SELECT * FROM inventory WHERE item_id='" + str(row_chest['id']) + "' and owner='"+ str(comment.user.username) +"'")
                                    self.cursor.execute(sql)
                                    rows_chest_item = self.cursor.fetchall()
                                    if(self.cursor.rowcount > 0):
                                        for row_chest_item in rows_chest_item:
                                            if row_chest_item['count'] > 0:
                                                #Check keys, but in new version of this code, not now
                                                sql = ("SELECT * FROM inventory WHERE item_id='117' and owner='" + str(comment.user.username) + "'")
                                                self.cursor.execute(sql)
                                                rows_key = self.cursor.fetchall()
                                                if (self.cursor.rowcount > 0):
                                                    for row_key in rows_key:
                                                        if row_key['count'] > 0:
                                                            current_answers = self.new_random(username=comment.user.username, items=self.items_chests['Sea'],chances=self.chances_chests['Sea'], counts=self.counts_chests['Sea'], loop=True, surely=3)
                                                            commands_result.append('0')
                                                            meanings.append([row_user['user_id'], row_user['balance'], current_answers, row_chest['id']])
                                                        else:
                                                            commands_result.append('1')
                                                else:
                                                    commands_result.append('1')
                                            else:
                                                commands_result.append('2')
                                    else:
                                        commands_result.append('2')
                    self.create_reply_chest(commands_result=commands_result, meanings=meanings, comment_id=comment.commentid)

    def create_reply_chest(self, commands_result, meanings, comment_id):
        bot_add = ""
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                href = '<a href="http://fav.me/dcgous4">Any Key</a>'
                bot_add = bot_add + hr_hr + ":bulletgreen: "+ href +" was removed from your inventory<br><i> — Success!! Let check what we've got...<hr>" + str(meanings[i][2][0]) + "</i>"

            if (commands_result[i] == '1'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                href = '<a href="http://fav.me/dcgous4">Any Key</a>'
                bot_add = bot_add + hr_hr + ":bulletorange: <i>— Oooff... I'm so sorry, but I can't do that now! This was locked by magic. If you have a magical key, for example, "+ href +", at least one will be enough to open this chest!</i>"

            if (commands_result[i] == '2'):
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ":bulletorange: <i>— Aww... where is your chest? Bring me the chest with any key and I'll gladly open it!</i>"
        self.da.post_comment(target='53DBF35E-5567-A12A-9B50-FD7556DFAC3B', body=bot_add, comment_type='deviation', commentid=str(comment_id))
        time.sleep(5)
        self.chest_db(commands_result, meanings)

    def chest_db(self, commands_result, meanings):
        for i in range(len(commands_result)):
            if(commands_result[i] == '0'):
                sql = ("SELECT * FROM inventory WHERE item_id='117' AND owner='" + str(meanings[i][2][2]) + "'")
                self.cursor.execute(sql)
                rows_key = self.cursor.fetchall()
                for row_key in rows_key:
                    sql = ("UPDATE inventory SET count=count-1 WHERE id='" + str(row_key['id']) + "'")
                    self.cursor.execute(sql)


                sql = ("SELECT * FROM inventory WHERE item_id='"+str(meanings[i][3])+"' AND owner='" + str(meanings[i][2][2]) + "'")
                self.cursor.execute(sql)
                rows_chest = self.cursor.fetchall()
                for row_chest in rows_chest:
                    sql = ("UPDATE inventory SET count=count-1 WHERE id='" + str(row_chest['id']) + "'")
                    self.cursor.execute(sql)


                sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + str(meanings[i][2][2]) + "', 'Any Key', '-1', 'Sea Chest', now())")
                self.cursor.execute(sql)

                sql = ("SELECT * FROM items WHERE id='" + str(meanings[i][3]) + "'")
                self.cursor.execute(sql)
                rows_chest = self.cursor.fetchall()
                for row_chest in rows_chest:
                    sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + str(meanings[i][2][2]) + "', '"+str(row_chest['name'])+"', '-1', 'Sea Chest', now())")
                    self.cursor.execute(sql)

                for j, row_item in enumerate(meanings[i][2][1]):
                    sql = ("SELECT * FROM inventory WHERE item_id='" + str(row_item['id']) + "' AND owner='" + str(meanings[i][2][2]) + "'")
                    self.cursor.execute(sql)
                    if (self.cursor.rowcount == 0):
                        sql = ("INSERT INTO inventory (item_id, owner, count) VALUES ('" + str(row_item['id']) + "', '" + str(meanings[i][2][2]) + "', '" + str(meanings[i][2][3][j]) + "')")
                        self.cursor.execute(sql)
                    else:
                        rows_inventory = self.cursor.fetchall()
                        for row_inventory in rows_inventory:
                            sql = ("UPDATE inventory SET count=count+" + str(meanings[i][2][3][j]) + " WHERE id='" + str(row_inventory['id']) + "'")
                            self.cursor.execute(sql)
                    sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('" + str(meanings[i][2][2]) + "', '" + str(row_item['name']) + "', '" + str(meanings[i][2][3][j]) + "', 'Sea Chest', now())")
                    self.cursor.execute(sql)

    def __init__(self):
        with SSHTunnelForwarder(('212.117.189.3', 22), ssh_pkey='id_rsa', ssh_private_key_password='LA66atituf', ssh_password='O0qa726dwG', ssh_username='torimori', remote_bind_address=('localhost', 3306)) as self.server:
            self.cnx = None
            self.cursor = None
            self.da = None
            self.mysql_connect()
            if self.da_connect():
                while True:
                    #self.start_method(3)
                    self.start_method(0)
                    self.start_method(1)
                    self.start_method(2)
                    #self.start_method(4)
                    self.start_method(5)

Bot()