import datetime
import json
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd, numpy as np
from pandas.io.json import json_normalize
import time


def parse_data(data):
    links = []
    body = data.find('body')
    script = body.find('script', text=lambda t: t.startswith('window._sharedData'))
    page_json = script.text.split(' = ', 1)[1].rstrip(';')
    data = json.loads(page_json)
    for link in data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']:
        links.append('https://www.instagram.com' + '/p/' + link['node']['shortcode'] + '/')
    return links


def create_df(s: requests.session(), links: []):
    information = pd.DataFrame(columns=['Account', 'Post Link', 'Caption', 'Post Type', 'Comments', 'View', 'Video Duration'])
    for i in range(len(links)):
        time.sleep(1)
        print(links[i])
        """
            Some links might fail, we will put the whole process in a try-catch
        """
        for j in range(10):
            try:
                post = s.get(links[i])
                post_data = bs(post.text, 'html.parser')
                post_title = post_data.title.text
                username = post_title.split()[0]
                body = post_data.find('body')
                scripts = body.find_all('script')

                for element in scripts:
                    if 'window.__additionalDataLoaded' in element.text:
                        post_script = element.text
                        break

                for k in range(len(post_script)):
                    if post_script[k] == '{':
                        json_text = post_script[k:-2]
                        break
                
                print(json_text)
                json_data = json.loads(json_text)
                if json_data['graphql']['shortcode_media']['__typename'] == 'GraphImage':
                    post_type = 'image'
                    view = None
                    video_duration = 0
                    comments = json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']
                elif json_data['graphql']['shortcode_media']['__typename'] == 'GraphVideo':
                    post_type = 'video'
                    view = json_data['graphql']['shortcode_media']['video_view_count']
                    video_duration = json_data['graphql']['shortcode_media']['video_duration']
                    comments = json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']
                else:
                    continue

                row = pd.DataFrame({"Account": username, "Post Link": links[i], "Caption": post_title, "Post Type": post_type, "Comments": comments,
                                    "View" : view, "Video Duration": video_duration})
                print("ROW: ", row)
                information = information.append(row, ignore_index=True)
                break
            except Exception as e:
                print(e)
                print("retying in 10 seconds...")
                time.sleep(10)
    #information = information.drop_duplicates(subset='shortcode')
    #information.index = range(len(information.index))
    information.to_csv(r"{}.csv".format(username))


def login(username, password):
    with requests.session() as s:
        link = 'https://www.instagram.com/accounts/login/'
        login_url = 'https://www.instagram.com/accounts/login/ajax/'

        time = int(datetime.datetime.now().timestamp())

        for i in range(5):
            try:
                response = s.get(link)
                csrf = response.cookies['csrftoken']
                break
            except Exception as e:
                print("retry...")

        """response = s.get(link)
        csrf = response.cookies['csrftoken']"""
        print(csrf)
        payload = {
            'username': username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{password}',
            'queryParams': {},
            'optIntoOneTap': 'false'
        }

        login_header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "x-csrftoken": csrf
        }
        for i in range(5):
            try:
                login_response = s.post(login_url, data=payload, headers=login_header)
                json_data = json.loads(login_response.text)
                break
            except Exception as e:
                print("trying..")

        if json_data["authenticated"]:
            print("login successful")
            cookies = login_response.cookies
            cookie_jar = cookies.get_dict()
            csrf_token = cookie_jar['csrftoken']
            print("csrf_token: ", csrf_token)
            session_id = cookie_jar['sessionid']
            print("session_id: ", session_id)
        else:
            print("login failed ", login_response.text)

        url = "https://www.instagram.com/{}".format("adidas")
        data_received = s.get(url)
        bs_data = bs(data_received.text, "html.parser")
        title = bs_data.title
        # rep = bs_data.find('meta', property='og:description').attrs["content"]

        print(title.text)
        # print(rep)
        links = parse_data(bs_data)
        print("Links: ", links)
        create_df(s, links)


# username = input("Enter your username: ")
# password = input("Enter your password: ")
login("mehranehn", "Passinsta174*")
