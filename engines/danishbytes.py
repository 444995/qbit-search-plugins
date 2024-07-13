# VERSION: 1.3                                                                    #
# AUTHOR: github.com/444995 - updates will come                                   #


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
CACHE_LOGIN_COOKIES = True                                # CACHE COOKIES (HIGHLY RECOMMENDED)
COOKIES_FILE_NAME = "danishbytes.cookies"                 # THE PATH TO THE LOGIN 

# ----------------IMPORTS-------------------------------- #

import os
import json
import gzip
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import http.cookiejar as cookielib
from urllib.error import HTTPError

# ----------------CODE----------------------------------- #

class HtmlExtractor:
    """
    Extracts needed keys and tokens from a given HTML response.
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


class danishbytes(object):
    """
    DanishBytes engine for qBittorrent.
    """

    url = 'https://danishbytes.club'
    name = 'DanishBytes'
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'

    supported_categories = {
        'all': '0', # 'all' is just every category combined
        'movies': '1',
        'tv': '2',
        'music': '3',
        'games': '4',
        'software': '5',
        'books': '8',
    }

    def __init__(self):
        """
        Initializes the DanishBytes engine for qBittorrent.
        """
        self.login_url = f"{self.url}/login"
        self.tracker_urls = [
            "https://danishbytes2.org/announce", 
            "https://dbytes.org/announce", 
            "https://danishbytes.club/announce"
        ]
        self.categories_string = "&categories%5B%5D="
        
        self.cur_dir = os.path.dirname(os.path.realpath(__file__))
        self.cookies_file_path = os.path.join(self.cur_dir, COOKIES_FILE_NAME)

        self.html_extractor = HtmlExtractor()

        self.opener = self._create_opener()
        self._set_cookies()
        self.csrf_token = self._verify_login()

        if self.csrf_token is None:
            raise Exception("Login failed, please check your credentials.")

    def _create_opener(self):
        self.cookiejar = cookielib.LWPCookieJar(self.cookies_file_path)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))
        opener.addheaders = [
            ('User-Agent', danishbytes.user_agent),
            ('Accept-Encoding', 'gzip, deflate'),
        ]

        return opener

    def _make_request(self, url, data=None):
        """
        Makes a request to the given URL using urllib.
        """
        encoded_data = urllib.parse.urlencode(data).encode() if data else None
        try:
            with self.opener.open(url, encoded_data or None) as response:
                if response.info().get('Content-Encoding') == 'gzip':
                    buffer = gzip.GzipFile(fileobj=response)
                    content = buffer.read()
                else:
                    content = response.read()
                return content

        except HTTPError as e:
            request_type = "POST" if data else "GET"
            raise Exception(f"HTTP {request_type} request to '{url}' failed with status: {e.code} - probably login failure")
            
    def _set_cookies(self):
        """
        Fetches the cookies from the cookies file if it exists, otherwise logs in.
        """
        if CACHE_LOGIN_COOKIES and os.path.exists(self.cookies_file_path):
            self.cookiejar.load(
                self.cookies_file_path,
                ignore_discard=True, 
                ignore_expires=True
            )
        else:
            self._login()

    def _login(self):
        """
        Logs into DanishBytes; this automatically sets the cookies in the cookiejar
            hence why cookies aren't returned
        """
        # initial request to get cookies and keys
        response = self._make_request(self.login_url)
 
        # fetch the csrf token, captcha key, dynamic name and value from the soup object
        soup = BeautifulSoup(response, "html.parser")
        _csrf_token = self.html_extractor.extract_meta_content(soup, "csrf-token")
        _captcha_key = self.html_extractor.extract_input_value(soup, "_captcha")
        _username = self.html_extractor.extract_input_value(soup, "_username")
        _dynamic_name, _dynamic_value = self.html_extractor.extract_dynamic_name_and_value(soup)


        # login request
        self._make_request(
            self.login_url, 
            data = { 
                "_token": _csrf_token,
                "private_username": PRIVATE_USERNAME,
                "username": PUBLIC_USERNAME,
                "password": PASSWORD,
                "remember": "on",
                "_captcha": _captcha_key,
                "_username": _username,
                _dynamic_name: _dynamic_value
            }
        )
 
        if CACHE_LOGIN_COOKIES:
            self.cookiejar.save(
                self.cookies_file_path, 
                ignore_discard=True, 
                ignore_expires=True
            )

    def _verify_login(self):
        """
        Verifies the login by checking if the csrf token is present in the site's main page.
        """
        response = self._make_request(self.url)
        soup = BeautifulSoup(response, "html.parser")
        csrf_token = self.html_extractor.extract_meta_content(soup, "csrf-token")

        # if the csrf token is None, it means the login failed, so we remove the cookies file
        # so we can allow the user to login again with a new session
        if csrf_token is None and os.path.exists(self.cookies_file_path):
            os.remove(self.cookies_file_path)

        return csrf_token

    def download_torrent(self, info):
        # will be implemented later
        pass

    def _process_search_results(self, search_results):
        """
        Processes search results and prints them.
        """
        # these shouldnt be defined each time, but for now it's fine
        rss_key = search_results['rsskey'] 
        pass_key = search_results['passkey']

        def _make_magnet_url(torrent):
            magnet_url = "magnet:?"
            magnet_url += f"dn={torrent['name']}&"
            magnet_url += f"xt=urn:btih:{torrent['info_hash']}&"
            magnet_url += f"as={self.url}/torrent/download/{torrent['id']}.{rss_key}&"
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
            engine_url = self.url
            desc_url = f"{self.url}/torrent/{torrent['id']}"

            # prettyprint isn't used because danishbytes gives size in bytes already
            print(f"{magnet_url}|{name}|{size}|{seeders}|{leechers}|{engine_url}|{desc_url}")

            torrent_num += 1

        return torrent_num


    def search(self, query, cat='all'):
        """
        Searches for torrents on DanishBytes.
        """
        if cat not in self.supported_categories:
            raise ValueError("Unsupported category")
        
        if cat == 'all':
            category_param = ''.join([self.categories_string + cat for cat in self.supported_categories.values()])
        else:
            category_param = self.categories_string + self.supported_categories[cat]

        page_num = 0
        while True:
            page_num += 1
            search_url = f"{self.url}/torrents/filter?_token={self.csrf_token}&search={query}&page={page_num}&qty=100{category_param}"
            response = self._make_request(search_url)
            search_results = json.loads(response)

            self._process_search_results(search_results)

            if len(search_results['torrents']) < 100:
                break

if __name__ == "__main__":
    # For testing purposes
    a = danishbytes()
    a.search('the', cat="tv")