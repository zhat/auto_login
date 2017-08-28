# coding:utf8
''''' 
日报 
'''
import datetime
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class MyEmail:
    def __init__(self):
        self.user = None
        self.passwd = None
        self.to_list = []
        self.cc_list = []
        self.tag = None
        self.doc = None

    def send(self):
        ''''' 
        发送邮件 
        '''
        try:
            server = smtplib.SMTP_SSL("smtp.exmail.qq.com", port=465)
            server.login(self.user, self.passwd)
            server.sendmail("<%s>" % self.user, self.to_list + self.cc_list, self.get_attach())
            server.close()
            print("send email successful")
        except Exception as e:
            print("send email failed")
            print(e)


    def get_attach(self):
        ''''' 
        构造邮件内容 
        '''
        attach = MIMEMultipart()
        # 添加邮件内容
        txt = MIMEText("Send Mail Test")
        attach.attach(txt)
        if self.tag is not None:
            # 主题,最上面的一行
            attach["Subject"] = self.tag
        if self.user is not None:
            # 显示在发件人
            attach["From"] = "BI Department <%s>" % self.user
        if self.to_list:
            # 收件人列表
            attach["To"] = ";".join(self.to_list)
        if self.cc_list:
            # 抄送列表
            attach["Cc"] = ";".join(self.cc_list)
        if self.doc:
            # 估计任何文件都可以用base64，比如rar等
            # 文件名汉字用gbk编码代替
            name = os.path.basename(self.doc).encode("gbk")
            f = open(self.doc, "rb")
            doc = MIMEText(f.read(), "base64", "gb2312")
            doc["Content-Type"] = 'application/octet-stream'
            doc["Content-Disposition"] = 'attachment; filename="' + name + '"'
            attach.attach(doc)
            f.close()
        return attach.as_string()


if __name__ == "__main__":
    my = MyEmail()

    my.user = "yangzhixiang@ledbrighter.com"
    my.passwd = "Yzx5131425fzq"
    my.to_list = ["yangzhixiang@ledbrighter.com", ]
    # my.cc_list = ["yangzhixiang@ledbrighter.com"]
    my.tag = "Amazon Auto Login System"
    now_time = datetime.datetime.now()
    yes_time = now_time + datetime.timedelta(days=-1)
    yes_time_nyr = yes_time.strftime('%Y-%m-%d')
    # my.doc = u"/home/xxxx/data/toutiao_data/toutiao_day/toutiao." + yes_time_nyr + ".csv"
    my.send()  