# -*- encoding: utf-8 -*-
import time 
import base64
import requests
import os
import json
import sys
import urllib
import string
import random
import re
import oauth2
from os import listdir, makedirs, remove
from os.path import isfile, join, exists
from pprint import pprint
from shutil import copyfile
from shutil import rmtree

consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""

source_directory = "./tweets"
dest_directory = "./temp"
log_directory = "./log"

if not exists(log_directory):
	makedirs(log_directory)

if exists(dest_directory):
	rmtree(dest_directory)

makedirs(dest_directory)

def log(msg, filename):
	path = "{0}/{1}".format(log_directory, filename)
	if exists(path):
		with open(path, "a") as f:
			f.write(msg)
	else:
		with open(path, "w") as f:
			f.write(msg)

def oauth_req(url, http_method = "GET", post_body = "", http_headers = None):
    consumer = oauth2.Consumer(key = consumer_key, secret = consumer_secret)
    token = oauth2.Token(key = access_key, secret = access_secret)
    client = oauth2.Client(consumer, token)
    resp, content = client.request(url, method = http_method, body = post_body, headers = http_headers)
    return json.loads(content)

def destroy_tweet(id):
	base_url = "https://api.twitter.com/1.1/statuses/destroy/{0}.json?".format(id)
	headers = dict(accept="application/json")

	payload = dict(
		trim_user = "true"
	)

	url = base_url + "trim_user={trim_user}".format(**payload)
	
	return oauth_req(url, http_headers = headers, http_method = "POST")

log("Starting up!\n", "startup.log")

month_files = [join(source_directory, f) for f in listdir(source_directory) if isfile(join(source_directory, f)) and "js" in f]

log("Found {0} month files.\n".format(len(month_files)), "startup.log")

# Json conversion
for month_file in month_files:
	if exists("{0}/{1}{2}".format(log_directory, month_file[month_file.index('s/') + 2:month_file.index('.js')], ".log")):
		continue

	with open(month_file, "r") as f:
		log("Converting file {0} to ".format(f.name), "startup.log")
		lines = f.readlines()		

	with open("{0}/{1}{2}".format(dest_directory, month_file[month_file.index('s/') + 2:month_file.index('.js')], ".json"), "w") as f:
		log("{0}\n".format(f.name), "startup.log")
		for line in lines[1:]:
			f.write(line)
		f.close()

dest_files = [join(dest_directory, f) for f in listdir(dest_directory) if isfile(join(dest_directory, f)) and "json" in f]
total_count = 0

log("Starting tweets processing\n".format(len(month_files)), "startup.log")

# Json reading
for dest_file in dest_files:
	log_name = "{0}{1}".format(dest_file[dest_file.index("p/") + 2:dest_file.index(".json")], ".log")
	with open(dest_file, "r") as f:
		data = json.load(f)
		log("Processing file \'{0}\': {1} tweets found...\n".format(dest_file, len(data)), log_name)
		count = 0
		for tweet in data:
			log("Processing tweet {0} of {1} - ID: {2} - ".format(count + 1, len(data), tweet["id"]), log_name)
			ans = destroy_tweet(tweet["id"])
			if "errors" in ans:
				if int(ans["errors"][0]["code"]) == 144:
					log("OK\n", log_name)
				else:
					log("Error {0}: {1}\n".format(ans["errors"][0]["code"], ans["errors"][0]["message"]), log_name)
			else:
				log("OK\n", log_name)
			count = count + 1
		total_count = total_count + len(data)

rmtree(dest_directory)

# Error correction
log_files = [join(log_directory, f) for f in listdir(log_directory) if isfile(join(log_directory, f)) and "log" in f]

for log_file in log_files:
	with open(log_file, "r") as f:
		lines = f.readlines()
		for line in lines:
			if "Error" in line:
				words = line.split()
				tweet_id = words[7]
				ans = destroy_tweet(tweet_id)
				print ans