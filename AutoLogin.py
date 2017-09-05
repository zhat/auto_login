import uuid
import os
import sys
import time
from datetime import datetime
import platform
import pandas as pd
import pymysql
from selenium import webdriver  # selenium 需要自己安装此模块
from selenium.webdriver.support.ui import WebDriverWait
from AmazonAutoLoginUserCheck import UserLoginCheck
import logging
import easygui as g
from ctypes import windll
import getpass
import random

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
                filename='AmazonAutoLoginModule.log',
                filemode='a+')
_LOGGING = logging.getLogger('AutoLogin.py')
"""
Amazon后台自动登录程序
"""
# 获取当前路径
current_path = os.path.abspath('.')
"""
    自动登录程序  
"""
class AmazonAutoLogin():
    title = "欢迎使用后台自动登录系统"
    def __init__(self, tryNum, has_to_login):
        # generate db connection
        self.dbconn = pymysql.connect(**DATABASE)
        self.cur = self.dbconn.cursor()
        self.login_username = ''
        # 获取执行程序的用户
        self.sys_username = getpass.getuser()
        # 两个版本的Python处理方式不一致
        if platform.python_version().startswith('3'):
            self.sys_username = filter(str.isalpha, self.sys_username)
            self.sys_username = "".join(list(self.sys_username))
        elif platform.python_version().startswith('2'):
            self.sys_username = self.sys_username
        _LOGGING.info("self.sys_username: " + self.sys_username)
        if has_to_login:
            # 检查用户是否具有登录权限
            ulc = UserLoginCheck(tryNum)
            ulc.login()
            # 获取本机MAC地址
            self.mac = ulc.getMacAddress()
            # 获取admin用户名
            self.chrome_admin_user = self.get_chrome_admin_user()
            # 初始化日志记录表
            self.log_table_name = ulc.log_table_name
            # init log result
            self.log_result_flag = False
            _LOGGING.info("check user info ")
            # 获取站点列表
            self.login_id = ulc.login_id
            # 当前登录系统的用户名
            self.login_username = ulc.login_username
            # 初始化驱动
            self.driver = self.generateDriver()
    # 获取admin用户名
    def get_chrome_admin_user(self):
        sqlcmd = "select chrome_admin_user from amazon_auto_login_chrome_users a where department <> '开发本机' and mac = '" + self.mac.upper() + "';"
        a = pd.read_sql(sqlcmd, self.dbconn)
        if (len(a)> 0):
            print(a["chrome_admin_user"][0])
            return a["chrome_admin_user"][0]
    # 记录日志保存到数据库
    def log_to_db(self, host_name, mac, action, status, msg):
        create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_sql1 = 'insert into %s' % self.log_table_name
        log_sql = log_sql1 + '(user_name, mac, action, status, msg, create_date) values(%s, %s, %s, %s, %s, %s)'
        self.cur.execute(log_sql, (host_name, mac, action, status, msg, create_time))
        self.dbconn.commit()
    # 生成驱动，启动本地浏览器
    def generateDriver(self):
        _LOGGING.info("generateDriver start...")
        sqlcmd = "select username as un, AES_DECRYPT(password_encrypt,'andy') as pw, login_url as url from core_amazon_account a where id in (%s);"%self.login_id
        # print(sqlcmd)
        a = pd.read_sql(sqlcmd, self.dbconn)
        if (len(a) > 0):
            self.username = a["un"]
            self.password = a["pw"]
            self.url = a["url"]
        else:
            # have no url to login in this PC
            errmsg = 'have no url to login in this PC'
            # log into db
            self.log_to_db(self.sys_username, self.mac, 'getLoginUrls', 'failed_1', errmsg)
            close_attr(self, 'cur')
            close_attr(self, 'dbconn')
            sys.exit(0)
        _LOGGING.info("get the username and password ")
        # 获取驱动
        executable_path = current_path + os.path.sep + 'drive' + os.path.sep + 'chromedriver.exe'
        os.environ["webdriver.chrome.driver"] = executable_path
        # 不保存密码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile': {
                'password_manager_enabled': False
            }
        })
        # 读取本地信息
        # chrome_options.add_argument("--user-data-dir=" + r"C:\Users\%s\AppData\Local\Google\Chrome\User Data" % self.sys_username)
        chrome_options.add_argument(
            "--user-data-dir=" + r"C:\Users\%s\AppData\Local\Google\Chrome\User Data" % self.chrome_admin_user)

        _LOGGING.info("Chrome opening...")
        _LOGGING.info("executable_path= " + current_path + os.path.sep + 'drive' + os.path.sep + 'chromedriver.exe')
        # _LOGGING.info("--user-data-dir=" + r"C:\Users\%s\AppData\Local\Google\Chrome\User Data" % self.sys_username)
        _LOGGING.info("--user-data-dir=" + r"C:\Users\%s\AppData\Local\Google\Chrome\User Data" % self.chrome_admin_user)

        #driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        driver = webdriver.Chrome(chrome_options=chrome_options)
        return driver

    def login_str(self,):
        if self.driver.find_elements_by_id('merchant-picker-auth-status'):
            self.driver.find_elements_by_xpath(
                    "//*[@id='merchant-picker-auth-status']//input[@name='not_authorized_sso_action' and @value='DIFFERENT_USER']")[
                    0].click()
            self.driver.find_elements_by_xpath("//*[@id='merchant-link-btn-continue']/span/input")[0].click()
            time.sleep(10)
        password_str = ''
        if platform.python_version().startswith('3'):
            password_str = self.password[0].decode('utf-8')
        elif platform.python_version().startswith('2'):
            password_str = str(self.password[0]).encode('utf-8')
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_id("ap_email").clear()
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_id("ap_email").send_keys(self.username[0])
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_id("ap_password").send_keys(password_str)
        self.driver.implicitly_wait(10)
        self.driver.find_element_by_id("signInSubmit").click()
        WebDriverWait(self.driver, 120).until(
            lambda driver: driver.execute_script("return document.readyState") == 'complete')
    # 登录
    def login(self):
        _LOGGING.info("start login...")
        self.driver.maximize_window()
        # 禁用鼠标和键盘
        user32 = windll.LoadLibrary('user32.dll')
        user32.BlockInput(True)
        _LOGGING.info("block input start...")
        try:
            _LOGGING.info("open the window...")
            self.driver.get(self.url[0])
            time.sleep(1)
            WebDriverWait(self.driver, 120).until(
                    lambda driver: driver.execute_script("return document.readyState") == 'complete')
            if not self.driver.find_elements_by_id('gw-lefty'):
                self.login_str()
            _LOGGING.info("login successfully!")
            self.driver.maximize_window()
            # login successful
            self.log_result_flag = True
            errmsg = ''
            # log into db
            self.log_to_db(self.sys_username, self.mac, 'login...', 'success', errmsg)
            _LOGGING.info("monitoring, exit system when all windows closed")
            # exit system when all windows closed
            user32.BlockInput(False)
            while True:
                time.sleep(1)
                winhandles = self.driver.window_handles
                if len(winhandles) == 0:
                    self.deleteAll()
        except Exception as e:
            if self.log_result_flag:
                errmsg = str(e)
                _LOGGING.error(errmsg)
                # log into db
                self.log_to_db(self.sys_username, self.mac, 'Chrome closed', 'System exit', errmsg)
            else:
                errmsg = str(e)
                _LOGGING.error(errmsg)
                # log into db
                self.log_to_db(self.sys_username, self.mac, 'loginUrls', 'failed_2', errmsg)
            _LOGGING.error("--------------------------------error-------------------------")
            _LOGGING.error(e)
            _LOGGING.error("--------------------------------error-------------------------")
        finally:
            user32.BlockInput(False)
            self.deleteAll()
    def deleteAll(self):
        try:
            close_attr(self, 'cur')
            close_attr(self, 'dbconn')
            if hasattr(self, 'driver'):
                self.driver.quit()
            sys.exit(0)
        except Exception as e:
            _LOGGING.error("--------------------------------error-------------------------")
            _LOGGING.error(e)
            _LOGGING.error("--------------------------------error-------------------------")
            sys.exit(0)

"""
    关闭资源用
"""
def close_attr(object_target, attr):
    try:
        if hasattr(object_target, attr):
            getattr(object_target, attr).close()
    except Exception as e:
        _LOGGING.info("close attr %s failed_3..." % attr)
"""
    获取程序运行所在机器的MAC
"""
def getMacAddress():
    _LOGGING.info("getMacAddress...")
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return "-".join([mac[e:e + 2] for e in range(0, 11, 2)])

if __name__=='__main__':
    #try:
    _LOGGING.info("all start here...")
        # print("程序运行过程中，请勿关闭此窗口！！！")
        # 中文有点问题，用英文显示
    print("*" * 60)
    print("** Do not close this window while the program is running! **")
    print("*" * 60)
    time.sleep(1 + random.random() * 1)
    # 判断是否是以管理员身份运行程序，该判断方式为独创
    user32 = windll.LoadLibrary('user32.dll')
    admin_flag = user32.BlockInput(True)
    # 强制要求以管理员身份运行，管理员身份才能进行键盘和鼠标的锁定
    fieldValues = []
    if admin_flag == 0:
        user32.BlockInput(False)
        fieldValues = g.msgbox(msg="请“以管理员身份运行”该程序！！！", title="欢迎使用后台自动登录系统", ok_button="再见")
        sys.exit(0)
    user32.BlockInput(False)
    _LOGGING.info("auto login start......")
    # tryNum 是最多可以尝试输错密码的次数
    autoLogin = AmazonAutoLogin(tryNum=5, has_to_login=True)
    # 程序休眠时间
    autoLogin.login()