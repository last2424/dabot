#import library
import deviantart, re, mysql.connector, requests
from Shop import Shop
from deviantart.user import User
from Transfer import Transfer
from deviantart.api import DeviantartError
from datetime import datetime, date, time
from fountain import Fountain
import time
from sshtunnel import SSHTunnelForwarder
#cnx = None
class Main:

    def __init__(self):
        with SSHTunnelForwarder(('212.117.189.3', 22), ssh_pkey='id_rsa', ssh_private_key_password='LA66atituf',
                        ssh_password='O0qa726dwG', ssh_username='torimori',
                        remote_bind_address=('localhost', 3306)) as self.server:
            self.cnx = mysql.connector.connect(user='torimori_info', password='LA66atituf', host='localhost',
                                  port=self.server.local_bind_port, database='torimori_info')
            self.cursor = self.cnx.cursor(buffered=True)
            self.da = deviantart.Api("7458", "98cdea34f4c07825335f32870d6f73b6", redirect_uri="https://torimori.info/answer.php", standard_grant_type="authorization_code")
    #create new client with the authorization code grant type
    #The authorization URI: redirect your users to this
            self.auth_uri = self.da.auth_uri
            self.shop = None
            self.transfer = None
            self.fountain = None
            print ("Please authorize app: {}".format(self.auth_uri))

    #Enter the value of the code parameter, found in to which DeviantArt redirected to
            code = input("Enter code:")

    #Try to authenticate with the given code
            try:
                self.da.auth(code=code)
            except deviantart.api.DeviantartError as e:
                print ("Couldn't authorize user. Error: {}".format(e))

    #If authenticated and access_token present
    #bree-dad-opter


            if self.da.access_token:
                self.shop = Shop(self.da, self.cnx, self.cursor)
                self.transfer = Transfer(self.da, self.cnx, self.cursor)
                self.fountain = Fountain(self.da, self.cnx, self.cursor)
                print("The access token {}.".format(self.da.access_token))
                print("The refresh token {}.".format(self.da.refresh_token))
                temp_comments = None
                while True:
                    if(self.server.is_active == False):
                        self.reconnectSSH()
                    try:
                        comments = self.da.get_comments(endpoint='deviation', deviationid='99085360-CEEE-BA80-91AF-7B2EE2F19D3F')
                        comments = comments['thread']
                        if(temp_comments != comments):
                            for i in range(len(comments)):
                                if(comments[i].replies == 0):
                                    sql = ("SELECT balance FROM users WHERE username='" + comments[i].user.username + "'")
                                    self.cursor.execute(sql)
                                    if (self.cursor.rowcount == 0):
                                        sql = ("SELECT username FROM users ORDER BY user_id ASC")
                                        self.cursor.execute(sql)
                                        for username in self.cursor:
                                            try:
                                                user = self.da.get_user(username=username[0])
                                            except DeviantartError:
                                                user = ""
                                            if(user != "" and user != None):
                                                if(str(user.username) == str(comments[i].user.username)):
                                                    sql = ("UPDATE users SET username='"+str(str(comments[i].user.username))+"' WHERE username='"+str(username[0])+"'")
                                                    self.cursor.execute(sql)
                                                    sql = ("UPDATE inventory SET owner='"+str(comments[i].user.username)+"' WHERE owner='"+str(username[0])+"'")
                                                    self.cursor.execute(sql)
                                                    sql = ("UPDATE transaction SET username='"+str(comments[i].user.username)+"' WHERE username='"+str(username[0])+"'")
                                                    self.cursor.execute(sql)
                                                    sql = ("UPDATE inventorylog SET username='" + str(comments[i].user.username) + "' WHERE username='" +str(username[0]) + "'")
                                                    self.cursor.execute(sql)
                                                    sql = ("SELECT id FROM transfers WHERE from='" + str(username[0]) + "'")
                                                    self.cursor.execute(sql)
                                                    for id in self.cursor:
                                                        sql = ("UPDATE transfers SET from='"+str(comments[i].user.username)+"' WHERE id='"+str(id[0])+"'")
                                                        self.cursor.execute(sql)
                                                    sql = ("SELECT id FROM transfers WHERE to='" + str(username[0]) + "'")
                                                    self.cursor.execute(sql)
                                                    for id in self.cursor:
                                                        sql = ("UPDATE transfers SET to='"+str(comments[i].user.username)+"' WHERE id='"+str(id[0])+"'")
                                                        self.cursor.execute(sql)
                                                    break
                                        sql = ("SELECT username FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                        self.cursor.execute(sql)
                                        if(self.cursor.rowcount == 0):
                                            sql = ("INSERT INTO users (username, balance) VALUES ('" + str(comments[i].user.username) + "', '0')")
                                            self.cursor.execute(sql)
                        if (self.server.is_active == False):
                            self.reconnectSSH()
                            self.fountain.message()
                            self.transfer.message()
                            if (temp_comments != comments):
                                self.shop.message_buy(comments=comments)
                                self.shop.message_sell(comments=comments)
                                temp_comments = comments
                        else:
                            self.fountain.message()
                            self.transfer.message()
                            if(temp_comments != comments):
                                self.shop.message_buy(comments=comments)
                                self.shop.message_sell(comments=comments)
                                temp_comments = comments
                        time.sleep(45)
                    except DeviantartError as e:
                        print(e.message)
                        time.sleep(60)
                        self.da.auth(refresh_token=self.da.refresh_token)

        self.cursor.close()
        self.cnx.close()



    def reconnectSSH(self):
        self.server = SSHTunnelForwarder(('212.117.189.3', 22), ssh_pkey='id_rsa', ssh_private_key_password='LA66atituf',
                                ssh_password='O0qa726dwG', ssh_username='torimori',
                                remote_bind_address=('localhost', 3306))
        self.cnx = mysql.connector.connect(user='torimori_info', password='LA66atituf', host='localhost',
                                  port=self.server.local_bind_port, database='torimori_info')
        self.cursor = self.cnx.cursor(buffered=True)
        self.shop = Shop(self.da, self.cnx, self.cursor)
        self.transfer = Transfer(self.da, self.cnx, self.cursor)
        self.fountain = Fountain(self.da, self.cnx, self.cursor)


Main()