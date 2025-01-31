# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..utils import urlencode_postdata


class VierIE(InfoExtractor):
    IE_NAME = 'vier'
    IE_DESC = 'vier.be and vijf.be'
    _VALID_URL = r'https?://(?:www\.)?(?P<site>vier|vijf)\.be/(?:[^/]+/videos/(?P<display_id>[^/]+)(?:/(?P<id>\d+))?|video/v3/embed/(?P<embed_id>\d+))'
    _NETRC_MACHINE = 'vier'
    _TESTS = [{
        'url': 'http://www.vier.be/planb/videos/het-wordt-warm-de-moestuin/16129',
        'md5': 'e4ae2054a6b040ef1e289e20d111b46e',
        'info_dict': {
            'id': '16129',
            'display_id': 'het-wordt-warm-de-moestuin',
            'ext': 'mp4',
            'title': 'Het wordt warm in De Moestuin',
            'description': 'De vele uren werk eisen hun tol. Wim droomt van assistentie...',
        },
    }, {
        'url': 'http://www.vijf.be/temptationisland/videos/zo-grappig-temptation-island-hosts-moeten-kiezen-tussen-onmogelijke-dilemmas/2561614',
        'info_dict': {
            'id': '2561614',
            'display_id': 'zo-grappig-temptation-island-hosts-moeten-kiezen-tussen-onmogelijke-dilemmas',
            'ext': 'mp4',
            'title': 'md5:84f45fe48b8c1fa296a7f6d208d080a7',
            'description': 'md5:0356d4981e58b8cbee19355cbd51a8fe',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.vier.be/janigaat/videos/jani-gaat-naar-tokio-aflevering-4/2674839',
        'info_dict': {
            'id': '2674839',
            'display_id': 'jani-gaat-naar-tokio-aflevering-4',
            'ext': 'mp4',
            'title': 'Jani gaat naar Tokio - Aflevering 4',
            'description': 'md5:2d169e8186ae4247e50c99aaef97f7b2',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Requires account credentials',
    }, {
        # Requires account credentials but bypassed extraction via v3/embed page
        # without metadata
        'url': 'http://www.vier.be/janigaat/videos/jani-gaat-naar-tokio-aflevering-4/2674839',
        'info_dict': {
            'id': '2674839',
            'display_id': 'jani-gaat-naar-tokio-aflevering-4',
            'ext': 'mp4',
            'title': 'jani-gaat-naar-tokio-aflevering-4',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Log in to extract metadata'],
    }, {
        # Without video id in URL
        'url': 'http://www.vier.be/planb/videos/dit-najaar-plan-b',
        'only_matching': True,
    }, {
        'url': 'http://www.vier.be/video/v3/embed/16129',
        'only_matching': True,
    }]

    def _real_initialize(self):
        self._logged_in = False

    def _login(self, site):
        username, password = self._get_login_info()
        if username is None or password is None:
            return

        login_page = self._download_webpage(
            'http://www.%s.be/user/login' % site,
            None, note='Logging in', errnote='Unable to log in',
            data=urlencode_postdata({
                'form_id': 'user_login',
                'name': username,
                'pass': password,
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        login_error = self._html_search_regex(
            r'(?s)<div class="messages error">\s*<div>\s*<h2.+?</h2>(.+?)<',
            login_page, 'login error', default=None)
        if login_error:
            self.report_warning('Unable to log in: %s' % login_error)
        else:
            self._logged_in = True

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        embed_id = mobj.group('embed_id')
        display_id = mobj.group('display_id') or embed_id
        video_id = mobj.group('id') or embed_id
        site = mobj.group('site')

        if not self._logged_in:
            self._login(site)

        webpage = self._download_webpage(url, display_id)

        if r'id="user-login"' in webpage:
            self.report_warning(
                'Log in to extract metadata', video_id=display_id)
            webpage = self._download_webpage(
                'http://www.%s.be/video/v3/embed/%s' % (site, video_id),
                display_id)

        video_id = self._search_regex(
            [r'data-nid="(\d+)"', r'"nid"\s*:\s*"(\d+)"'],
            webpage, 'video id', default=video_id or display_id)
        application = self._search_regex(
            [r'data-application="([^"]+)"', r'"application"\s*:\s*"([^"]+)"'],
            webpage, 'application', default=site + '_vod')
        filename = self._search_regex(
            [r'data-filename="([^"]+)"', r'"filename"\s*:\s*"([^"]+)"'],
            webpage, 'filename')

        playlist_url = 'http://vod.streamcloud.be/%s/_definst_/mp4:%s.mp4/playlist.m3u8' % (application, filename)
        formats = self._extract_wowza_formats(playlist_url, display_id, skip_protocols=['dash'])
        self._sort_formats(formats)

        title = self._og_search_title(webpage, default=display_id)
        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }


class VierVideosIE(InfoExtractor):
    IE_NAME = 'vier:videos'
    _VALID_URL = r'https?://(?:www\.)?(?P<site>vier|vijf)\.be/(?P<program>[^/]+)/videos(?:\?.*\bpage=(?P<page>\d+)|$)'
    _TESTS = [{
        'url': 'http://www.vier.be/demoestuin/videos',
        'info_dict': {
            'id': 'demoestuin',
        },
        'playlist_mincount': 153,
    }, {
        'url': 'http://www.vijf.be/temptationisland/videos',
        'info_dict': {
            'id': 'temptationisland',
        },
        'playlist_mincount': 159,
    }, {
        'url': 'http://www.vier.be/demoestuin/videos?page=6',
        'info_dict': {
            'id': 'demoestuin-page6',
        },
        'playlist_mincount': 20,
    }, {
        'url': 'http://www.vier.be/demoestuin/videos?page=7',
        'info_dict': {
            'id': 'demoestuin-page7',
        },
        'playlist_mincount': 13,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        program = mobj.group('program')
        site = mobj.group('site')

        page_id = mobj.group('page')
        if page_id:
            page_id = int(page_id)
            start_page = page_id
            playlist_id = '%s-page%d' % (program, page_id)
        else:
            start_page = 0
            playlist_id = program

        entries = []
        for current_page_id in itertools.count(start_page):
            current_page = self._download_webpage(
                'http://www.%s.be/%s/videos?page=%d' % (site, program, current_page_id),
                program,
                'Downloading page %d' % (current_page_id + 1))
            page_entries = [
                self.url_result('http://www.' + site + '.be' + video_url, 'Vier')
                for video_url in re.findall(
                    r'<h[23]><a href="(/[^/]+/videos/[^/]+(?:/\d+)?)">', current_page)]
            entries.extend(page_entries)
            if page_id or '>Meer<' not in current_page:
                break

        return self.playlist_result(entries, playlist_id)
