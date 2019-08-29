# github-utilities

A collection of Github utilities written in Python

## es_things_in_last_hour

This is a script which connects to an elastic search server (such as sensu)
and pulls entries for it matching a particular pattern in the last hour
then sends them into slack

The Jenkins job for this is here:

* https://see.yak.run/job/cron-jobs/job/elasticsearch-hourly-things/

## notify-by-label

This script looks at all the PR's in a given project based upon the label
name and then puts an alert into Slack reminding people to work on them.

It's a bit ass about because you can't look at the PR's and see the labels
in the github API, instead you have to get all the labels and then based on
which ones you want, do a search for the PR's which match the labels.

The Jenkins job for this is here:

* https://see.yak.run/job/cron-jobs/job/github-notify-by-label/
