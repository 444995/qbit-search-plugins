# VERSION: 1.01
# AUTHORS: github.com/444995 - the code will improve and get updated
# LICENSING INFORMATION

# ----------------USER SETTINGS-------------------------- #

PRIVATE_USERNAME = "REPLACE_ME"                           # A DANISHBYTES ACCOUNT HAS A PRIVATE USERNAME
PUBLIC_USERNAME = "REPLACE_ME"                            # AND A PUBLIC USERNAME
PASSWORD = "REPLACE_ME"                                   # YOU ALSO NEED A PASSWORD
CACHE_LOGIN = True                                        # THIS IS TO CACHE THE LOGIN SESSION, SO YOU DON'T HAVE TO LOGIN EVERY TIME
LOGIN_SESSION_PATH = "danishbytes.pkl"                    # THE PATH TO THE LOGIN SESSION FILE

# ----------------NECESSARY IMPORTS---------------------- #

from html.parser import HTMLParser
from helpers import download_file, retrieve_url
from novaprinter import prettyPrinter

# ----------------IMPORTS-------------------------------- #

import requests
import pickle
import os
from bs4 import BeautifulSoup
import urllib.parse

# ------------------------------------------------------- #


class danishbytes(object):
    """
    `url`, `name`, `supported_categories` should be static variables of the engine_name class,
     otherwise qbt won't install the plugin.

    `url`: The URL of the search engine.
    `name`: The name of the search engine, spaces and special characters are allowed here.
    `supported_categories`: What categories are supported by the search engine and their corresponding id,
    possible categories are ('all', 'anime', 'books', 'games', 'movies', 'music', 'pictures', 'software', 'tv').
    """

    url = 'https://danishbytes.club'
    name = 'DanishBytes'
    # categories will get implemented
    supported_categories = { 
        'all': '0',
        'anime': '7',
        'games': '2',
        'movies': '6',
        'music': '1',
        'software': '3',
        'tv': '4'
    }

    def __init__(self):
        """
        Setting up env
        """
        self.base_url = danishbytes.url
        self.login_url = self.base_url + "/login"
        self.tracker_urls = ["https://danishbytes2.org/announce", "https://dbytes.org/announce", "https://danishbytes.club/announce"]
        self.user_agent = "Mozilla/5.0 (Linux; Android 10; RMX2185) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Mobile Safari/537.36"
        self.login_headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': self.user_agent
        }
        self.cur_dir = os.path.dirname(os.path.realpath(__file__))

        self.session = self._handle_user_login()

    def _get_db_session(self, response):
        """
        Extracts the db_session from the response headers.
        """
        return str(response.headers).split("db_session=")[1].split(";")[0]
    
    def _get_xsrf_token(self, response):
        """
        Extracts the XSRF token from the response headers.
        """
        return str(response.headers).split("XSRF-TOKEN=")[1].split(";")[0]

    def _write_cache_to_file(self, session):
        """
        Writes the session cache to a file.
        """
        with open(os.path.join(self.cur_dir, LOGIN_SESSION_PATH), 'wb') as file:
            pickle.dump(session.cookies, file)
        
    def _read_cache_from_file(self):
        """
        Reads the session cache from a file.
        """
        with open(os.path.join(self.cur_dir, LOGIN_SESSION_PATH), 'rb') as file:
            return requests.Session().cookies.update(pickle.load(file))

    def _extract_meta_content(self, soup, name):
        """Extracts content from meta tag with the given name."""
        tag = soup.find("meta", {"name": name})
        return tag["content"].strip() if tag else None
    
    def _extract_input_value(self, soup, name):
        """Extracts value from input tag with the given name."""
        tag = soup.find("input", {"name": name})
        return tag["value"].strip() if tag else None

    def _extract_dynamic_name_and_value(self, soup):
        """Extracts dynamic input name and value after the username input."""
        dynamic_name, dynamic_value = None, None
        for i, element in enumerate(soup.find_all("input", {"name": True, "value": True})):
            name = element["name"]
            if name == "_username":
                dynamic_name = soup.find_all("input", {"name": True, "value": True})[i+1]["name"]
                dynamic_value = soup.find_all("input", {"name": True, "value": True})[i+1]["value"]
                return dynamic_name, dynamic_value

    def _handle_user_login(self):
        """
        Handles user login and returns a session.
        """
        if CACHE_LOGIN and os.path.exists(LOGIN_SESSION_PATH):
            return self._read_cache_from_file()
            
        main_page = requests.get(self.base_url, allow_redirects=False)
        initial_db_session = self._get_db_session(main_page)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'cookie': f'db_session={initial_db_session}',
            'user-agent': self.user_agent
        }

        response = requests.get(self.login_url, headers=headers, allow_redirects=False)

        soup = BeautifulSoup(response.text, "html.parser")

        csrf_token = self._extract_meta_content(soup, "csrf-token")
        captcha_key = self._extract_input_value(soup, "_captcha")
        dynamic_name, dynamic_value = self._extract_dynamic_name_and_value(soup)
        _username = self._extract_input_value(soup, "_username")
        xsrf_token = self._get_xsrf_token(response)
        db_session = self._get_db_session(response)

        self.login_headers['cookie'] = f'XSRF-TOKEN={xsrf_token}; db_session={db_session}'

        payload = {
            "_token": csrf_token,
            "private_username": PRIVATE_USERNAME,
            "username": PUBLIC_USERNAME,
            "password": PASSWORD,
            "remember": "on",
            "_captcha": captcha_key,
            "_username": _username,
            dynamic_name: dynamic_value
        }
        
        session = requests.Session()
        login_response = session.post(self.login_url, headers=self.login_headers, data=urllib.parse.urlencode(payload), allow_redirects=True)


        if CACHE_LOGIN:
            self._write_cache_to_file(session)
        
        return session

    def download_torrent(self, info):
        """
        Providing this function is optional.
        It can however be interesting to provide your own torrent download
        implementation in case the search engine in question does not allow
        traditional downloads (for example, cookie-based download).
        """
        print(download_file(info))

    # DO NOT CHANGE the name and parameters of this function
    # This function will be the one called by nova2.py
    def search(self, what, cat='all'):
        """
        Here you can do what you want to get the result from the search engine website.
        Everytime you parse a result line, store it in a dictionary
        and call the prettyPrint(your_dict) function.

        `what` is a string with the search tokens, already escaped (e.g. "Ubuntu+Linux")
        `cat` is the name of a search category in ('all', 'anime', 'books', 'games', 'movies', 'music', 'pictures', 'software', 'tv')
        """

        response = self.session.get(self.base_url)

        soup = BeautifulSoup(response.text, "html.parser")

        csrf_token = self._extract_meta_content(soup, "csrf-token")

        def get_info(search_results):
            rss_key = search_results['rsskey']
            pass_key = search_results['passkey']

            def _make_magnet_url(torrent):
                magnet_url = "magnet:?"
                magnet_url += f"dn={torrent['name']}&"
                magnet_url += f"xt=urn:btih:{torrent['info_hash']}&"
                magnet_url += f"as={self.base_url}/torrent/download/{torrent['id']}.{rss_key}&"
                magnet_url += f"xl={torrent['size']}&"
                for tracker in self.tracker_urls:
                    magnet_url += f"tr={tracker}/{pass_key}&"

                return magnet_url[:-1]
            
            torrent_num = 0
            for torrent in search_results['torrents']:
                magnet_url = _make_magnet_url(torrent)
                name = torrent['name']
                size = torrent['size']
                seeders = torrent['seeders']
                leechers = torrent['leechers']
                engine_url = self.base_url
                desc_url = f"{self.base_url}/torrent/{torrent['id']}"

                print(f"{magnet_url}|{name}|{size}|{seeders}|{leechers}|{engine_url}|{desc_url}")

                torrent_num += 1

            return torrent_num
            
        page_num = 0
        while True:
            page_num += 1

            req_url = f"{self.base_url}/torrents/filter?_token={csrf_token}&search={what}&search_not=&uploader=&imdb=&tvdb=&view=list&tmdb=&mal=&igdb=&size_min=0&size_max=0&year_min=&year_max=&categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=5&categories%5B%5D=4&categories%5B%5D=3&categories%5B%5D=8&types%5B%5D=34&types%5B%5D=30&types%5B%5D=1&types%5B%5D=2&types%5B%5D=3&types%5B%5D=4&types%5B%5D=5&types%5B%5D=6&types%5B%5D=33&types%5B%5D=7&types%5B%5D=8&types%5B%5D=9&types%5B%5D=10&types%5B%5D=19&types%5B%5D=14&types%5B%5D=16&types%5B%5D=17&types%5B%5D=18&types%5B%5D=11&types%5B%5D=20&types%5B%5D=21&types%5B%5D=22&types%5B%5D=12&types%5B%5D=13&types%5B%5D=23&types%5B%5D=24&types%5B%5D=25&types%5B%5D=26&types%5B%5D=27&types%5B%5D=28&types%5B%5D=29&types%5B%5D=31&types%5B%5D=32&types%5B%5D=35&types%5B%5D=15&types%5B%5D=36&types%5B%5D=37&resolutions%5B%5D=1&resolutions%5B%5D=2&resolutions%5B%5D=3&resolutions%5B%5D=4&resolutions%5B%5D=5&resolutions%5B%5D=6&resolutions%5B%5D=7&resolutions%5B%5D=8&resolutions%5B%5D=9&resolutions%5B%5D=10&resolutions%5B%5D=11&language_codes%5B%5D=gb&language_codes%5B%5D=dk&language_codes%5B%5D=xx&language_codes%5B%5D=se&language_codes%5B%5D=no&language_codes%5B%5D=fi&language_codes%5B%5D=jp&language_codes%5B%5D=fr&language_codes%5B%5D=es&language_codes%5B%5D=de&language_codes%5B%5D=po&language_codes%5B%5D=kr&language_codes%5B%5D=is&language_codes%5B%5D=it&language_codes%5B%5D=pt&language_codes%5B%5D=ru&language_codes%5B%5D=cn&language_codes%5B%5D=nl&language_codes%5B%5D=ae&language_codes%5B%5D=in&language_codes%5B%5D=tu&language_codes%5B%5D=th&language_codes%5B%5D=gr&language_codes%5B%5D=ro&language_codes%5B%5D=ba&language_codes%5B%5D=id&language_codes%5B%5D=hu&language_codes%5B%5D=ir&language_codes%5B%5D=ua&language_codes_subs%5B%5D=gb&language_codes_subs%5B%5D=dk&language_codes_subs%5B%5D=xx&language_codes_subs%5B%5D=se&language_codes_subs%5B%5D=no&language_codes_subs%5B%5D=fi&language_codes_subs%5B%5D=jp&language_codes_subs%5B%5D=fr&language_codes_subs%5B%5D=es&language_codes_subs%5B%5D=de&language_codes_subs%5B%5D=po&language_codes_subs%5B%5D=kr&language_codes_subs%5B%5D=is&language_codes_subs%5B%5D=it&language_codes_subs%5B%5D=pt&language_codes_subs%5B%5D=ru&language_codes_subs%5B%5D=cn&language_codes_subs%5B%5D=nl&language_codes_subs%5B%5D=ae&language_codes_subs%5B%5D=in&language_codes_subs%5B%5D=tu&language_codes_subs%5B%5D=th&language_codes_subs%5B%5D=gr&language_codes_subs%5B%5D=ro&language_codes_subs%5B%5D=ba&language_codes_subs%5B%5D=id&language_codes_subs%5B%5D=hu&language_codes_subs%5B%5D=ir&language_codes_subs%5B%5D=ua&page={page_num}&qty=100"

            search_results = self.session.get(req_url).json()

            torrent_num = get_info(search_results)

            if torrent_num < 100:
                break




if __name__ == "__main__":
    engine = danishbytes()
    engine.search('hello')

