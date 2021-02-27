# reddit post scraping
# better use proxies to prevent IP block

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from datetime import date
from bs4 import BeautifulSoup
import re
import base64
import requests
import json
from pathlib import Path
import logging
import random
from multiprocessing import Pool
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# remove new line character
def new_line_remover(keyword_list):
    for i in range(len(keyword_list)):
        if '\n' in keyword_list[i]:
            keyword_list[i] = keyword_list[i].replace('\n', '')


# number of times to divide group
def even_chunks(l, n):
    # l is the name of list
    # n is number of elements in small list
    for i in range(0, len(l), n):
        yield l[i:i + n]


# function to wait for random time
def random_wait(a=0, b=None):
    if b == None:
        time.sleep(a)
    else:
        time.sleep(random.randrange(a,b))


def log_fun(log_path=None):
    # log_path = 'logs/'
    today = date.today()
    if log_path is None:
        log_file = Path(str(today) + '.log')
    else:
        log_file = Path(log_path + str(today) + '.log')
    logging.basicConfig(filename=log_file, filemode='a', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    return logging


# function to insert data
def inserter(payloads, sub_url):
    logger = log_fun('logs/')
    for d in payloads:
        print("Post response: {}".format(r.text))
        logger.info("Post response: %s, Payload: %s, Subreddit: %s", r.text, d, sub_url)


def reddit_crawler(subreddits):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
    # Configure driver and driver options
    driver_path = Path('chromedriver.exe').as_posix()
    options = Options()
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(executable_path=driver_path, options=options)

    login_url = 'https://www.reddit.com/login/'
    driver.get(login_url)
    random_wait(5, 10)

    account = ["your username", "your password"]
    try:
        # find the form element
        form = driver.find_element_by_class_name('AnimatedForm')
        # enter username
        username = form.find_element_by_id('loginUsername')
        username.clear()
        username.send_keys(account[0])
        # enter password
        password = form.find_element_by_id('loginPassword')
        password.clear()
        password.send_keys(account[1])
        # time.sleep(3)
        # click to login
        button = form.find_element_by_class_name('AnimatedForm__submitButton')
        button.click()
        time.sleep(3)
    except Exception as e:
        print('Login issue', e)
        driver.quit()

    try:
        for i in range(len(subreddits)):
            # if i == 0:
            #     reddit_url = login_url
            # else:
            #     reddit_url = subreddits[i-1]
            #     driver.get(reddit_url)
            #     random_wait(5, 10)

            reddit_url = subreddits[i]
            driver.get(reddit_url)
            logging.info("url hits")
            random_wait(5, 10)

            # join subreddit
            try:
                join = driver.find_element_by_xpath('//*[@id="SHORTCUT_FOCUSABLE_DIV"]/div[2]/div/div/div/div[2]/div[1]/div/div[1]/div/div[2]/button')
                print(join.text)
                if 'JOINED' not in join.text:
                    join.click()
            except Exception as e:
                print('Join subreddit issue:', e)

            try:
                # _2XKLlvmuqdor3RvVbYZfgz
                source_18 = driver.page_source
                soup_18 = BeautifulSoup(source_18, 'html.parser')
                data_18 = soup_18.find('h3', class_='_2XKLlvmuqdor3RvVbYZfgz')
                if data_18 is not None:
                    buttons = driver.find_elements_by_tag_name('button')
                    buttons[1].click()
            except Exception as e:
                print("18+ plus blocker issue:", e)

            try:
                # scroll down website
                html = driver.find_element_by_tag_name('html')
                for i in range(17):
                    html.send_keys(Keys.END)
                    random_wait(10, 15)
            except Exception as e:
                print('Scrolling issue:', e)

            # # Selenium script to scroll to the bottom, wait 3 seconds for the next batch of data to load, then continue scrolling.  It will continue to do    this until the page stops loading new data.
            # lenOfPage = driver.execute_script(
            #     "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            # match = False
            # while (match == False):
            #     lastCount = lenOfPage
            #     time.sleep(3)
            #     lenOfPage = driver.execute_script(
            #         "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            #     if lastCount == lenOfPage:
            #         match = True

            # Now that the page is fully scrolled, grab the source code
            source = driver.page_source
            # Throw your source into BeautifulSoup and start parsing!
            soup = BeautifulSoup(source, 'html.parser')
            data = soup.find_all('div', class_='Post')

            # scroll back to top
            # because click does not work properly from the bottom of page
            driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)

            payloads = []

            for post in data:
                try:
                    # upvote posts only which has more than thousand likes
                    try:
                        likes = post.find('div', class_='_1rZYMD_4xY3gRcSS3p8ODO').text
                        # print('This is likes', likes)
                        if 'k' in likes:
                            upvote_id = post.find('button', class_='voteButton').attrs['id']
                            upvote_ele = driver.find_element_by_id(upvote_id)
                            # element.get_attribute("attribute name")
                            upvote_value = upvote_ele.get_attribute('aria-pressed')
                            if upvote_value == 'false':
                                upvote_ele.click()
                    except Exception as e:
                        print('Unable to upvote', e)

                    # payload data
                    d = dict()
                    url = post.find('a', attrs={'class': '_3jOxDPIQ0KaOWpzvSQo-1s'}).attrs['href']
                    lst = url.split('/')
                    target_index = lst.index('comments') + 1
                    d['post_id'] = lst[target_index]

                    # title
                    if post.find('h3'):
                        # print('Extracting ad_title')
                        d['ad_title'] = post.find('h3').text
                    elif post.find('h1'):
                        d['ad_title'] = post.find('h1').text

                    d['post_url'] = post.find('a', attrs={'class': '_3jOxDPIQ0KaOWpzvSQo-1s'}).attrs['href']

                    # _2pjSQOdNtYd1I2W0Z1Im8I 
                    act = post.find('a', class_='_2pjSQOdNtYd1I2W0Z1Im8I')
                    d['action'] = act.text

                    # _1rZYMD_4xY3gRcSS3p8ODO
                    lik = post.find('div', class_='_1rZYMD_4xY3gRcSS3p8ODO _25IkBM0rRUqWX5ZojEMAFQ').text
                    if lik == "•":
                        lik = 0
                    d['likes'] = lik

                    d['post_description'] = post.find('a', class_='styled-outbound-link').text
                    d['post_date'] = int(time.time())
                    d['post_owner'] = post.find('a').text.split('/')[1]

                    if post.find('img', alt="Post image"):
                        # print('if statement')
                        d['type'] = 'IMAGE'
                        # original format
                        img_src = post.find('img', alt="Post image").attrs['src']
                        d['image_video_url'] = img_src
                    elif post.find('video'):
                        # print('elif statement')
                        d['type'] = 'VIDEO'
                        # Extracting the video url
                        vid_src = post.find('video').find('source').attrs['src']
                        vid_lst = vid_src.split('/')
                        vid_lst.pop()
                        vid_src = '/'.join(vid_lst)
                        vid_src = vid_src + '/DASH_96.mp4'
                        d['image_video_url'] = vid_src

                    # append to payloads list
                    payloads.append(d)
                except Exception as e:
                    print("Post error:", e)

            # insert payloads to inserter function
            inserter(payloads, reddit_url)
    except Exception as e:
        print('Looping subreddits issue:', e)
    # close the driver
    driver.quit()   


def open_file(lst):
    # lst is link extension numbers
    url_list = []
    for i in lst:
        # open the file with all links
        link_file = open(i + ".txt", "r")
        reddit_links = link_file.readlines()
        # remove new_line character
        new_line_remover(reddit_links)
        url_list.extend(reddit_links)
    return url_list

def get_reddit_urls():
    # generate tuple of lists with subreddits along with base urls
    # insert file extension numbers in open_file
    reddit_links = open_file(['reddit_links'])
    # shuffle the reddit urls
    random.shuffle(reddit_links)
    # make new lists with each n elements inside the bigger list
    n = 20
    # tuple_of_lists = tuple(even_chunks(reddit_links, n))
    list_of_lists = list(even_chunks(reddit_links, n))
    # creating new list of list with desired values 
    base_urls = ["https://www.reddit.com/", "https://www.reddit.com/hot/", "https://www.reddit.com/new/", "https://www.reddit.com/top/"]
    new_list_of_lists = []

    # with all subreddits and base urls
    for lst in list_of_lists:
        new_list = lst + base_urls
        random.shuffle(new_list)
        new_list_of_lists.append(new_list)

    # # with only base urls
    # for i in range(64):
    #     new_urls = base_urls.copy()
    #     random.shuffle(new_urls)
    #     new_list_of_lists.append(new_urls)

    tuple_of_lists = tuple(new_list_of_lists)
    return tuple_of_lists

if __name__ == '__main__':
    # get reddit urls
    tuple_of_lists = get_reddit_urls()

    with Pool(8) as p:
        print(p.map(reddit_crawler, tuple_of_lists))