# -*- coding:utf8 -*-
import os
import re
import random

import requests


class Position(object):

    def __init__(self, payload):
        self.payload = payload
        self.name = payload['positionName'].encode('utf8')
        self.company = payload['companyShortName'].encode('utf8')
        self.id = payload['positionId']
        self.position_url = 'http://www.lagou.com/jobs/%s.html' % self.id

    @property
    def salary(self):
        if '-' not in self.payload['salary']:
            print self.payload['salary']
            return

        # 8K
        last_parts = self.payload['salary'].split('-')[-1]
        finded = re.search('(\d+)', last_parts)
        if finded:
            return int(finded.groups()[0])
        else:
            raise ValueError(last_parts)


class Lagou(object):

    def __init__(self):
        self.url = 'http://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false&px=new&city=%(city)s'
        self.httpclient = requests.Session()
        self.httpclient.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_%s)' % random.randint(1, 9)
        self.httpclient.headers['Referer'] = 'http://www.lagou.com/'
        self.httpclient.headers['Cookie'] = 'ser_trace_token=20150911211926-4ada397cfccc4ead84662514ea71bf95; LGUID=20150911211925-b96ca0d5-5887-11e5-8fa3-525400f775ce; tencentSig=3794087932; _qddab=3-cdbgnu.ip1va9ps; RECOMMEND_TIP=true; _putrc=2C12C4A7D498BD6F; login=true; unick=%E9%AB%98%E7%94%B0%E7%94%B0; LGMOID=20160724170536-A5144F994E878CDD333761195AE30E10; HISTORY_POSITION=2135316%2C30k-50k%2C%E4%B9%90%E5%88%BB%E8%BF%90%E5%8A%A8%2CCTO%7C1968205%2C20k-40k%2C%E8%9A%82%E8%9A%81%E9%87%91%E6%9C%8D%2C%E5%85%A8%E6%A0%88%E5%B7%A5%E7%A8%8B%E5%B8%88%7C2137766%2C25k-50k%2C%E6%A1%94%E5%88%A9%2C%E5%85%A8%E6%A0%88%E5%89%8D%E7%AB%AF%E5%BC%80%E5%8F%91%7C1903454%2C15k-30k%2C%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4%EF%BC%8D%E7%A5%9E%E9%A9%AC%E6%90%9C%E7%B4%A2%2C%E5%89%8D%E7%AB%AF%E5%BC%80%E5%8F%91%E5%B7%A5%E7%A8%8B%E5%B8%88%7C1970395%2C15k-30k%2C%E9%93%AD%E5%B8%88%E5%A0%82%E6%95%99%E8%82%B2%2C%E5%89%8D%E7%AB%AF%E5%B7%A5%E7%A8%8B%E5%B8%88%7C; JSESSIONID=CBCFF0A6C97AC877F3E9376ED569F749; ctk=1470539142; SEARCH_ID=bda15f66324c46a5a00ef863f01301b9; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1468159339; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1470539143; _gat=1; _ga=GA1.2.559660837.1441977566; LGSID=20160807110544-d51351ae-5c4b-11e6-83b5-525400f775ce; PRE_UTM=; PRE_HOST=; PRE_SITE=http%3A%2F%2Fwww.lagou.com%2Fjobs%2Flist_python%3Fcity%3D%25E6%259D%25AD%25E5%25B7%259E%26cl%3Dfalse%26fromSearch%3Dtrue%26labelWords%3D%26suginput%3D; PRE_LAND=http%3A%2F%2Fwww.lagou.com%2Fjobs%2Flist_java%3Fcity%3D%25E6%259D%25AD%25E5%25B7%259E%26cl%3Dfalse%26fromSearch%3Dtrue%26labelWords%3D%26suginput%3D; LGRID=20160807110544-d513534a-5c4b-11e6-83b5-525400f775ce'

    def _is_last_page(self, body):
        try:
            return body['content']['positionResult']['resultSize'] == 0
        except KeyError:
            raise Exception(body)

    def _get_result(self, body):
        return body['content']['positionResult']['result']

    def get_all(self, city, keyword, start_page=1, cls=None):
        """Get all position from lagou"""
        url = self.url % {'city': city}
        total = []
        page = start_page
        while True:
            data = 'pn=%s&kd=%s' % (page, keyword)
            print data
            body = self._do_post(url, data)
            if self._is_last_page(body):
                break
            else:
                total.extend(self._get_result(body))
                page = page + 1
        if cls:
            return [cls(pos) for pos in total]
        else:
            return total

    def _do_post(self, url, data):
        response = self.httpclient.post(url, data)
        response_body = response.json()

        if int(response.status_code) != 200:
            raise Exception(response.status_code)

        return response_body


class FileCache(object):

    def __init__(self, path):
        self._path = path
        self._cache = None

        dirname = os.path.dirname(self._path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def get(self):
        if self._cache:
            return self._cache

        if os.path.exists(self._path):
            content = open(self._path).read()
            self._cache = content
            return content

    def set(self, content):
        open(self._path, 'w').write(content)
        self._cache = content


class Sorter(object):

    def __call__(self, positions):
        self.sort(positions)

    def sort(self, positions):
        pass


class SalarySorter(Sorter):

    def sort(self, positions):
        return sorted(positions, key=lambda x: x.salary)


if __name__ == '__main__':
    lagou = Lagou()
    python = lagou.get_all('杭州', 'java', 123, Position)
    sorter = SalarySorter()
    for py in sorter.sort(python):
        print py.salary, py.name, py.company, py.position_url
