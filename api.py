# -*- coding: utf-8 -*-
"""
Songloft API 封装
对接 Songloft 自托管音乐服务器的 REST API
"""

import requests

DEFAULT_TIMEOUT = 15
API_PREFIX = '/api/v1'


class SongloftApi(object):
    def __init__(self, base_url, access_token=None):
        """
        :param base_url: Songloft 服务器地址，例如 http://192.168.1.100:58091
        :param access_token: JWT access token（登录后获取）
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        if access_token:
            self.session.headers.update({
                'Authorization': 'Bearer ' + access_token,
            })

    def set_token(self, access_token):
        """更新 Bearer Token"""
        if access_token:
            self.session.headers.update({
                'Authorization': 'Bearer ' + access_token,
            })

    def _url(self, path):
        return self.base_url + API_PREFIX + path

    def _get(self, path, params=None):
        try:
            resp = self.session.get(self._url(path), params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise SongloftException('无法连接到服务器，请检查服务器地址')
        except requests.exceptions.Timeout:
            raise SongloftException('连接超时，请检查网络')
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status == 401:
                raise SongloftException('认证失败，请重新登录')
            elif status == 403:
                raise SongloftException('权限不足')
            elif status == 404:
                raise SongloftException('资源不存在')
            raise SongloftException('请求失败：HTTP {}'.format(status))
        except Exception as e:
            raise SongloftException('请求异常：{}'.format(str(e)))

    def _post(self, path, data=None):
        try:
            resp = self.session.post(self._url(path), json=data, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise SongloftException('无法连接到服务器，请检查服务器地址')
        except requests.exceptions.Timeout:
            raise SongloftException('连接超时，请检查网络')
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status == 401:
                raise SongloftException('用户名或密码错误')
            raise SongloftException('请求失败：HTTP {}'.format(status))
        except Exception as e:
            raise SongloftException('请求异常：{}'.format(str(e)))

    # ------------------------------------------------------------------ #
    # 认证
    # ------------------------------------------------------------------ #

    def login(self, username, password):
        """
        登录并返回 tokens dict：
        {
            'access_token': str,
            'refresh_token': str,
            'expires_in': int,
            'token_type': 'Bearer'
        }
        """
        data = self._post('/auth/login', {'username': username, 'password': password})
        return data

    def refresh_token(self, refresh_token):
        """使用 refresh_token 刷新 access_token"""
        data = self._post('/auth/refresh', {'refresh_token': refresh_token})
        return data

    # ------------------------------------------------------------------ #
    # 歌曲
    # ------------------------------------------------------------------ #

    def get_songs(self, limit=50, offset=0, keyword=None, song_type=None):
        """
        获取歌曲列表
        :return: {'songs': [...], 'total': int}
        """
        params = {'limit': limit, 'offset': offset}
        if keyword:
            params['keyword'] = keyword
        if song_type:
            params['type'] = song_type
        return self._get('/songs', params=params)

    def get_song(self, song_id):
        """获取单首歌曲详情"""
        return self._get('/songs/{}'.format(song_id))

    def notify_played(self, song_id, play_type='finish'):
        """通知后端歌曲播放事件"""
        try:
            path = '/songs/{}/played'.format(song_id)
            self.session.post(
                self._url(path),
                params={'source': 'kodi', 'type': play_type},
                timeout=5,
            )
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 歌单
    # ------------------------------------------------------------------ #

    def get_playlists(self, limit=100, offset=0, playlist_type=None):
        """
        获取歌单列表
        :return: {'playlists': [...], 'total': int}
        """
        params = {'limit': limit, 'offset': offset}
        if playlist_type:
            params['type'] = playlist_type
        return self._get('/playlists', params=params)

    def get_playlist(self, playlist_id):
        """获取歌单详情"""
        return self._get('/playlists/{}'.format(playlist_id))

    def get_playlist_songs(self, playlist_id, limit=100, offset=0, keyword=None):
        """
        获取歌单内歌曲
        :return: {'songs': [...], 'total': int}
        """
        params = {'limit': limit, 'offset': offset, 'sort': 'position', 'order': 'asc'}
        if keyword:
            params['keyword'] = keyword
        return self._get('/playlists/{}/songs'.format(playlist_id), params=params)


class SongloftException(Exception):
    def __init__(self, message):
        self.message = message
        super(SongloftException, self).__init__(message)
