#!/usr/bin/env python

import json
import httplib
from urllib2 import Request, urlopen, URLError, HTTPError
import base64
import sys
import os
import logging
import urllib

KIBANA_SEARCH = 'https://sensu.yak.run/kibana/app/kibana#/discover?_g=(refreshInterval:(display:Off,pause:!f,value:0),time:(from:now-1h,mode:quick,to:now))&_a=(query:(query_string:(query:\'%s\')),sort:!(\'@timestamp\',desc))'
SEARCHES = {
    'production': 'deployment: "prd-01" AND message: error',
    'infra': 'deployment: "infra" AND message: error'
}
TIMEFRAME = '1h'

## exception class for SlackMessage
class SlackException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

## a class representing a slack message
class SlackMessage:
    header = ''
    text = ''
    __channel = ''
    __url = ''
    __color = 'good'

    def __init__(self,url,channel):
        self.__url = url
        self.__channel = channel

    def danger(self):
        self.__color = 'danger'

    def good(self):
        self.__color = 'good'

    def warning(self):
        self.__color = 'warning'

    def __to_o(self):
        return {
            'channel': self.__channel,
            'text': self.header,
            'attachments': [{
                'text': self.text,
                'color': self.__color,
                'mrkdwn_in': ['text', 'pretext']
            }]
        }

    def send(self):
        try:
            req = Request(self.__url, json.dumps(self.__to_o()))
            response = urlopen(req)
            response.read()
        except Exception as e:
            raise SlackException('unable to send slack message %s' % (e))

## the thing which is doing the work
def do_search(environment,query):
    auth = base64.encodestring('%s:%s' % (os.environ.get('USERNAME'), os.environ.get('PASSWORD'))).replace('\n', '')
    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Basic %s' % (auth)
    }
    body = {
        'query': {
            'bool': {
                'must': {
                    'query_string': {
                    'default_field': '_all',
                    'query': '%s' % (query)
                    }
                },
                'filter': {
                    'range': {
                        '@timestamp': {
                            'gte': 'now-%s' % (TIMEFRAME)
                        }
                    }
                }
            }
        }
    }
    conn = httplib.HTTPSConnection('sensu.yak.run')
    conn.request(method='GET', url='/esapi/_search', body=json.dumps(body), headers=headers)
    j = json.loads(conn.getresponse().read())
    lines = []
    for hit in j['hits']['hits']:
        date = hit['_source']['@timestamp']
        host = hit['_source']['host']
        source = hit['_source']['source']
        message = hit['_source']['message']
        lines.append('%s %s %s %s' % (date, host, source, message))
    if len(lines):
        slack = SlackMessage(os.environ.get('SLACK_HOOK_URL'),'#monitoring')
        slack.header = '*interesting log lines in the last %s*: %s' % (TIMEFRAME,environment)
        slack.warning()
        kibana = KIBANA_SEARCH % (urllib.quote_plus(query))
        slack.text = '<%s|kibana search>: %s\n```%s```' % (kibana,query,'\n'.join(lines))
        slack.send()

## MAIN ##

for key in SEARCHES.keys():
    do_search(key,SEARCHES[key])
