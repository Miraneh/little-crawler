import datetime
import json
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import time

instagram_pages = ["nike", "adidas", "instagram", "neymarjr", "natgeo", "therock", "leomessi", "caistudio",
                   "takashipom",
                   "artistgeorgecondo", "kaws", "aiww", "obeygiant", "pauloctavious", "osgemeos", "kennyscharf",
                   "mayabeano", "jr", "artbymoga", "sarahandersencomics"]


def get_post_links(data):
    links = []
    body = data.find('body')
    script = body.find('script', text=lambda t: t.startswith('window._sharedData'))
    page_json = script.text.split(' = ', 1)[1].rstrip(';')
    data = json.loads(page_json)
    for link in data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']:
        links.append('https://www.instagram.com' + '/p/' + link['node']['shortcode'] + '/')
    return links


def extract_data_from_posts(s: requests.session(), links: []):
    information = pd.DataFrame(
        columns=['Account', 'Post Link', 'Caption', 'Post Type', 'Comments', 'View', 'Video Duration'])
    for i in range(len(links)):
        time.sleep(1)
        print(links[i])
        """
            Some links might fail, we will put the whole process in a try-catch
        """
        for j in range(10):
            try:
                post = s.get(links[i])
                post_html_data = bs(post.text, 'html.parser')
                post_title = post_html_data.title.text
                print(post_title)

                caption = ""
                for k in range(len(post_title)):
                    if post_title[k] == '“':
                        caption = post_title[k:-1]
                        break

                body = post_html_data.find('body')
                scripts = body.find_all('script')

                for scr in scripts:
                    if 'window.__additionalDataLoaded' in scr.text:
                        post_script = scr.text
                        break

                for k in range(len(post_script)):
                    if post_script[k] == '{':
                        detail_text = post_script[k:-2]
                        break

                json_data = json.loads(detail_text)
                post_kind = json_data['graphql']['shortcode_media']['__typename']

                if post_kind == 'GraphImage':
                    post_type = 'image'
                    view = None
                    video_duration = 0
                    comments = json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']['count']
                elif post_kind == 'GraphVideo':
                    post_type = 'video'
                    view = json_data['graphql']['shortcode_media']['video_view_count']
                    video_duration = json_data['graphql']['shortcode_media']['video_duration']
                    comments = json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']['count']
                elif post_kind == 'GraphSidecar':
                    post_type = 'collection'
                    view = None
                    video_duration = 0
                    comments = json_data['graphql']['shortcode_media']['edge_media_to_parent_comment']['count']

                username = json_data['graphql']['shortcode_media']['owner']['username']
                row = pd.DataFrame(
                    {"Account": [username], "Post Link": [links[i]], "Caption": [caption], "Post Type": [post_type],
                     "Comments": [comments],
                     "View": [view], "Video Duration": [video_duration]})
                print("ROW: ", row)
                information = information.append(row, ignore_index=True)
                break
            except Exception as e:
                print(e)
                print("retying in 10 seconds...")
                time.sleep(10)

    information.to_csv(r"{}.csv".format(username))
    print("Creation Completed.")


def start_crawling(s: requests.session):
    for ig_page in instagram_pages:
        url = "https://www.instagram.com/{}".format(ig_page)
        data_received = s.get(url)
        bs_page = bs(data_received.text, "html.parser")
        title = bs_page.title

        print(title.text)
        links = get_post_links(bs_page)
        print("Links: ", links)
        extract_data_from_posts(s, links)


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
                print("Connecting to login page failed. Retrying... (if it takes too long you might want to rerun)")

        print("Connected to login page. We'll login now...")

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

        start_crawling(s)


user_name = input("Enter your username: ")
pass_word = input("Enter your password: ")
login(user_name, pass_word)
