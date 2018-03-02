import deviantart, re, mysql.connector, random
from Shop import Shop
from deviantart.user import User
from Transfer import Transfer
from deviantart.api import DeviantartError
from datetime import datetime, date, time
import time
class Fountain:
    def __init__(self, da, cnx, cursor):
        self.items = ["Shiny Coin", "Refresh Water M", "Potion of Change", "Ancient Potion M", "Fur Potion M", "Cotton Potion M", "Sage Potion M", "Prismatic Potion M", "Aura Potion M"]
        self.chances = {
            "Shiny Coin": 1,
            "Refresh Water M": 7,
            "Potion of Change": 2,
            "Ancient Potion M": 0.5,
            "Fur Potion M": 0.5,
            "Cotton Potion M": 0.5,
            "Sage Potion M": 0.2,
            "Prismatic Potion M": 0.2,
            "Aura Potion M": 0.1
        }
        self.answers = {
            "Nothing": "<br><i>And... nothing more happened.</i>",
            "Shiny Coin": "<br><i><What a luck! You noticed a gold coin lying in the fountain. Now Shiny Coin x1 is in your inventory.</i><br>",
            "Refresh Water M": "<br><i>You decided to get water from the fountain and got Refresh Water M x1!</i><br>",
            "Potion of Change": "<br><i>Nothing happened more until you decided to draw water from the fountain. This water looks unusual! You got Potion of Change x1</i><br>",
            "Ancient Potion M": "<br><i>When you came to the fountain - you felt the power, like something very large and ancient was just here. You've got Ancient Potion M x1!</i><br>",
            "Fur Potion M": "<br><i>You just got the water from the fountain but noticed the hair in it. \"Eww, I will not drink it!\" - your first thought was. However, later you notice that the hair is pretty... magical. And the water too. You got a Fur Potion x1!</i><br>",
            "Cotton Potion M": "<br><i>You notice a cotton candy in the fountain... It is barbarism!! But, hmm, maybe someone was cooking the potions here and leave here this piece? Let's check the water!.. Oh, it was right. You just got a Cotton Potion x1!</i><br>",
            "Sage Potion M": "<br><i>Looking into the water of the fountain, you feel how you are filled with knowledge. You look through the water and see your past and near future. The water in the magic fountain is truly magical today! You see how you are getting a Sage Potion x1!</i><br>",
            "Prismatic Potion M": "<br><i>There is a slight rain around a fountain, but you can't find the clouds. However, you see the beautiful rainbows everywhere. The water in the fountain constantly changes its color and even its taste. You decide to collect some water from the fountain. The vessel becomes an unusual shape and almost shines... How beautiful! You just got a Prismatic Potion x1!</i><br>",
            "Aura Potion M": "<br><i>There is a slight rain around a fountain, but you can't find the clouds. However, you see the beautiful rainbows everywhere. The water in the fountain constantly changes its color and even its taste. You decide to collect some water from the fountain. The vessel becomes an unusual shape and almost shines... How beautiful! You just got a Prismatic Potion x1!</i><br>"
        }
        self.da = da
        self.cnx = cnx
        self.cursor = cursor
        self.temp_comments = None

    def message(self):
        comments = self.da.get_comments(endpoint='deviation', deviationid='E4BD00A0-98EC-65C7-0BFC-43C2833B498F', limit=25)
        comments = comments['thread']
        if (self.temp_comments != comments):
            for i in range(len(comments)):
                cursor = self.cursor
                cnx = self.cnx
                commands_result = []
                meanings = []
                if (comments[i].replies == 0 and comments[i].hidden == None):
                    comments[i].body = re.sub(r"(\w+)'s", r"\\\'s", comments[i].body)
                    comments[i].body = re.sub(r'(\w+)"s', r'\\\"s', comments[i].body)
                    list = re.search('Try\sthe\sluck', comments[i].body, re.IGNORECASE)
                    if(list != None):
                        list = list.group(0)
                        sql = ("SELECT balance FROM users WHERE username='" + str(comments[i].user.username) + "'")
                        cursor.execute(sql)
                        if (cursor.rowcount > 0):
                            for balance5 in cursor:
                                if(balance5[0] > 0):
                                    list = re.sub('</span>|<span>|<b>|</b>|<hr>|<hr />|</hr>|</a>', '', list)
                                    list = re.sub('<a\s(?<=<a\s).*?(?=>)>', '', list)
                                    list = re.sub('&nbsp;', ' ', list)
                                    #date
                                    sql = ("SELECT date FROM transaction WHERE username='"+comments[i].user.username+"' AND note='Magic Fountain' AND count='-1' ORDER BY id DESC LIMIT 1")
                                    cursor.execute(sql)

                                    if(cursor.rowcount > 0):
                                        for(date2) in cursor:
                                            date2 = re.split('-', str(date2[0]))
                                            date2[1] = re.sub('0', '', str(date2[1]))
                                            date2[2] = re.sub('0', '', str(date2[2]))
                                            if (datetime.now().date()-date(int(date2[0]), int(date2[1]), int(date2[2]))).days >= 7:
                                                answers2 = self.random(username=comments[i].user.username, cursor=cursor)
                                                commands_result.append('0')
                                                id1 = 0
                                                balance1 = 0
                                                sql = ("SELECT user_id, balance FROM users WHERE username='"+comments[i].user.username+"'")
                                                cursor.execute(sql)
                                                for id, balance in cursor:
                                                    id1 = id
                                                    balance1 = balance
                                                meanings.append([id1, balance1, answers2])
                                            else:
                                                commands_result.append('2')
                                                meanings.append([(datetime.now().date()-date(int(date2[0]), int(date2[1]), int(date2[2]))).days])

                                    else:
                                        answers2 = self.random(username=comments[i].user.username, cursor=cursor)
                                        commands_result.append('0')
                                        id1 = 0
                                        balance1 = 0
                                        sql = ("SELECT user_id, balance FROM users WHERE username='" + comments[i].user.username + "'")
                                        cursor.execute(sql)
                                        for id, balance in cursor:
                                            id1 = id
                                            balance1 = balance
                                        meanings.append([id1, balance1, answers2])
                                else:
                                    commands_result.append('3')
                        else:
                            sql = ("SELECT username FROM users ORDER BY user_id ASC")
                            cursor.execute(sql)
                            for username in cursor:
                                try:
                                    user = self.da.get_user(username=username[0])
                                except DeviantartError:
                                    user = ""
                                if (str(user.username) == str(comments[i].user.username)):
                                    sql = (
                                    "UPDATE users SET username='" + str(comments[i].user.username) + "' WHERE username='" +
                                    str(username[0]) + "'")
                                    cursor.execute(sql)
                                    sql = (
                                    "UPDATE inventory SET owner='" + comments[i].user.username + "' WHERE owner='" +
                                    username[0] + "'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE transaction SET username='" + comments[
                                        i].user.username + "' WHERE username='" + username[0] + "'")
                                    cursor.execute(sql)
                                    sql = ("UPDATE inventorylog SET username='" + comments[
                                        i].user.username + "' WHERE username='" + username[0] + "'")
                                    cursor.execute(sql)
                                    sql = ("SELECT id FROM transfers WHERE from='" + username[0] + "'")
                                    cursor.execute(sql)
                                    for id in cursor:
                                        sql = ("UPDATE transfers SET from='" + comments[i].user.username + "' WHERE id='" +id[0] + "'")
                                        cursor.execute(sql)
                                    sql = ("SELECT id FROM transfers WHERE to='" + username[0] + "'")
                                    cursor.execute(sql)
                                    for id in cursor:
                                        sql = ("UPDATE transfers SET to='" + comments[i].user.username + "' WHERE id='" + id[0] + "'")
                                        cursor.execute(sql)
                                    break
                            sql = ("SELECT username FROM users WHERE username='" + comments[i].user.username + "'")
                            cursor.execute(sql)
                            if (cursor.rowcount == 0):
                                sql = ("INSERT INTO users (username, balance) VALUES ('" + comments[i].user.username + "', '0')")
                                cursor.execute(sql)
                            commands_result.append('1')
                            id1 = 0
                            balance1 = 0
                            sql = ("SELECT user_id, balance FROM users WHERE username='" + comments[i].user.username + "'")
                            cursor.execute(sql)
                            for id, balance in cursor:
                                id1 = id
                                balance1 = balance
                            meanings.append([id1, balance1])

                        self.create_reply(commands_result=commands_result, meanings=meanings, comment_id=comments[i].commentid)
            self.temp_comments = comments
            time.sleep(20)

    def create_reply(self, commands_result, meanings, comment_id):
        is_hr = False
        hr = ""
        bot_add = ""
        for i in range(len(commands_result)):
            if (commands_result[i] == '0'):
                is_hr = True
                href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                if (hr == ""):
                    hr = "<hr><small>Your current balance: <b>" + str(meanings[i][1]) + " NP</b><br><a href=" + str(
                    href) + ">Check your profile</a></small>"
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + "" + str(meanings[i][2])
            if (commands_result[i] == '1'):
                is_hr = True
                href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                hr = "<hr><small>Your current balance: " + str(meanings[i][1]) + " NP<br><a href=" + str(
                    href) + ">Check your profile</a></small>"
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + "You should have a least one Nyam Point to do this. Come back later!"
            if (commands_result[i] == '2'):
                is_hr = False
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + ""
                if(meanings[i][0] == 6):
                    bot_add = bot_add + "<i>Not now! The Fountain isn't ready for you.</i><br>Please, wait for a new day to get a new try!"
                elif(meanings[i][0] <= 2):
                    bot_add = bot_add + "<i>It seems that you checked this place recently and don't ready for another try...</i><br>Come back in a week!"
                elif(meanings[i][0] <= 4 and meanings[i][0] > 2):
                    bot_add = bot_add + "<i>You don't ready for another try!</i><br>Come back in a couple of days~"
            if(commands_result[i] == '3'):
                is_hr = True
                href = '"https://torimori.info/index.php?page=balance_info&id=' + str(meanings[i][0]) + '"'
                if (hr == ""):
                    hr = "<hr><small>Your current balance: <b>" + str(meanings[i][1]) + " NP</b><br><a href=" + str(
                    href) + ">Check your profile</a></small>"
                hr_hr = ""
                if (bot_add != ""):
                    hr_hr = "<hr />"
                bot_add = bot_add + hr_hr + "<i>You feel like you have to do something before you will be blessed by this fountain... oh, right! At least one Nyam Point will be enough!</i>"
        if (is_hr):
            bot_add = bot_add + hr
        self.da.post_comment(target='E4BD00A0-98EC-65C7-0BFC-43C2833B498F', comment_type='deviation', body=bot_add,
                             commentid=comment_id)
        time.sleep(5)


    def random(self, username, cursor):
        answers2 = ""
        sql = ("UPDATE users SET balance=balance-1 WHERE username='"+str(username)+"'")
        cursor.execute(sql)
        sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('"+str(username)+"', '-1', 'Magic Fountain', now())")
        cursor.execute(sql)
        randNP = random.randint(10, 25)
        sql = ("UPDATE users SET balance=balance+'"+str(randNP)+"' WHERE username='" + str(username) + "'")
        cursor.execute(sql)
        sql = ("INSERT INTO transaction (username, count, note, date) VALUES ('"+str(username)+"', '"+str(randNP)+"', 'Magic Fountain', now())")
        cursor.execute(sql)
        for i in range(len(self.items)):
            randChange = 1 + random.random() * 99
            if(randChange <= self.chances[self.items[i]]):
                sql = ("SELECT id, thumb FROM items WHERE name='"+str(self.items[i])+"'")
                cursor.execute(sql)
                if(cursor.rowcount > 0):
                    for id, thumb in cursor:
                        sql = ("INSERT INTO inventory (item_id, owner, count) VALUES ('"+str(id)+"', '"+username+"', '1')")
                        cursor.execute(sql)
                        sql = ("INSERT INTO inventorylog (username, item, count, note, date) VALUES ('"+username+"', '"+self.items[i]+"', '1', 'Magic Fountain', now())")
                        cursor.execute(sql)
                        answers2 = answers2 + self.answers[self.items[i]] + thumb
        if(answers2 == ""):
            answers2 = answers2 + self.answers['Nothing']
        answers2 = "You received "+str(randNP)+" NP! "+answers2
        return answers2



