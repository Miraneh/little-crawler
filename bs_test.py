import datetime
import json
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd, numpy as np
from pandas.io.json import json_normalize


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
    information = pd.DataFrame()
    for i in range(len(links)):
        """
            Some links might fail, we will put the whole process in a try-catch
        """
        try:
            post = s.get(links[i])
            post_data = bs(post, 'html.parser')
            body = post_data.find('body')
            script = body.find('script')
            raw = script.text.strip().replace('window._sharedData =', '').replace(';', '')
            json_data = json.loads(raw)
            posts = json_data['entry_data']['PostPage'][0]['graphql']
            posts = json.dumps(posts)
            posts = json.loads(posts)
            x = pd.DataFrame.from_dict(json_normalize(posts), orient='columns')
            x.columns = x.columns.str.replace("shortcode_media.", "")
            print("here" , x)
            information.append(x)

        except Exception as e:
            print(e)

    information = information.drop_duplicates(subset='shortcode')
    information.index = range(len(information.index))
    information.to_csv("nike_data.csv")


def login(username, password):
    with requests.session() as s:
        link = 'https://www.instagram.com/accounts/login/'
        login_url = 'https://www.instagram.com/accounts/login/ajax/'

        time = int(datetime.datetime.now().timestamp())
        response = s.get(link)
        csrf = response.cookies['csrftoken']
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

        login_response = s.post(login_url, data=payload, headers=login_header)
        json_data = json.loads(login_response.text)

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

        url = "https://www.instagram.com/{}".format("nike")
        data_received = s.get(url)
        bs_data = bs(data_received.text, "html.parser")
        title = bs_data.title
        # rep = bs_data.find('meta', property='og:description').attrs["content"]

        print(title.text)
        # print(rep)
        links = parse_data(bs_data)
        print("Links: ", links)
        create_df(s, links)



#username = input("Enter your username: ")
#password = input("Enter your password: ")
login("mehranehn", "Passinsta174*")
