from django.shortcuts import render
import mysql.connector
from .scheduler import scheduler
import feedparser
from datetime import datetime
from django.views import View

"""==================================================="""
import sys
from time import sleep
from selenium.webdriver.common.by import By
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
browser = webdriver.Chrome(options=options)


# Create your views here.
mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="phongquoc",
        database="nckh"
    )
cursor = mydb.cursor()

#global var
default = 10000
#import config from db
query1= "SET SQL_SAFE_UPDATES = 0;"
cursor.execute(query1)
query = """SELECT `time` FROM `setting`;"""
cursor.execute(query)
x = cursor.fetchall()
for row in x:
   default = int(row[0])

def auto_del_dup():
    auto = """delete t1 FROM web t1 INNER  JOIN web t2 WHERE t1.id > t2.id  AND t1.title = t2.title AND t1.link = t2.link AND t1.published = t2.published;"""
    cursor.execute(auto)
    mydb.commit()
    print("Task del running")

scheduler.add_job(auto_del_dup, 'interval', seconds=60*300)

class JobScheduler:
    jobs = {}

    @classmethod
    def add_job(cls, url, interval):
        job = scheduler.add_job(cls.job_function, 'interval', seconds=interval, args=[url])
        cls.jobs[url] = job

    @classmethod
    def remove_job(cls, url):
        if url in cls.jobs:
            job = cls.jobs.pop(url)
            job.remove()

    @staticmethod
    def job_function(url):
        feed = feedparser.parse(url)
        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")
        print("Current Time =", current_time)
        feed = feedparser.parse('http://www.zone-h.org/rss/specialdefacements')
        sql = """INSERT INTO web(title, link, published) VALUES (%(title)s, %(link)s, %(published)s)"""

        for entry in feed.entries:
            data = {
                'title': entry.title,
                'link' : entry.link,
                'published' : entry.published,
            }
            cursor.execute(sql, data)
            mydb.commit()
        print('task is running')


JobScheduler.add_job('http://www.zone-h.org/rss/specialdefacements', interval=default)

def archive():
    browser.get("http://www.zone-h.org/archive?hz=1")

    for i in range(2, 27):
        a = '#ldeface > tbody > tr:nth-child(' + str(i) +') > td:nth-child(8)'
        test = browser.find_element(By.CSS_SELECTOR, a)
        string = test.text
        string_after = string.split("/")
        link1= string_after[0]
        link_final = re.findall(".com$", link1)
        if link_final:
            print(link1)
    browser.close()

scheduler.add_job(archive, 'interval', seconds=30)


scheduler.start()

def config(request):
    global default
    config = default

    if request.method == "POST":
        config = request.POST["config"]
        default = int(config)
        test = int(config)
        timesql = "UPDATE `setting` SET time=" + str(config) + " WHERE name='admin';"
        cursor.execute(timesql)
        JobScheduler.remove_job('http://www.zone-h.org/rss/specialdefacements')
        JobScheduler.add_job('http://www.zone-h.org/rss/specialdefacements', test)


    mydb.commit()
    return render(request, 'function/config.html',{'context': default})


def feed_view(request):
    feed = feedparser.parse('http://www.zone-h.org/rss/specialdefacements')
    entries = []
    for entry in feed.entries:
        entries.append({
            'title' : entry.title,
            'link' : entry.link,
            'published' : entry.published
        })
    context = {'data' : entries}
    return render(request, 'function/feed.html', context)

def feed_search(request):
    if request.method == "POST":
        searched = request.POST["searched"]
        sql = " SELECT * FROM WEB WHERE title REGEXP" + " '^" + searched + "';"
        print(sql)
        cursor.execute(sql)
        result = cursor.fetchall()
        return render(request, 'function/search.html',{'result':result})
    else:
        return render(request, 'function/search.html',{})

def list(request):
    auto = """delete t1 FROM web t1 INNER  JOIN web t2 WHERE t1.id > t2.id  AND t1.title = t2.title AND t1.link = t2.link AND t1.published = t2.published;"""
    cursor.execute(auto)
    list = " SELECT * FROM WEB;"
    cursor.execute(list)
    result = cursor.fetchall()
    mydb.commit()
    return render(request, 'function/list.html',{'result': result})
