# -*- coding:utf8 -*-
import argparse
import re
import random
import collections

import requests
from terminaltables import AsciiTable


def chinese(string):
    return string.encode('utf8')


class Position(object):

    def __init__(self, payload):
        self.payload = payload
        self.create_time = chinese(payload['createTime'])
        self.name = chinese(payload['positionName'])
        self.company = chinese(payload['companyShortName'])
        self.id = payload['positionId']
        self.city = chinese(payload['city'])
        self.position_url = 'http://www.lagou.com/jobs/%s.html' % self.id

    @property
    def salary(self):
        raw = self.payload['salary']
        if u'以上' in raw:
            finded = re.search('(\d+)', raw)
            return int(finded.groups()[0])

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

    def _get_total_count(self, body):
        return body['content']['positionResult']['totalCount']

    def _validate_body(self, body):
        if body['success'] == False:
            print body['msg']
            return False
        else:
            return True

    def get_all(self, keyword, city=None, start_page=1, max_page=50, cls=None):
        """Get all position from lagou"""
        print "%s in city: %s" % (keyword, city)
        url = self.url
        if city:
            url = url + '&city=%s' % city

        total = []
        total_count = 0
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
                    total_count = self._get_total_count(body)
                    total.extend(self._get_result(body))
                    page = page + 1
        except Exception as ex:
            print ex

        print 'Position desired count: %s' % total_count
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


def get_line(radio=1):
    char = '▇'
    length = int(100 * radio)
    if length < 1:
        return '|'
    else:
        return char * length


class Counter(object):

    def __init__(self):
        self._counter = collections.defaultdict(lambda: 0)

    def increase(self, name):
        self._counter[name] += 1

    def sum(self):
        return sum(self._counter.values())

    def print_stats_graph(self, reverse=False):
        total = self.sum()
        for key in sorted(self._counter.keys(), reverse=reverse):
            value = self._counter[key]
            percent = value / float(total)
            print '%3s: %s %s (%.2f%%)' % (key, get_line(percent),  value, percent * 100)


def parse_argv():
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keyword', required=True)
    parser.add_argument('-c', '--city')
    parser.add_argument('-p', '--page', type=int, default=1)
    parser.add_argument('-s', '--sort', default='salary', help="[salary, time]")
    parser.add_argument('-o', '--company-stats', action='store_true')
    return parser.parse_args()


def get_sort_key(args):
    if args.sort == 'time':
        return lambda x: x.create_time
    else:
        return lambda x: x.salary


if __name__ == '__main__':
    args = parse_argv()
    lagou = Lagou()
    positions = lagou.get_all(args.keyword, city=args.city, start_page=args.page, cls=Position)

    # position lists
    sort_key = get_sort_key(args)
    positions = sorted(positions, key=sort_key)

    salary_counter = Counter()
    city_counter = Counter()
    company_counter = Counter()

    table_datas = [
        ['#', 'K', 'name', 'company', 'city', 'time', 'link']
    ]
    for index, pos in enumerate(positions):
        salary_counter.increase(pos.salary)
        city_counter.increase(pos.city)
        company_counter.increase(pos.company)

        table_datas.append([
            index + 1, pos.salary, pos.name, pos.company, pos.city, pos.create_time, pos.position_url
        ])

    print AsciiTable(table_datas).table

    print '[-] Position Total: %s' % len(positions)

    print '[-] City distribute:'
    print '=' * 80
    city_counter.print_stats_graph()

    print '[-] Salary distribute:'
    print '=' * 80
    salary_counter.print_stats_graph()

    if args.company_stats:
        print '[-] Company distribute'
        company_counter.print_stats_graph()
