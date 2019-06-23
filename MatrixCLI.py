import json
import time
import requests
import argparse
import os
import getpass
import re
from datetime import datetime
import datetime as dt
from requests_toolbelt.multipart.encoder import MultipartEncoder


def strsp(min, max):
    while min < max:
        print(" ", end='')
        min += 1
    print("    ", end='')
    return

def invalidUser(user):
    print('Invalid user / Following user have no pic: ' + str(user))
    exit()

def disconnectedUser(username):
    print('Invalid or disconnected user: ' + username + '.\nYou can try to get the daily logtime of a disconnected user with the -d option')
    exit()

def classicPrint(host, user, maxlen):
    for i in range(0, len(host)):
        print(user[i], end='')
        strsp(len(user[i]), maxlen)
        print(host[i])

def userPrint(host, user, maxlen):
    user, host= zip(*sorted(zip(user, host)))
    classicPrint(host, user, maxlen)

def hostPrint(host, user, maxlen):
    host, user = zip(*sorted(zip(host, user)))
    classicPrint(host, user, maxlen)

def diff_times_in_seconds(t1, t2):
    # caveat emptor - assumes t1 & t2 are python times, on the same day and t2 is after t1
    h1, m1, s1 = t1.hour, t1.minute, t1.second
    h2, m2, s2 = t2.hour, t2.minute, t2.second
    t1_secs = s1 + 60 * (m1 + 60*h1)
    t2_secs = s2 + 60 * (m2 + 60*h2)
    return t2_secs - t1_secs

def getSec(t1):
    # caveat emptor - assumes t1 & t2 are python times, on the same day and t2 is after t1
    h1, m1, s1 = t1.hour, t1.minute, t1.second
    t1_secs = s1 + 60 * (m1 + 60*h1)
    return t1_secs

def printPic(username):
    username = username.lower()
    url = 'https://cdn.intra.42.fr/users/large_' + username + '.JPG'
    img = requests.get(url, stream=True)
    if img.status_code != 200:
        invalidUser(args.picture)
    multipart_data = MultipartEncoder(fields={
        'bilde': ('image.jpeg', img.content),
        'farger': '1',
        'bgcolor': 'Black',
        'fontface': 'Fixedsys',
        'fontsize': '+0',
        'supersmall': '0',
        'charkodek': ' .:coCO8@',
        'sendt': '1',
        'referer': 'https://www.google.fr/'
    })
    response = requests.post('http://lunatic.no/ol/img2aschtml.php', data=multipart_data,
                             headers={'Content-Type': multipart_data.content_type})
    image = re.sub(r'<SPAN ID=[a-z].>', '', response.text)
    image = re.sub(r'<SPAN ID=.>', '', image)
    image = re.sub(r'</SPAN>', '', image)
    image = re.sub(r'<SPAN.*>', '', image)
    image = re.sub(r'<!DOC[\s\S]*<PRE>', '', image)
    image = re.sub(r'<!--[\s\S]*>', '', image)
    image = re.sub(r'<span[\s\S]*</PRE>', '', image)
    file = open('/Users/' + getpass.getuser() + '/goinfre/image', 'w')
    file.write(image)
    file.close()
    os.system('/bin/cat ~/goinfre/image')

def getLastUptime(json_res):
    if not json_res[0]['end_at']:
        json_res[0]['end_at'] = time.strftime('%H:%M:%S')
    beginhour = str(json_res[0]['begin_at'])[11:19]
    beginhour_object = datetime.strptime(beginhour, '%H:%M:%S')
    endhour = time.strftime('%H:%M:%S')
    endhour_object = datetime.strptime(endhour, '%H:%M:%S')
    return str(dt.timedelta(seconds=(diff_times_in_seconds(beginhour_object, endhour_object))))


def displayUptime(username, data):
    username = username.lower()
    response = requests.post('https://api.intra.42.fr/oauth/token', data=data)
    token = response.text[17:81]
    req = "https://api.intra.42.fr/v2/users/" + username + "/locations?access_token=" + token
    json_res = json.loads(requests.get(req).text)
    if not json_res:
        disconnectedUser(username)
    if json_res[0] and json_res[0]['end_at']:
        disconnectedUser(username)
    else:
        print(username + '\'s uptime: ' + getLastUptime(json_res))

def displayLogtime(username, data, offset):
    username = username.lower()
    response = requests.post('https://api.intra.42.fr/oauth/token', data=data)
    token = response.text[17:81]
    req = "https://api.intra.42.fr/v2/users/" + username + "/locations?access_token=" + token
    json_res = json.loads(requests.get(req).text)
    if not json_res:
        disconnectedUser(username)
    if json_res[0] and json_res[0]['end_at']:
        disconnectedUser(username)
    else:
        if offset == 0: #Daily logtime
            today = time.strftime('%Y-%m-%d')
            secs = 0
            for cid in json_res:
                if cid['begin_at'][0:10] == today and cid['end_at']:
                    begin = datetime.strptime(cid['begin_at'][11:19], '%H:%M:%S')
                    end = datetime.strptime(cid['end_at'][11:19], '%H:%M:%S')
                    time_elapsed = diff_times_in_seconds(begin, end)
                    secs = secs + time_elapsed
            todaylog = str(dt.timedelta(seconds=(int(getSec(datetime.strptime(getLastUptime(json_res), '%H:%M:%S'))) + int(secs))))
            print(username + '\'s daily logtime: ' + str(todaylog))
        #elif offset == 1: #Weekly logtime
            #A FAIRE

def mainHandler(data):
    response = requests.post('https://api.intra.42.fr/oauth/token', data=data)
    token = response.text[17:81]
    user = []
    host = []
    maxlen = 0
    for i in range(1, args.loop):
        req = "https://api.intra.42.fr/v2/campus/9/locations?access_token=" + token + "&filter[active]=true&per_page=100&page=" + str(
            i)
        result = requests.get(req)
        json_res = json.loads(result.text)
        for entry in json_res:
            if entry['host'] != 'Magic World':
                user.append(entry['user']['login'])
                host.append(entry['host'])
            if len(entry['user']['login']) > maxlen:
                maxlen = len(entry['user']['login'])
        time.sleep(0.5)
    if args.uptime:
        displayUptime(args.uptime, data)
    elif args.daily:
        displayLogtime(args.daily, data, 0)
    elif args.user:
        userPrint(host, user, maxlen)
    elif args.host:
        hostPrint(host, user, maxlen)
    else:
        classicPrint(host, user, maxlen)


## PROGRAM START ##

# Parsing
parser = argparse.ArgumentParser()
parser.add_argument("-host", help="Sort results by hostname", action="store_true")
parser.add_argument("-up", "--uptime", help="Display user's uptime", type=str, metavar="[USER]")
parser.add_argument("-d", "--daily", help="Display user's daily logtime", type=str, metavar="[USER]")
parser.add_argument("-u", "--user", help="Sort results by login name", action="store_true")
parser.add_argument("-p", "--picture", help="Display ASCII-art picture of the user", type=str, metavar="[USER]")
parser.add_argument("-l", "--loop", help="Set the loops factor (Default is 5, meaning 5x100 max users per search). Decreasing this number may improve wait time", type=int, choices=range(1, 30), metavar="[1-30]", default=5)
args = parser.parse_args()

# API credentials
data = {
  'grant_type': 'client_credentials',
  'client_id': '007ea7439a9b92d792c0ea3dafe27b8cc4b611cbee85351b6900de945a4de13f',
  'client_secret': '73e6a5f3fff507fea7013d4260e804881651a45dd34b7ced58038b73977042e8'
}

# Launcher
if not args.picture:
    mainHandler(data)
else:
    printPic(str(args.picture))
