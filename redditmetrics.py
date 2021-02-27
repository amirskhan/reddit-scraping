# code to scrape subreddits from redditmetrics.com
# better use proxies to prevent IP block

import time
from datetime import date
from bs4 import BeautifulSoup
import re
import base64
import requests
import json
from pathlib import Path
import random


user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
proxies = "use proxies"

count = 0
while True:
    if count == 0:
        url = 'https://redditmetrics.com/top'
    else:
        url = 'https://redditmetrics.com/top/offset/' + str(count)
    response = requests.get(url, proxies=proxies, headers={'User-Agent': user_agent}, timeout=5)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find_all('td', attrs={'class':'tod'})
    subreddits = []
    for name in data:
        if name.a:
            sub_url = "https://www.reddit.com" + name.a.text
            subreddits.append(sub_url)

    for sub in subreddits:
        print(sub)

    # insert list in text file
    with open("file.txt", "a") as f:
        for item in subreddits:
            f.write("%s\n" % item)

    count += 100
    if soup.find('a', attrs={'href':'/top/offset/' + str(count)}):
        continue
    else:
        break

    print(count)