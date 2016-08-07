# -*- coding:utf8 -*-
import re
import random
import collections

import requests


class Position(object):

    def __init__(self, payload):
        self.payload = payload
        self.name = payload['positionName'].encode('utf8')
        self.company = payload['companyShortName'].encode('utf8')
        self.id = payload['positionId']
        self.city = payload['city']
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
        self.url = 'http://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false&px=new'
        self.httpclient = requests.Session()
        self.httpclient.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_%s)' % random.randint(1, 9)
        self.httpclient.headers['Referer'] = 'http://www.lagou.com/'
        self.httpclient.headers['Cookie'] = 'JSESSIONID=18F853F0C7F4B3C3CECCD2B46C52FFDB; LGMOID=20160807111055-58A9677E97C8714E09FE1ABEC926DA69; ctk=1470540395; _gat=1; _ga=GA1.2.1928742054.1470540420; user_trace_token=20160807112700-cd932936-5c4e-11e6-83b5-525400f775ce; LGSID=20160807112700-cd932bf8-5c4e-11e6-83b5-525400f775ce; PRE_UTM=; PRE_HOST=; PRE_SITE=http%3A%2F%2Fwww.lagou.com%2Fjobs%2Flist_python%3Fcity%3D%25E6%259D%25AD%25E5%25B7%259E%26cl%3Dfalse%26fromSearch%3Dtrue%26labelWords%3D%26suginput%3D; PRE_LAND=http%3A%2F%2Fwww.lagou.com%2Fjobs%2Flist_java%3Fcity%3D%25E6%259D%25AD%25E5%25B7%259E%26cl%3Dfalse%26fromSearch%3Dtrue%26labelWords%3D%26suginput%3D; LGRID=20160807112700-cd932d45-5c4e-11e6-83b5-525400f775ce; LGUID=20160807112700-cd932da2-5c4e-11e6-83b5-525400f775ce; SEARCH_ID=ee2af34614b34d6babb923c362062887; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1468159339; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1470540434'

    def _is_last_page(self, body):
        try:
            return int(body['content']['pageNo']) == 0
        except KeyError:
            raise Exception(body)

    def _get_result(self, body):
        return body['content']['positionResult']['result']

    def _validate_body(self, body):
        if body['success'] == False:
            print body['msg']
            return False
        else:
            return True

    def get_all(self, keyword, city=None, start_page=1, max_page=50, cls=None):
        """Get all position from lagou"""
        url = self.url
        if city:
            url = url + '&city=%s' % city

        total = []
        page = start_page
        try:
            while True:
                if page > max_page:
                    break
                data = {
                    'pn': page,
                    'kd': keyword,
                }
                body = self._do_post(url, data)
                if not self._validate_body(body):
                    break

                if self._is_last_page(body):
                    break
                else:
                    total.extend(self._get_result(body))
                    page = page + 1
        except Exception as ex:
            print ex

        if cls:
            return [cls(pos) for pos in total]
        else:
            return total

    def _do_post(self, url, data):
        response = self.httpclient.post(url, data)

        if int(response.status_code) != 200:
            raise Exception(response.status_code)

        response_body = response.json()
        return response_body


class Sorter(object):

    def __call__(self, positions):
        self.sort(positions)

    def sort(self, positions):
        pass


class SalarySorter(Sorter):

    def sort(self, positions):
        return sorted(positions, key=lambda x: x.salary)


def get_line(radio=100):
    char = '▇'
    return char * int(100 * radio)


if __name__ == '__main__':
    lagou = Lagou()
    python = lagou.get_all('python', city='杭州', start_page=1, cls=Position)
    sorter = SalarySorter()
    counter = collections.defaultdict(lambda: 0)
    for py in sorter.sort(python):
        print py.salary, py.name, py.company, py.city, py.position_url
        counter[py.salary] = counter[py.salary] + 1
    print '-' * 30
    total = sum(counter.values())
    for k, v in counter.iteritems():
        percent = v / float(total)
        print '%2s: %s %s (%.2f)' % (k, get_line(percent),  v, percent)
