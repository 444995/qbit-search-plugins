#VERSION: 1.00
# AUTHORS: github.com/444995 - the code is bad right now, i know
# LICENSING INFORMATION

from html.parser import HTMLParser
from helpers import download_file, retrieve_url
from novaprinter import prettyPrinter

# some other imports if necessary
import requests
import pickle
from bs4 import BeautifulSoup

class danishbytes(object):
    """
    `url`, `name`, `supported_categories` should be static variables of the engine_name class,
     otherwise qbt won't install the plugin.

    `url`: The URL of the search engine.
    `name`: The name of the search engine, spaces and special characters are allowed here.
    `supported_categories`: What categories are supported by the search engine and their corresponding id,
    possible categories are ('all', 'anime', 'books', 'games', 'movies', 'music', 'pictures', 'software', 'tv').
    """

    url = 'https://www.danishbytes.club'
    name = 'DanishBytes'
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
        Some initialization
        """

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
        # code will be added so it automatically logs in and uses that session (instead of this hardcoded one)
        SESSION_FILE = 'c:/Users/Admin/Desktop/db/1session.pkl'


        def load_session(file_path):
            session = requests.Session()
            with open(file_path, 'rb') as f:
                session.cookies.update(pickle.load(f))
            return session

        session = load_session(SESSION_FILE)


        response = session.get("https://danishbytes.club/")

        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("meta", {"name": "csrf-token"})["content"].strip()

        def get_info(search_results):
            rss_key = search_results['rsskey']
            pass_key = search_results['passkey']

            def _make_magnet_url(torrent):
                base_magnet_url = "magnet:?"
                dn = f"dn={torrent['name']}"
                xt = f"xt=urn:btih:{torrent['info_hash']}"
                as_ = f"as=https://danishbytes.club/torrent/download/{torrent['id']}.{rss_key}"
                xl = f"xl={torrent['size']}"
                tr1 = f"tr=https://danishbytes2.org/announce/{pass_key}"
                tr2 = f"tr=https://dbytes.org/announce/{pass_key}"
                tr3 = f"tr=https://danishbytes.club/announce/{pass_key}"

                return f"{base_magnet_url}{dn}&{xt}&{as_}&{xl}&{tr1}&{tr2}&{tr3}"
            
            torrent_num = 0
            for torrent in search_results['torrents']:
                magnet_url = _make_magnet_url(torrent)
                name = torrent['name']
                size = torrent['size']
                seeders = torrent['seeders']
                leechers = torrent['leechers']
                engine_url = f"https://danishbytes.club"
                desc_url = f"https://danishbytes.club/torrent/{torrent['id']}"

                # print link|name|size|seeds|leech|engine_url|desc_link
                print(f"{magnet_url}|{name}|{size}|{seeders}|{leechers}|{engine_url}|{desc_url}")

                torrent_num += 1

            return torrent_num
            
        page_num = 0
        while True:
            page_num += 1

            req_url = f"https://danishbytes.club/torrents/filter?_token={csrf_token}&search={what}&search_not=&uploader=&imdb=&tvdb=&view=list&tmdb=&mal=&igdb=&size_min=0&size_max=0&year_min=&year_max=&categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=5&categories%5B%5D=4&categories%5B%5D=3&categories%5B%5D=8&types%5B%5D=34&types%5B%5D=30&types%5B%5D=1&types%5B%5D=2&types%5B%5D=3&types%5B%5D=4&types%5B%5D=5&types%5B%5D=6&types%5B%5D=33&types%5B%5D=7&types%5B%5D=8&types%5B%5D=9&types%5B%5D=10&types%5B%5D=19&types%5B%5D=14&types%5B%5D=16&types%5B%5D=17&types%5B%5D=18&types%5B%5D=11&types%5B%5D=20&types%5B%5D=21&types%5B%5D=22&types%5B%5D=12&types%5B%5D=13&types%5B%5D=23&types%5B%5D=24&types%5B%5D=25&types%5B%5D=26&types%5B%5D=27&types%5B%5D=28&types%5B%5D=29&types%5B%5D=31&types%5B%5D=32&types%5B%5D=35&types%5B%5D=15&types%5B%5D=36&types%5B%5D=37&resolutions%5B%5D=1&resolutions%5B%5D=2&resolutions%5B%5D=3&resolutions%5B%5D=4&resolutions%5B%5D=5&resolutions%5B%5D=6&resolutions%5B%5D=7&resolutions%5B%5D=8&resolutions%5B%5D=9&resolutions%5B%5D=10&resolutions%5B%5D=11&language_codes%5B%5D=gb&language_codes%5B%5D=dk&language_codes%5B%5D=xx&language_codes%5B%5D=se&language_codes%5B%5D=no&language_codes%5B%5D=fi&language_codes%5B%5D=jp&language_codes%5B%5D=fr&language_codes%5B%5D=es&language_codes%5B%5D=de&language_codes%5B%5D=po&language_codes%5B%5D=kr&language_codes%5B%5D=is&language_codes%5B%5D=it&language_codes%5B%5D=pt&language_codes%5B%5D=ru&language_codes%5B%5D=cn&language_codes%5B%5D=nl&language_codes%5B%5D=ae&language_codes%5B%5D=in&language_codes%5B%5D=tu&language_codes%5B%5D=th&language_codes%5B%5D=gr&language_codes%5B%5D=ro&language_codes%5B%5D=ba&language_codes%5B%5D=id&language_codes%5B%5D=hu&language_codes%5B%5D=ir&language_codes%5B%5D=ua&language_codes_subs%5B%5D=gb&language_codes_subs%5B%5D=dk&language_codes_subs%5B%5D=xx&language_codes_subs%5B%5D=se&language_codes_subs%5B%5D=no&language_codes_subs%5B%5D=fi&language_codes_subs%5B%5D=jp&language_codes_subs%5B%5D=fr&language_codes_subs%5B%5D=es&language_codes_subs%5B%5D=de&language_codes_subs%5B%5D=po&language_codes_subs%5B%5D=kr&language_codes_subs%5B%5D=is&language_codes_subs%5B%5D=it&language_codes_subs%5B%5D=pt&language_codes_subs%5B%5D=ru&language_codes_subs%5B%5D=cn&language_codes_subs%5B%5D=nl&language_codes_subs%5B%5D=ae&language_codes_subs%5B%5D=in&language_codes_subs%5B%5D=tu&language_codes_subs%5B%5D=th&language_codes_subs%5B%5D=gr&language_codes_subs%5B%5D=ro&language_codes_subs%5B%5D=ba&language_codes_subs%5B%5D=id&language_codes_subs%5B%5D=hu&language_codes_subs%5B%5D=ir&language_codes_subs%5B%5D=ua&page={page_num}&qty=100"

            search_results = session.get(req_url).json()

            torrent_num = get_info(search_results)

            if torrent_num < 100:
                break