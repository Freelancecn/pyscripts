#! /usr/bin/env python3
# -*- coding:utf-8 -*-

import re
import click
import os,sys
import sqlite3
import ssl,socket
import time
from pprint import pprint
from datetime import datetime

DB = 'domain.db'
SEND_EMAIL = 'youremail@domain'
PASSWORD = 'password'
RECEIVE_EMAIL = '1001@qq.com'
SMTP_SERVER = 'smtp.qq.com'
ALERT_DAYS = 3

def create_domain_table():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE DOMAIN
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time TEXT,
            domain TEXT UNIQUE,
            s_time TEXT,
            e_time TEXT,
            remain DATE );''')
    conn.commit()
    c.close()
    conn.close()

def insert_domain_table(sslinfo):
    if sslinfo:
        conn = sqlite3.connect(DB)
        conn.text_factory = str
        c = conn.cursor()
        check_time = sslinfo['check_time']
        domain = sslinfo['domain']
        s_time = sslinfo['s_time']
        e_time = sslinfo['e_time']
        remain = sslinfo['remain']
        c.execute("REPLACE INTO DOMAIN (check_time,domain,s_time,e_time,remain) VALUES(?,?,?,?,?);",(check_time,domain,s_time,e_time,remain))
        conn.commit()
        c.close()
        conn.close()
        print("insert ssl information for {}".format(domain))

def is_domain(domain):
    is_domain = False
    regex = r'(^[0-9a-zA-Z][0-9a-zA-Z_]+)\.([a-zA-Z]+)'
    is_domain = bool(re.match(regex,str(domain)))
    if not is_domain:
        print("{} is not a domain".format(domain))
    return is_domain


def get_ssl_info(domain):
    server_name = domain
    print("get ssl information for {}".format(domain))
    sslinfo = {}

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_default_certs()

    s = socket.socket()
    s.settimeout(5)
    s = context.wrap_socket(s,server_hostname=server_name)
    try:
        s.connect((server_name,443))
        s.do_handshake()
        cert = s.getpeercert()

        e_time = ssl.cert_time_to_seconds(cert['notAfter'])
        remain = e_time
        e_time = datetime.utcfromtimestamp(e_time)

        s_time = ssl.cert_time_to_seconds(cert['notBefore'])
        s_time = datetime.utcfromtimestamp(s_time)

        check_time = datetime.utcnow()

        sslinfo['check_time'] = str(check_time)
        sslinfo['domain'] = server_name
        sslinfo['s_time'] = str(s_time)
        sslinfo['e_time'] = str(e_time)
        sslinfo['remain'] = remain

        return sslinfo
    except socket.timeout:
        print("TimeOut")

def add_from_file(file):
    with open(file,'r') as f:
        for i in f.readlines():
            if is_domain(i):
                sslinfo = get_ssl_info(i.strip())
                insert_domain_table(sslinfo)

@click.command("add",short_help="add domain")
@click.option("--file","-f",type=click.Path(),default=None)
@click.argument("domain",required=False)
def add_domain(domain,file):
    if not os.path.isfile(DB):
        create_domain_table()
    if file:
        add_from_file(file)
    else:
        sslinfo = get_ssl_info(domain)
        insert_domain_table(sslinfo)

@click.command("del",short_help="delete domain")
@click.argument("domain")
def del_domain(domain):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('delete from DOMAIN where domain=?;',(domain,))
    conn.commit()
    c.close()
    conn.close()


@click.command("query",short_help="query domain")
@click.argument("domain",required=False)
def get_domain_info(domain):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if domain:
        domainInfo = c.execute('select * from DOMAIN where domain=?;',(domain,))
        domainInfo = domainInfo.fetchone()
    else:
        domainInfo = c.execute('select * from DOMAIN')
        domainInfo = domainInfo.fetchall()

    c.close()
    conn.close()
    pprint(domainInfo)


@click.command("output",short_help="output the ssl status to /path/to/name.html")
@click.argument("htmlfile",type=click.File('w'),default="sslstatus.html")
def generation_html_file(htmlfile):
    html = [
           ' <!DOCTYPE html>',
           ' <html>',
           ' <head>',
           ' <meta charset="utf-8">',
           ' <meta http-equiv="X-UA-Compatible" content="IE=edge">',
           ' <title>SSL Status</title>',
           ' <meta name="description" content="SSL Status">',
           ' <meta name="viewport" content="width=device-width, initial-scale=1">',
           ' <style>',
           ' body { -webkit-font-smoothing: antialiased; min-height: 100vh; display: flex; flex-direction: column; } *, *:after, *:before { box-sizing: border-box; } * { margin: 0; padding: 0; } a { text-decoration-style: none; text-decoration: none; color: inherit; cursor: pointer; } p { font-size: 16px; line-height: 1.5; font-weight: 400; color: #5A5B68; } p.small { font-size: 15px; } p.tiny { font-size: 14px; } .tiny { font-size: 14px; } .section { margin-left: auto; margin-right: auto; display: flex; flex-direction: column; max-width: 1342px; /*56 + 1230 + 56*/ padding-left: 8px; padding-right: 8px; left: 0; right: 0; width: 100%; } .container { display: flex; flex-direction: column; align-items: center; } .flex_column { display: flex; flex-direction: column; } .justify_content_center { justify-content: center; } h1 { font-size: 48px; letter-spacing: -1px; line-height: 1.2; font-weight: 700; color: #323648; } .header { display: flex; flex-direction: row; justify-content: space-between; align-items: center; } .width_100 { width: 100%; } .align_center { align-items: center; } .text_center { text-align: center; } .raven_gray { color: #5A5B68; } .black_licorice { color: #323648; } .bg_lighter_gray { background-color: #F5F5F5; } .bg_white { background-color: white; } .semi_bold { font-weight: 700; } .underline { text-decoration: underline; } #services_legend .header { background-color: #F5F5F5; padding-left: 20px; padding-right: 20px; height: 44px; border-left: 1px solid #E8E8E8; border-right: 1px solid #E8E8E8; border-top: 1px solid #E8E8E8; justify-content: center; } @media (min-width: 768px) { #services_legend .header { flex-wrap: wrap; justify-content: space-between; align-content: center; height: 74px; } } @media (min-width: 1072px) { #services_legend .header { height: 56px; } } #services { margin-bottom: 56px; border-style: solid; border-color: #E8E8E8; border-width: 1px 0 0 1px; display: flex; flex-direction: row; flex-wrap: wrap; } #services .service { padding: 20px; border-style: solid; border-color: #E8E8E8; border-width: 0 1px 1px 0; width: 100%; } @media (min-width: 1072px) { #services .service { width: 50%; } } @media (max-width: 767px) { h1 { font-size: 28px; } } @media (min-width: 768px) { .section { padding-left: 56px; padding-right: 56px; } } /* CALENDAR START */ /* CALENDAR END */ /* CALENDAR TOOLTIPS START */ /* CALENDAR TOOLTIPS END */ /* DAY INCIDENTS START */ /* DAY INCIDENTS END */ /* INCIDENT START */ /* INCIDENT END */ /* FOOTER START */ .footer { display: flex; flex-direction: column; flex-wrap: wrap; justify-content: center; align-items: center; height: 200px; } .footer p { text-align: center; } .footer > .info { order: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; } .footer .sub_info { display: flex; flex-direction: column; align-items: center; } .footer > .links { display: flex; flex-direction: row; justify-content: space-between; align-items: center; order: 2; width: 250px; margin-top: 25px; } @media (min-width: 768px) { .footer { height: 112px; } .footer > .links { margin-top: 20px; } .footer .sub_info { flex-direction: row; } } @media (min-width: 1072px) { .footer { height: 90px; align-items: stretch; } .footer > .links { flex-basis: 60%; order: 1; margin-top: 0; } .footer > .info { align-items: flex-end; flex-basis: 50%; order: 2; } /* FOOTER END */ }',
           ' </style>',
           ' </head>',
           ' <body class="bg_lighter_gray">',
           ' <div class="bg_white width_100">',
           ' <div class="container">',
           ' <h1 class="black_licorice text_center width_100">SSL status</h1>',
           ' </div>',
           ' <div id="services_legend" class="section justify_content_center">',
           ' <div class="header">',
           ' <p class="title semi_bold black_licorice">Sites SSL Status</p>',
           ' </div>',
           ' </div>',
           ' <div class="section">',
           ' <div id="services">',
           ]
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('select * from DOMAIN')
    domain = c.fetchall()
    c.close()
    conn.close()
    for i in domain:
        remain = i[5] - time.time()
        remain = round(remain/86400)
        html += [
                '<div class="service header align_center">',
                '<div class="flex_column">',
                '<p class="black_licorice semi_bold">' + i[2] + '</p>',
                '<p class="small raven_gray">last check:  ' + i[1] + '</p>',
                '<p class="small raven_gray">issue date:  ' + i[3] + '</p>',
                '<p class="small raven_gray">expire date: ' + i[4] + '</p>',
                '<p class="small raven_gray">remain:      ' + str(remain) + ' Days' + '</p>',
                '</div>',
                '</div>',
                ]
    html += [
            '</div>',
            '</div>',
            '</div>',
            '<div class="section">',
            '<div class="footer">',
            '<div class="info">',
            '<div class="sub_info">',
            '<p class="tiny"><a href="https://github.com/freelancecn" class="underline">github</a></p>',
            '</div>',
            '</div>',
            '<div class="links">',
            '<p class="semi_bold tiny">SSL Status</p>',
            '</div>',
            '</div>',
            '</div>',
            '</body>',
            '</html>',
            ]
    htmlfile.write('\n'.join(html))

def send_alert_email(msg,email):
    from email.mime.text import MIMEText

    import smtplib

    msg = MIMEText(msg,'plain','utf-8')
    msg['From'] = SEND_EMAIL
    msg['To'] = email
    msg['Subject'] = 'SSL Alert'

    server = smtplib.SMTP(SMTP_SERVER,587)
    server.starttls()
    server.login(SEND_EMAIL,PASSWORD)
    server.sendmail(SEND_EMAIL,[email],msg.as_string())
    server.quit()
    print("The email send to {}.".format(email))

@click.command("email",short_help="send alert email")
@click.argument("email",default=RECEIVE_EMAIL)
def get_expired_domain(email):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('select * from DOMAIN')
    domain = c.fetchall()
    c.close()
    conn.close()
    msg = ' '
    for i in domain:
        if i[5] < ALERT_DAYS:
            msg = msg + '    ' +i[2] + '    remain    ' + str(i[5]) + ' Days'
    if not msg:
        send_alert_email(msg,email)
    else:
        print("No Domain has been expired")



@click.group()
def main():
    pass

main.add_command(add_domain)
main.add_command(del_domain)
main.add_command(get_domain_info)
main.add_command(get_expired_domain)
main.add_command(generation_html_file)

if __name__ == '__main__':
    main()

