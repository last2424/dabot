import deviantart, re, mysql.connector, requests, traceback
from Shop import Shop
from deviantart.user import User
from Transfer import Transfer
from deviantart.api import DeviantartError
from mysql.connector.errors import InterfaceError
from datetime import datetime, date, time
from fountain import Fountain
import time
from sshtunnel import SSHTunnelForwarder
#cnx = None
class Main:
    def reconnect(self):
        self.server = SSHTunnelForwarder(('212.117.189.3', 22), ssh_pkey='id_rsa', ssh_private_key_password='LA66atituf', ssh_password='O0qa726dwG', ssh_username='torimori', remote_bind_address=('localhost', 3306))
        self.server.start()
        self.cnx = mysql.connector.connect(user='torimori_info', password='LA66atituf', host='localhost', port=self.server.local_bind_port, database='torimori_info')
        self.cursor = self.cnx.cursor(buffered=True)

    def __init__(self):
        with SSHTunnelForwarder(('212.117.189.3', 22), ssh_pkey='id_rsa', ssh_private_key_password='LA66atituf',
                                ssh_password='O0qa726dwG', ssh_username='torimori',
                                remote_bind_address=('localhost', 3306)) as self.server:
            self.cnx = mysql.connector.connect(user='torimori_info', password='LA66atituf', host='localhost',
                                    port=self.server.local_bind_port, database='torimori_info')
            self.cursor = self.cnx.cursor(buffered=True)
            da = deviantart.Api("7771", "c8ec5442fe785741b2e5cbad0a7391a9", redirect_uri="https://torimori.info/answer.php", standard_grant_type="authorization_code")
            #create new client with the authorization code grant type
            #The authorization URI: redirect your users to this
            auth_uri = da.auth_uri

            print ("Please authorize app: {}".format(auth_uri))

            #Enter the value of the code parameter, found in to which DeviantArt redirected to
            code = input("Enter code:")

            #Try to authenticate with the given code
            try:
                da.auth(code=code)
            except deviantart.api.DeviantartError as e:
                print ("Couldn't authorize user. Error: {}".format(e))

            #If authenticated and access_token present
            #bree-dad-opter


            if da.access_token:
                shop = Shop(da, self.cnx, self.cursor)
                transfer = Transfer(da, self.cnx, self.cursor)
                fountain = Fountain(da, self.cnx, self.cursor)
                print("The access token {}.".format(da.access_token))
                print("The refresh token {}.".format(da.refresh_token))
                temp_comments = None
                while True:
                    try:
                        comments = da.get_comments(endpoint='deviation', deviationid='B147125B-6E0B-D409-9D20-04F55F5BF453', limit=25)
                        time.sleep(2)
                        comments = comments['thread']
                        if(temp_comments != comments):
                            for i in range(len(comments)):
                                if(comments[i].replies == 0 and comments[i].hidden == None):
                                    sql = ("SELECT balance FROM users WHERE username='" + comments[i].user.username + "'")
                                    self.cursor.execute(sql)
                                    if (self.cursor.rowcount == 0):
                                        sql = ("SELECT username FROM users ORDER BY user_id ASC")
                                        self.cursor.execute(sql)
                                        for username in self.cursor:
                                            try:
                                                user = da.get_user(username=username[0])
                                                time.sleep(2)
                                            except DeviantartError:
                                                user = ""
                                            if(user != "" and user != None):
                                                if(str(user) == str(comments[i].user.username)):
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
                                        sql = ("SELECT balance FROM users WHERE username='" + comments[i].user.username + "'")
                                        self.cursor.execute(sql)
                                        if (self.cursor.rowcount == 0):
                                            sql = ("INSERT INTO users (username, balance) VALUES ('" + str(comments[i].user.username) + "', '0')")
                                            self.cursor.execute(sql)
                        if(temp_comments != comments):
                            if (self.server.is_active == True):
                                shop.message_buy(comments=comments)
                                shop.message_sell(comments=comments)
                            else:
                                reconnect()
                            temp_comments = comments
                        if(self.server.is_active == True):
                            fountain.message()
                        else:
                            reconnect()
                        if (self.server.is_active == True):
                            transfer.message()
                        else:
                            reconnect()
                        time.sleep(45)
                    except DeviantartError as e:
                            print(e.message)
                            print(traceback.format_exc())
                            da.auth(refresh_token=da.refresh_token)
                            time.sleep(120)

                    except InterfaceError:
                        reconnect()

            self.cursor.close()
            self.cnx.close()


Main()