from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode, toUnicode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.event import fireEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.providers.base import MultiProvider
from couchpotato.core.providers.info.base import MovieProvider, SeasonProvider, EpisodeProvider
from couchpotato.core.providers.torrent.base import TorrentProvider
import traceback

log = CPLog(__name__)


class SceneAccess(MultiProvider):

    def getTypes(self):
        return [Movie, Season, Episode]


class Base(TorrentProvider):

    urls = {
        'test': 'https://www.sceneaccess.eu/',
        'login': 'https://www.sceneaccess.eu/login',
        'login_check': 'https://www.sceneaccess.eu/inbox',
        'detail': 'https://www.sceneaccess.eu/details?id=%s',
        'search': 'https://www.sceneaccess.eu/browse?c%d=%d',
        'archive': 'https://www.sceneaccess.eu/archive?&c%d=%d',
        'download': 'https://www.sceneaccess.eu/%s',
    }

    http_time_between_calls = 1 #seconds

    def _search(self, media, quality, results):

        url = self.buildUrl(media, quality)
        data = self.getHTMLData(url, opener = self.login_opener)

        if data:
            html = BeautifulSoup(data)

            try:
                resultsTable = html.find('table', attrs = {'id' : 'torrents-table'})
                if resultsTable is None:
                    return

                entries = resultsTable.find_all('tr', attrs = {'class' : 'tt_row'})
                for result in entries:

                    link = result.find('td', attrs = {'class' : 'ttr_name'}).find('a')
                    url = result.find('td', attrs = {'class' : 'td_dl'}).find('a')
                    leechers = result.find('td', attrs = {'class' : 'ttr_leechers'}).find('a')
                    torrent_id = link['href'].replace('details?id=', '')

                    results.append({
                        'id': torrent_id,
                        'name': link['title'],
                        'url': self.urls['download'] % url['href'],
                        'detail_url': self.urls['detail'] % torrent_id,
                        'size': self.parseSize(result.find('td', attrs = {'class' : 'ttr_size'}).contents[0]),
                        'seeders': tryInt(result.find('td', attrs = {'class' : 'ttr_seeders'}).find('a').string),
                        'leechers': tryInt(leechers.string) if leechers else 0,
                        'get_more_info': self.getMoreInfo,
                    })

            except:
                log.error('Failed getting results from %s: %s', (self.getName(), traceback.format_exc()))

    def getMoreInfo(self, item):
        full_description = self.getCache('sceneaccess.%s' % item['id'], item['detail_url'], cache_timeout = 25920000)
        html = BeautifulSoup(full_description)
        nfo_pre = html.find('div', attrs = {'id':'details_table'})
        description = toUnicode(nfo_pre.text) if nfo_pre else ''

        item['description'] = description
        return item

    # Login
    def getLoginParams(self):
        return tryUrlencode({
            'username': self.conf('username'),
            'password': self.conf('password'),
            'submit': 'come on in',
        })

    def loginSuccess(self, output):
        return '/inbox' in output.lower()

    loginCheckSuccess = loginSuccess


class Movie(MovieProvider, Base):

    cat_ids = [
        ([22], ['720p', '1080p']),
        ([7], ['cam', 'ts', 'dvdrip', 'tc', 'r5', 'scr', 'brrip']),
        ([8], ['dvdr']),
    ]

    def buildUrl(self, media, quality):
        url = self.urls['search'] % (
           self.getCatId(quality['identifier'])[0],
           self.getCatId(quality['identifier'])[0]
        )

        arguments = tryUrlencode({
            'search': fireEvent('searcher.get_search_title', media['library'], include_identifier = True, single = True),
            'method': 2,
        })
        query = "%s&%s" % (url, arguments)

        return query

class Season(SeasonProvider, Base):

    cat_ids = [
        ([26], ['hdtv_sd', 'hdtv_720p', 'webdl_720p', 'webdl_1080p']),
    ]

    def buildUrl(self, media, quality):
        url = self.urls['archive'] % (
           self.getCatId(quality['identifier'])[0],
           self.getCatId(quality['identifier'])[0]
        )

        arguments = tryUrlencode({
            'search': fireEvent('searcher.get_search_title', media['library'], include_identifier = True, single = True),
            'method': 2,
        })
        query = "%s&%s" % (url, arguments)

        return query

class Episode(EpisodeProvider, Base):

    cat_ids = [
        ([27], ['hdtv_720p', 'webdl_720p', 'webdl_1080p']),
        ([17, 11], ['hdtv_sd'])
    ]

    def buildUrl(self, media, quality):
        url = self.urls['search'] % (
           self.getCatId(quality['identifier'])[0],
           self.getCatId(quality['identifier'])[0]
        )

        arguments = tryUrlencode({
            'search': fireEvent('searcher.get_search_title', media['library'], include_identifier = True, single = True),
            'method': 2,
        })
        query = "%s&%s" % (url, arguments)

        return query