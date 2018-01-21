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
with SSHTunnelForwarder(('212.117.189.3', 22), ssh_pkey='id_rsa', ssh_private_key_password='LA66atituf',
                        ssh_password='O0qa726dwG', ssh_username='torimori',
                        remote_bind_address=('localhost', 3306)) as server:
    cnx = mysql.connector.connect(user='torimori_info', password='LA66atituf', host='localhost',
                                  port=server.local_bind_port, database='torimori_info')
    cursor = cnx.cursor(buffered=True)
    da = deviantart.Api("7458", "98cdea34f4c07825335f32870d6f73b6", redirect_uri="http://last2424.ru/answer.php", standard_grant_type="authorization_code")
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
        shop = Shop(da, cnx, cursor)
        transfer = Transfer(da, cnx, cursor)
        fountain = Fountain(da, cnx, cursor)
        print("The access token {}.".format(da.access_token))
        print("The refresh token {}.".format(da.refresh_token))
        temp_comments = None
        while True:
            try:
                comments = da.get_comments(endpoint='deviation', deviationid='99085360-CEEE-BA80-91AF-7B2EE2F19D3F')
                comments = comments['thread']
                if(temp_comments != comments):
                    for i in range(len(comments)):
                        if(comments[i].replies == 0):
                            sql = ("SELECT balance FROM users WHERE username='" + comments[i].user.username + "'")
                            cursor.execute(sql)
                            if (cursor.rowcount == 0):
                                sql = ("SELECT username FROM users ORDER BY user_id ASC")
                                cursor.execute(sql)
                                for username in cursor:
                                    try:
                                        user = da.get_user(username=username[0])
                                    except DeviantartError:
                                        user = ""
                                    if(user != "" and user != None):
                                        if(str(user.username) == str(comments[i].user.username)):
                                            sql = ("UPDATE users SET username='"+str(str(comments[i].user.username))+"' WHERE username='"+str(username[0])+"'")
                                            cursor.execute(sql)
                                            sql = ("UPDATE inventory SET owner='"+str(comments[i].user.username)+"' WHERE owner='"+str(username[0])+"'")
                                            cursor.execute(sql)
                                            sql = ("UPDATE transaction SET username='"+str(comments[i].user.username)+"' WHERE username='"+str(username[0])+"'")
                                            cursor.execute(sql)
                                            sql = ("UPDATE inventorylog SET username='" + str(comments[i].user.username) + "' WHERE username='" +str(username[0]) + "'")
                                            cursor.execute(sql)
                                            sql = ("SELECT id FROM transfers WHERE from='" + str(username[0]) + "'")
                                            cursor.execute(sql)
                                            for id in cursor:
                                                sql = ("UPDATE transfers SET from='"+str(comments[i].user.username)+"' WHERE id='"+str(id[0])+"'")
                                                cursor.execute(sql)
                                            sql = ("SELECT id FROM transfers WHERE to='" + str(username[0]) + "'")
                                            cursor.execute(sql)
                                            for id in cursor:
                                                sql = ("UPDATE transfers SET to='"+str(comments[i].user.username)+"' WHERE id='"+str(id[0])+"'")
                                                cursor.execute(sql)
                                            break
                                sql = ("SELECT username FROM users WHERE username='" + str(comments[i].user.username) + "'")
                                cursor.execute(sql)
                                if(cursor.rowcount == 0):
                                    sql = ("INSERT INTO users (username, balance) VALUES ('" + str(comments[i].user.username) + "', '0')")
                                    cursor.execute(sql)
                fountain.message()
                transfer.message()
                if(temp_comments != comments):
                    shop.message_buy(comments=comments)
                    shop.message_sell(comments=comments)
                    temp_comments = comments
                    time.sleep(45)
            except DeviantartError as e:
                    print(e.message)
                    time.sleep(60)
                    da.auth(refresh_token=da.refresh_token)

    cursor.close()
    cnx.close()