# -*-coding: utf-8 -*-
import easygui as g
import pandas as pd
import pymysql
import uuid
import sys
import logging
import os, re
from datetime import datetime
import getpass

DATABASE = {
            'host':"192.168.2.23",
            'database':"leamazon",
            'user':"ama_account",
            'password':"T89ZY#UQWS",
            'port':3306,
            'charset':'utf8'
}

logging.basicConfig(level = logging.INFO,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %Y-%m-%d %H:%M:%S',
                filename='AmazonAutoLoginUserCheck.log',
                filemode='a+')

_LOGGING = logging.getLogger('AmazonAutoLoginUserCheck.py')

class UserLoginCheck():

    def __init__(self, tryNum=5):
        _LOGGING.info("UserLoginCheck init...")
        self.tryNum = tryNum
        self.dbconn = pymysql.connect(**DATABASE)
        self.cur = self.dbconn.cursor()

        self.login_username = ''
        # get host_name
        self.sys_username = getpass.getuser()

        _LOGGING.info("self.sys_username: " + self.sys_username)

        # login result
        self.login_result = False
        self.login_id = 0
        self.contact_info = "！！！\n\n\n有疑问请邮箱联系管理员杨志祥(yangzhixiang@ledbrighter.com)！！！"

        self.msg = "请输入用户名和密码"
        self.title = "欢迎使用后台自动登录系统"
        self.fieldNames = ["用户名", "密码"]
        self.fieldValues = []
        self.login_id_list = []

        # step 1 : check mac
        self.mac = self.getMacAddress()

        # get or generate log table
        self.log_table_name = "amz_auto_login_log"

        errorMsg = self.checkMacInfo(self.mac)
        if errorMsg == "":
            # log into db
            self.log_to_db(self.sys_username, self.mac, 'checkMac', 'success', '')
            self.fieldValues = g.multpasswordbox(self.msg, self.title, self.fieldNames)
            if self.fieldValues is None:
                # log into db
                self.log_to_db(self.sys_username, self.mac, 'check user info', 'failed_8', 'no username or password inputed')
                sys.exit(0)
        else:
            # log into db
            self.log_to_db(self.sys_username, self.mac, 'checkMac', 'failed_5', errorMsg)
            self.fieldValues = g.msgbox(msg=errorMsg, title=self.title, ok_button="再见")
            close_attr(self, 'cur')
            close_attr(self, 'dbconn')
            sys.exit(0)

    def __del__(self):
        close_attr(self, 'cur')
        close_attr(self, 'dbconn')

    def login(self):
        _LOGGING.info("login ...")
        i = 0
        while True:
            if i == self.tryNum-1:
                errmsg = "您已经输错【%s】次用户名或密码" % self.tryNum + self.contact_info
                self.fieldValues = g.msgbox(msg=errmsg, title=self.title, ok_button="再见")
                # log into db
                self.log_to_db(self.sys_username, self.mac, 'checkUserinfo', 'failed_6', errmsg)
                break

            username = self.fieldValues[0]
            password = self.fieldValues[1]
            errmsg = self.checkLoginInfo(username, password)

            self.login_username = username

            if self.login_result == True:
                break
            if errmsg == "":
                self.login_result = True
                # log into db
                self.log_to_db(self.sys_username, mac, 'checkUserinfo', 'success', errmsg)
                self.fieldValues = g.msgbox(msg=errmsg, title=self.title, ok_button="再见")
                break
            self.fieldValues = g.multpasswordbox(errmsg, self.title, self.fieldNames, self.fieldValues)
            i = i + 1
        _LOGGING.info("程序正在运行，请勿关闭此窗口！！！")

    def log_to_db(self, host_name, mac, action, status, msg):
        create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_sql1 = 'insert into %s' % self.log_table_name
        log_sql = log_sql1 + '(user_name, mac, action, status, msg, create_date) values(%s, %s, %s, %s, %s, %s)'
        self.cur.execute(log_sql, (host_name, mac, action, status, msg, create_time))
        self.dbconn.commit()

    def getMacAddress(self):
        _LOGGING.info("getMacAddress ...")
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return "-".join([mac[e:e + 2] for e in range(0, 11, 2)])

    # 获取计算机MAC地址和IP地址
    def getlocalmac(self):
        cmd = "ipconfig /all"
        result = self.execcmd(cmd)
        pat1 = "物理地址[\. ]+: ([\w-]+)"
        pat2 = "IPv4 地址[\. ]+: ([\.\d]+)"
        MAC = re.findall(pat1, result)[0]  # 找到MAC
        IP = re.findall(pat2, result)[0]  # 找到IP
        return MAC

    # execute command, and return the output
    def execcmd(self, cmd):
        r = os.popen(cmd)
        text = r.read()
        r.close()
        return text

    def checkLoginInfo(self, username, password):
        _LOGGING.info("checkLoginInfo ...")
        # step 2 : check status and mac
        sqlcmd = "select status, mac_localhost, login_id from amazon_auto_login_users a " \
                   "where username = " + "'" + username + "' and AES_DECRYPT(password_encrypt,'andy') = " + "'" + password + "' ;"
        login_result = pd.read_sql(sqlcmd, self.dbconn)

        if len(login_result>0):
            status = login_result["status"][0]
            mac_localhost1 = login_result["mac_localhost"][0].upper()
            mac_localhost2 = self.getMacAddress().upper()
        else:
            return "用户名或密码错误" + self.contact_info

        if status == 1 and mac_localhost1 == mac_localhost2:
            # self.login_id = login_result["login_id"][0]
            self.login_result = True

            self.fieldValues = g.msgbox(msg="您已通过验证！！！\n\n\n\n\n请点击“继续”按钮选择站点登录！！！", title=self.title,
                                        ok_button="继续")

            zone_dict = self.getzonedict(mac_localhost2)
            reply = g.choicebox(msg="请选择你要登录的站点，默认为选择第一个站点！！！", title=self.title, choices=zone_dict.keys())
            if reply:
                self.login_id = zone_dict[reply]
            else:
                self.login_id = zone_dict[0]
            return ""

        elif mac_localhost1 != mac_localhost2:
            return "您未授权在本机登录amazon后台" + self.contact_info
        elif status == 0:
            return "您的帐号登录权限已被收回" + self.contact_info

    def checkMacInfo(self, mac):
        _LOGGING.info("checkMacInfo ...")
        sqlcmd = "select max(status) as status from amazon_auto_login_users a " \
                   "where upper(mac_localhost) = " + "upper('" + mac + "') ;"
        mac_result = pd.read_sql(sqlcmd, self.dbconn)

        if mac_result["status"][0]:
            status = mac_result["status"][0]
        else:
            status = ""

        if status == "" :
            return "本机未授权登录amazon后台" + self.contact_info
        elif status == 0:
            return "本机登录权限已被收回" + self.contact_info
        else:
            return ""

    def getzonedict(self, mac):
        _LOGGING.info("getzonedict ...")
        sqlcmd = "select zone,login_id from amazon_auto_login_users a " \
                 "where upper(mac_localhost) = " + "upper('" + mac + "') and status = 1;"
        zone_result = pd.read_sql(sqlcmd, self.dbconn)
        return dict(zip(zone_result["zone"], zone_result["login_id"]))

def close_attr(object_target, attr):
    try:
        if hasattr(object_target, attr):
            getattr(object_target, attr).close()
    except Exception as e:
        _LOGGING.info("close attr %s failed_7..." % attr)

if __name__ == '__main__':
    uc = UserLoginCheck(2)
    # uc.login()
    # print(uc.getlocalmac())
    mac = uc.getMacAddress()
    # print(mac)
    # print("-----------------------------------------------------------")
    # print(uc.login_result)
    # print(uc.login_id)
    # print(type(uc.login_id))
    # print("-----------------------------------------------------------")
