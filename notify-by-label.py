#!/usr/bin/env python

# notify-by-label (c) by Lee Webb (nullify005 at gmail dot com)
#
# notify-by-label is licensed under a
# Creative Commons Attribution-ShareAlike 4.0 International License.
#
# You should have received a copy of the license along with this
# work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.

from github import Github
from slacker import Slacker
import argparse
import sys
import logging
from urllib import quote

def get_gh_labels():
    g = Github(args.ghtoken)
    org = g.get_organization(args.ghorg)
    repo = org.get_repo(args.ghrepo)
    return repo.get_labels()

def get_pr_strs_for_label(label):
    ret = []
    g = Github(args.ghtoken)
    org = g.get_organization(args.ghorg)
    repo = org.get_repo(args.ghrepo)
    issues = g.search_issues('repo:%s/%s is:pr state:open label:"%s"' % (args.ghorg,args.ghrepo,label))
    if issues.totalCount == 0:
        return []
    for issue in issues:
        ipr = issue.pull_request
        pr_id = int(ipr.html_url.split('/')[-1])
        pr = repo.get_pull(pr_id)
        user = pr.user
        ret.append('<%s|%s> by %s @ %s' % (pr.html_url,pr.title,user.name,pr.created_at))
    return ret

## setup the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.info('starting')

## arg parser
parser = argparse.ArgumentParser(description='Scan all open Pull Requests and notify into Slack if there are reviews outstanding')
parser.add_argument('--ghtoken', dest='ghtoken', required=True, action='store', help='Github API Token')
parser.add_argument('--ghorg', dest='ghorg', default='TutoringAustralasia', action='store', help='Github Organisation')
parser.add_argument('--ghrepo', dest='ghrepo', default='eureka', action='store', help='Github Repository')
parser.add_argument('--stoken', dest='stoken', required=True, action='store', help='Slack API Token')
parser.add_argument('--schannel', dest='schannel', default='#general', action='store', help='Slack Channel')
parser.add_argument('--suser', dest='suser', default='prcalltoaction', action='store', help='Slack User')
parser.add_argument('--semoji', dest='semoji', default=':warning:', action='store', help='Slack Emoji Icon')
parser.add_argument('--verbose', dest='verbose', action='store_true', help='Increase Logging Verbosity')
args = parser.parse_args()

## setup the logger
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

## main
logging.info('Searching %s/%s for Pull Requests by Label' % (args.ghorg,args.ghrepo))
labels = get_gh_labels()
attachments = []
for label in labels:
    issues = get_pr_strs_for_label(label.name)
    logging.info('There are %d issues for label: %s' % (len(issues),label.name))
    if issues:
        search = 'repo:%s/%s is:pr state:open label:"%s"' % (args.ghorg,args.ghrepo,label.name)
        attachment = {
            'title': label.name,
            'title_link': 'https://github.com/search?q=%s' % (quote(search)),
            'color': '#%s' % (label.color),
            'text': '\n'.join(issues),
            'mrkdwn_in': ['text', 'pretext']
        }
        logging.debug('Appending: %s to attachments for label: %s' % (attachment,label.name))
        attachments.append(attachment)
if not attachments:
    logging.warning('nothing to do? chips')
    sys.exit(0)
logging.info('Sending slack message to channel: %s' % (args.schannel))
slack = Slacker(args.stoken)
slack.chat.post_message(
    args.schannel,
    text='@here Outstanding Pull Requests for Project <https://github.com/%s/%s/pulls|%s>' % (args.ghorg,args.ghrepo,args.ghrepo),
    parse=True,
    attachments=attachments,
    icon_emoji=args.semoji,
    username=args.suser
)
