#####################################################################################
#   AUTHOR: github.com/444995 - the code will improve and get updated               #
#   VERSION: 1.02                                                                   #
#####################################################################################


###########################   LICENSING INFORMATION   ###############################
#   Permission is hereby granted, free of charge, to any person obtaining a copy    #
#   of this software and associated documentation files (the "Software"), to deal   #
#   in the Software without restriction, including without limitation the rights    #
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
#   copies of the Software, and to permit persons to whom the Software is           #
#   furnished to do so, subject to the following conditions:                        #
#                                                                                   #
#   The above copyright notice and this permission notice shall be included in      #
#   all copies or substantial portions of the Software.                             #
#                                                                                   #                                    
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
#   SOFTWARE.                                                                       #
#####################################################################################


# ----------------USER SETTINGS-------------------------- #

PRIVATE_USERNAME = "REPLACE_ME"                           # A DANISHBYTES ACCOUNT HAS A PRIVATE USERNAME
PUBLIC_USERNAME = "REPLACE_ME"                            # AND A PUBLIC USERNAME
PASSWORD = "REPLACE_ME"                                   # YOU ALSO NEED A PASSWORD
CACHE_LOGIN = True                                        # THIS IS TO CACHE THE LOGIN SESSION, SO YOU DON'T HAVE TO LOGIN EVERY TIME
LOGIN_SESSION_FILENAME = "danishbytes.pkl"                # THE PATH TO THE LOGIN SESSION FILE

# ----------------IMPORTS-------------------------------- #

import os
import pickle
import urllib.request
import urllib.parse
import requests
from bs4 import BeautifulSoup

# ----------------CODE----------------------------------- #

class SessionCacheManager:
    """
    Manages the session cache.
    """
    def __init__(self, login_session_filepath):
        self.login_session_filepath = login_session_filepath

    def write_login_cache_to_file(self, session):
        """
        Writes the session cache to a file.
        """
        with open(self.login_session_filepath, 'wb') as file:
            pickle.dump(session.cookies, file)
        
    def read_login_cache_from_file(self):
        """
        Reads the session cache from a file.
        """
        with open(self.login_session_filepath, 'rb') as file:
            session = requests.Session()
            session.cookies.update(pickle.load(file))
            return session

    def cache_exists(self):
        """
        Checks if the cache exists.
        """
        return os.path.exists(self.login_session_filepath)

    def remove_cache(self):
        """
        Removes the cache.
        """
        if self.cache_exists():
            os.remove(self.login_session_filepath)


class HtmlExtractor:
    """
    Extracts content from HTML.
    """
    @staticmethod
    def extract_meta_content(soup, name):
        """Extracts content from meta tag with the given name."""
        tag = soup.find("meta", {"name": name})
        return tag["content"].strip() if tag else None

    @staticmethod
    def extract_input_value(soup, name):
        """Extracts value from input tag with the given name."""
        tag = soup.find("input", {"name": name})
        return tag["value"].strip() if tag else None

    @staticmethod
    def extract_dynamic_name_and_value(soup): # should probably get refactored
        """Extracts dynamic input name and value after the username input."""
        dynamic_name, dynamic_value = None, None
        for i, element in enumerate(soup.find_all("input", {"name": True, "value": True})):
            name = element["name"]
            if name == "_username":
                dynamic_name = soup.find_all("input", {"name": True, "value": True})[i+1]["name"]
                dynamic_value = soup.find_all("input", {"name": True, "value": True})[i+1]["value"]
        
        return dynamic_name, dynamic_value

    @staticmethod
    def fetch_specific_cookie(response, cookie_name):
        """
        Fetches the specific cookie from the response headers.
        """
        return str(response.headers).split(f"{cookie_name}=")[1].split(";")[0]
        


class danishbytes(object):
    """
    DanishBytes engine for qBittorrent.
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
        Initializes the DanishBytes engine for qBittorrent.
        """
        self.site_url = danishbytes.url
        self.login_url = f"{self.site_url}/login"
        self.tracker_urls = ["https://danishbytes2.org/announce", "https://dbytes.org/announce", "https://danishbytes.club/announce"]
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0"
        
        self.cur_dir = os.path.dirname(os.path.realpath(__file__))
        self.login_session_path = os.path.join(self.cur_dir, LOGIN_SESSION_FILENAME)


        self.html_extractor = HtmlExtractor()
        self.session_cache_manager = SessionCacheManager(login_session_filepath=self.login_session_path)

        self.session = self._fetch_session()
        self.csrf_token = self._verify_login()

    def _fetch_session(self):
        """
        Fetches the session from the cache or logs in and returns the session.
        """
        if CACHE_LOGIN and self.session_cache_manager.cache_exists():
            return self.session_cache_manager.read_login_cache_from_file()

        return self._login()


    def _login(self):
        """
        Logs into DanishBytes and returns the session.
        """
        # initial request to get the db_session cookie
        response = requests.get(self.site_url, allow_redirects=False)
        initial_db_session = self.html_extractor.fetch_specific_cookie(response, "db_session")

        # make a request to the login page so we can get the csrf token, captcha key, dynamic name, dynamic value, xsrf toke and db_session cookie
        response = requests.get(
            self.login_url, 
            headers={
                'cookie': f'db_session={initial_db_session}', 
                'user-agent': self.user_agent
            }, 
            allow_redirects=False
        )

        soup = BeautifulSoup(response.text, "html.parser")

        # fetch the db_session cookie from response headers
        _db_session = self.html_extractor.fetch_specific_cookie(response, "db_session")
        _xsrf_token = self.html_extractor.fetch_specific_cookie(response, "XSRF-TOKEN")

        # fetch the csrf token, captcha key, dynamic name and value from the soup object
        _csrf_token = self.html_extractor.extract_meta_content(soup, "csrf-token")
        _captcha_key = self.html_extractor.extract_input_value(soup, "_captcha")
        _username = self.html_extractor.extract_input_value(soup, "_username")
        _dynamic_name, _dynamic_value = self.html_extractor.extract_dynamic_name_and_value(soup)

        
        # payload for the login request
        payload = {
            "_token": _csrf_token,
            "private_username": PRIVATE_USERNAME,
            "username": PUBLIC_USERNAME,
            "password": PASSWORD,
            "remember": "on",
            "_captcha": _captcha_key,
            "_username": _username,
            _dynamic_name: _dynamic_value
        }
        
        # session so we can use it later without having to login each time
        session = requests.Session()
        session.post(
            self.login_url, 
            headers={
                'content-type': 'application/x-www-form-urlencoded', 
                'cookie': f'XSRF-TOKEN={_xsrf_token}; db_session={_db_session}', 
                'user-agent': self.user_agent
            }, 
            data=urllib.parse.urlencode(payload), 
            allow_redirects=True,
        )

        if CACHE_LOGIN:
            self.session_cache_manager.write_login_cache_to_file(session)
        
        return session


    def _verify_login(self):
        """
        Verifies the login by checking if the csrf token is present in the site's main page.
        """
        response = self.session.get(self.site_url, allow_redirects=False)
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = self.html_extractor.extract_meta_content(soup, "csrf-token")

        # if the csrf token is None, it means the login failed, so we remove the login session file
        # so we can allow the user to login again with a new session
        if csrf_token is None:
            self.session_cache_manager.remove_cache()

        return csrf_token

    def download_torrent(self, info):
        # will be implemented later
        pass

    def _process_search_results(self, search_results):
        """
        Processes search results and prints them.
        """
        rss_key = search_results['rsskey']
        pass_key = search_results['passkey']

        def _make_magnet_url(torrent):
            magnet_url = "magnet:?"
            magnet_url += f"dn={torrent['name']}&"
            magnet_url += f"xt=urn:btih:{torrent['info_hash']}&"
            magnet_url += f"as={self.site_url}/torrent/download/{torrent['id']}.{rss_key}&"
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
            engine_url = self.site_url
            desc_url = f"{self.site_url}/torrent/{torrent['id']}"

            # prettyprint isn't used because danishbytes gives size in bytes already
            print(f"{magnet_url}|{name}|{size}|{seeders}|{leechers}|{engine_url}|{desc_url}")

            torrent_num += 1

        return torrent_num


    def search(self, what, cat='all'):
        """
        Searches for torrents on DanishBytes.
        """
        if self.csrf_token is None:
            raise Exception("Your login to DanishBytes failed. Please check your credentials and try again.")


        page_num = 0
        while True:
            page_num += 1

            req_url = f"{self.site_url}/torrents/filter?_token={self.csrf_token}&search={what}&search_not=&uploader=&imdb=&tvdb=&view=list&tmdb=&mal=&igdb=&size_min=0&size_max=0&year_min=&year_max=&categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=5&categories%5B%5D=4&categories%5B%5D=3&categories%5B%5D=8&types%5B%5D=34&types%5B%5D=30&types%5B%5D=1&types%5B%5D=2&types%5B%5D=3&types%5B%5D=4&types%5B%5D=5&types%5B%5D=6&types%5B%5D=33&types%5B%5D=7&types%5B%5D=8&types%5B%5D=9&types%5B%5D=10&types%5B%5D=19&types%5B%5D=14&types%5B%5D=16&types%5B%5D=17&types%5B%5D=18&types%5B%5D=11&types%5B%5D=20&types%5B%5D=21&types%5B%5D=22&types%5B%5D=12&types%5B%5D=13&types%5B%5D=23&types%5B%5D=24&types%5B%5D=25&types%5B%5D=26&types%5B%5D=27&types%5B%5D=28&types%5B%5D=29&types%5B%5D=31&types%5B%5D=32&types%5B%5D=35&types%5B%5D=15&types%5B%5D=36&types%5B%5D=37&resolutions%5B%5D=1&resolutions%5B%5D=2&resolutions%5B%5D=3&resolutions%5B%5D=4&resolutions%5B%5D=5&resolutions%5B%5D=6&resolutions%5B%5D=7&resolutions%5B%5D=8&resolutions%5B%5D=9&resolutions%5B%5D=10&resolutions%5B%5D=11&language_codes%5B%5D=gb&language_codes%5B%5D=dk&language_codes%5B%5D=xx&language_codes%5B%5D=se&language_codes%5B%5D=no&language_codes%5B%5D=fi&language_codes%5B%5D=jp&language_codes%5B%5D=fr&language_codes%5B%5D=es&language_codes%5B%5D=de&language_codes%5B%5D=po&language_codes%5B%5D=kr&language_codes%5B%5D=is&language_codes%5B%5D=it&language_codes%5B%5D=pt&language_codes%5B%5D=ru&language_codes%5B%5D=cn&language_codes%5B%5D=nl&language_codes%5B%5D=ae&language_codes%5B%5D=in&language_codes%5B%5D=tu&language_codes%5B%5D=th&language_codes%5B%5D=gr&language_codes%5B%5D=ro&language_codes%5B%5D=ba&language_codes%5B%5D=id&language_codes%5B%5D=hu&language_codes%5B%5D=ir&language_codes%5B%5D=ua&language_codes_subs%5B%5D=gb&language_codes_subs%5B%5D=dk&language_codes_subs%5B%5D=xx&language_codes_subs%5B%5D=se&language_codes_subs%5B%5D=no&language_codes_subs%5B%5D=fi&language_codes_subs%5B%5D=jp&language_codes_subs%5B%5D=fr&language_codes_subs%5B%5D=es&language_codes_subs%5B%5D=de&language_codes_subs%5B%5D=po&language_codes_subs%5B%5D=kr&language_codes_subs%5B%5D=is&language_codes_subs%5B%5D=it&language_codes_subs%5B%5D=pt&language_codes_subs%5B%5D=ru&language_codes_subs%5B%5D=cn&language_codes_subs%5B%5D=nl&language_codes_subs%5B%5D=ae&language_codes_subs%5B%5D=in&language_codes_subs%5B%5D=tu&language_codes_subs%5B%5D=th&language_codes_subs%5B%5D=gr&language_codes_subs%5B%5D=ro&language_codes_subs%5B%5D=ba&language_codes_subs%5B%5D=id&language_codes_subs%5B%5D=hu&language_codes_subs%5B%5D=ir&language_codes_subs%5B%5D=ua&page={page_num}&qty=100"

            search_results = self.session.get(req_url).json()

            torrent_num = self._process_search_results(search_results)

            if torrent_num < 100:
                break



if __name__ == "__main__":
    # For testing purposes
    a = danishbytes()
    a.search('hello')