# VERSION: 1.0
# AUTHORS: github.com/444995

import tempfile
import urllib.parse
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import gzip
from helpers import retrieve_url
from novaprinter import prettyPrinter
import http.cookiejar as cookielib

# EVEN IF THIS IS SET TO FALSE
# IT STILL FALLS BACK TO MAGNET LINKS 
# IF A TORRENT FILE IS NOT AVAILABLE
USE_MAGNET_LINKS = False

class zooqle(object):
    url = 'https://zooqle.skin'
    name = 'Zooqle'

    # Categories are not supported on the site in the way
    # that you can use a query and a category for searching
    supported_categories = {
        'all': "0"
    }

    search_url = f"{url}/search/"
    download_url = f"{url}/torfile/"
    torrent_page_url = f'{url}/torrent-page/'

    def __init__(self):
        self.torrents_per_page = 40
        self.cookiejar = cookielib.LWPCookieJar()
        self.opener = self._create_opener()

    def _create_opener(self):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'),
            ('Content-Type', 'application/x-www-form-urlencoded'),
        ]
        return opener

    def _make_request(self, url, data=None, return_as_soup=False):
        try:
            encoded_data = urllib.parse.urlencode(data).encode() if data else None
            with self.opener.open(url, encoded_data) as response:
                if response.info().get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(response.read())
                else:
                    content = response.read()
                
                return content if not return_as_soup else BeautifulSoup(content, 'html.parser')
            
        except HTTPError as e:
            raise HTTPError(f"Request failed: {e}")

    def download_torrent(self, info):
        if USE_MAGNET_LINKS:
            return
        
        torrent_file = self._make_request(
            url=self.download_url, 
            data={"hid": info}
        )
        
        with tempfile.NamedTemporaryFile(suffix='.torrent', delete=False) as file:
            file.write(torrent_file)
        print(f"{file.name} {self.download_url}")

    def search(self, what, _):
        what = urllib.parse.quote(what)
        
        page_num = 1
        while True:
            response = self._make_request(
                url=f"{self.url}/query/{what}/page/{page_num}",
                data={'q': what,
                      'page': page_num},
                return_as_soup=True
            )

            num_results = self._parse_results(response)

            if num_results < self.torrents_per_page:
                return
            
            page_num += 1

    def _parse_results(self, soup):
        rows = soup.find_all('tr')

        torrents_found = 0
        for row in rows:
            torrent_data = self._extract_torrent_data(row)
            if torrent_data:
                prettyPrinter(torrent_data)
                torrents_found += 1

        return torrents_found
    
    def _extract_torrent_data(self, row):
        name_elem = row.find('a', onclick=lambda x: x and x.startswith('t9mov'))
        if not name_elem:
            return None

        size_elem = row.find('td', string=lambda x: x and any(unit in x for unit in ['KB', 'MB', 'GB', 'TB']))
        seeds_elem = row.find('td', style='font-size:13px;text-align:right; padding-right:5px')
        leech_elem = seeds_elem.find_next_sibling('td') if seeds_elem else None
        id_input = row.find('input', {'name': 'id'})

        torrent_id = id_input['value'] if id_input else None
        if not torrent_id:
            return None

        torrent_page = self._get_torrent_page(torrent_id)

        return {
            'name': name_elem.get_text(strip=True),
            'size': size_elem.get_text(strip=True) if size_elem else 'N/A',
            'seeds': seeds_elem.get_text(strip=True).split()[0] if seeds_elem else -1,
            'leech': leech_elem.get_text(strip=True).split()[0] if leech_elem else -1,
            'link': self._get_download_link(torrent_page),
            'desc_link': self.url,  # Placeholder, as actual desc_link requires a payload post req
            'engine_url': self.url
        }

    def _get_torrent_page(self, torrent_id):
        return self._make_request(
            self.torrent_page_url, 
            data={'id': torrent_id}, 
            return_as_soup=True
        )

    def _get_download_link(self, torrent_page):
        download_buttons = torrent_page.find_all('div', class_='download-btn')
        magnet_link = None
        hid = None

        # If a torrent file is not available
        # we need to fetch the magnet url instead
        for button in download_buttons:
            # Always look for magnet link
            magnet_anchor = button.find('a', href=lambda x: x and x.startswith('magnet:'))
            if magnet_anchor and not magnet_link:
                magnet_link = magnet_anchor['href']

            # Look for torrent link if USE_MAGNET_LINKS is False
            if not USE_MAGNET_LINKS:
                torrent_form = button.find('form', {'id': 'hashid'})
                if torrent_form:
                    hid_input = torrent_form.find('input', {'name': 'hid'})
                    if hid_input:
                        hid = hid_input['value']
                        break  # Exit loop if torrent link is found

        # Return links based on priority
        if USE_MAGNET_LINKS or (not USE_MAGNET_LINKS and not hid):
            return magnet_link if magnet_link else 'N/A'
        else:
            return hid




if __name__ == "__main__":
    engine = zooqle()
    engine.search("hey")