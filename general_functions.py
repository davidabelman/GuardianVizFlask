# -*- coding: utf-8 -*-
"""
general_functions.py
General functions used within project
"""


def load_pickle(filename, silent = False):
	"""
	Loads pickle and prints to screen
	"""
	import pickle
	if not silent:
		print "Loading pickle (%s)" %(filename)
	try:
		return pickle.load( open( filename, "rb" ) )
	except:
		print "Error loading pickle."

def save_pickle(data, filename, silent = False):
	"""
	Saves pickle and prints to screen
	"""
	import pickle
	if not silent:
		print "Saving pickle (%s)" %(filename)
	pickle.dump( data, open( filename, "wb" ) )

def write_to_python_module(data, variable_name, filename, silent = False):
	"""
	Saves a variable to a python module
	"""
	f = open(filename, 'w')
	f.write('import datetime\n')
	f.write('%s = %s' %(variable_name, str(data)))
	f.close()
	if not silent:
		print "Saving file (%s)" %(filename)

def export_dict_to_json(data, path):
	"""
	Write a python element to JSON
	"""
	import json
	j = json.dumps(data)
	with open(path, 'w') as file_to_write:
		file_to_write.write(j)
	print "Exported JSON (%s)" %(path) 

def convert_str_to_date(string):
	"""
	Converts a string of format u'2013-06-24T23:06:02Z' into datetime.date (ignores time)
	"""
	from time import mktime, strptime
	from datetime import datetime
	struct = strptime(string[0:10], "%Y-%m-%d")
	dt = datetime.fromtimestamp(mktime(struct))
	return dt

def convert_datetime_to_str(dt):
	"""
	Converts datetime to str in format 2014-7-4
	"""
	import datetime
	return "%s-%s-%s" %(dt.year, dt.month, dt.day)

def create_REST_request(main, parameters = []):
	"""
	Appends a list of parameters to a URL separating all with & sign.
	Output something like this:
	http://beta.content.guardianapis.com/world?api-key=explorer&page-size=76&order-by=oldest&use-date=published&show-tags=keyword&show-elements=all&show-story-package=true&show-related=true&show-most-viewed=true&show-fields=standfirst%2Cthumbnail%2Cbyline%2Cheadline%2Cbody
	"""
	for p in parameters:
		main += p+"&"
	print "Generated the following request: %s" %(main[:-1])
	return main[:-1]

def create_stopword_list(extra_words):
	"""
	Creates stopword list (adds extra words to original English set)
	"""
	from sklearn.feature_extraction.text import TfidfVectorizer
	original = list(TfidfVectorizer.get_stop_words(TfidfVectorizer(stop_words='english')))
	if extra_words:
		return frozenset(original+extra_words)
	else:
		return frozenset(original)

def convert_dict_to_list(dictionary):
	return [dictionary[key] for key in dictionary]

def find_articles_by_tag(articles, tag_list, all_tags_required=True):
	"""
	Given articles (list of dict) and list of tags, export list of articles which match all tags or any tag
	"""
	return_list = []
	# Convert articles to list if they are currently in dict form
	if type(articles)== dict:
		articles = convert_dict_to_list(articles)
	# Convert a string into a list, assumes the string is one tag
	if type(tag_list) == str:
		tag_list = [tag_list]
		print "Tag list was provided as a string: assuming just one tag. Please supply in list format if more than one tag."
	# Loop through articles and add each one if it meets conditions
	for a in articles:
		try:
			article_tags = a['tags']
		except:
			print "ERROR - this should be an article:"
			print a
		number_of_tags_provided = len(tag_list)
		crossover = [x in article_tags for x in tag_list]  # results in list of [True, False, True, True] for tags provided
		if all_tags_required:
			if sum(crossover) == number_of_tags_provided:
				return_list.append(a)
		else:
			if sum(crossover) > 0:
				return_list.append(a)
	return return_list

def print_current_status():
	"""
	Print current status on path defined by options.current_articles_path
	"""
	import options	
	reload(options)
	print "======"
	print "Status for %s" %options.current_articles_path
	print "======"

	articles = load_pickle(filename = options.current_articles_path)
	cosine_similarities = load_pickle(filename = options.current_articles_path_cosine_similarites)

	# Number of articles crawled
	print "\nArticles crawled:", len(articles)

	# Date range for articles
	print "\nFirst article date:", min([articles[x]['date'] for x in articles])
	print "Latest article date:", max([articles[x]['date'] for x in articles])

	# Number of articles analysed for cosine similarity
	print "\nCosine similarities calculated:", len(cosine_similarities)

	# Number of articles by month
	dates = [str(articles[x]['date'].year)+'-'+str(articles[x]['date'].month).zfill(2) for x in articles]
	dates_unique = list(set(dates))
	dates_unique.sort()
	print "\nArticles crawled by month"
	for d in dates_unique:
		print "%s: %s articles" %(d, dates.count(d))

	# Number of World articles by month
	dates = [str(articles[x]['date'].year)+'-'+str(articles[x]['date'].month).zfill(2) for x in articles if 'World news' in articles[x]['tags']]
	dates_unique = list(set(dates))
	dates_unique.sort()
	print "\nWORLD articles crawled by month"
	for d in dates_unique:
		print "%s: %s articles" %(d, dates.count(d))

	# Number of UK articles by month
	dates = [str(articles[x]['date'].year)+'-'+str(articles[x]['date'].month).zfill(2) for x in articles if 'UK news' in articles[x]['tags']]
	dates_unique = list(set(dates))
	dates_unique.sort()
	print "\nUK articles crawled by month"
	for d in dates_unique:
		print "%s: %s articles" %(d, dates.count(d))

	# FB shares pulled
	dates = [str(articles[x]['date'].year)+'-'+str(articles[x]['date'].month).zfill(2) for x in articles if type(articles[x]['facebook']['snapshot_of_total'])==int]
	dates_unique = list(set(dates))
	dates_unique.sort()
	print "\nFB shares crawled by month"
	for d in dates_unique:
		print "%s: %s articles" %(d, dates.count(d))


def search_guardian_by_query(
		query,
		articles,
		pickle_or_database = 'pickle',
		start_date='2012-01-01',
		end_date='2015-01-01',
		section='world',
		guardian_page_size=100,
		return_number=10):
	"""
	Given query, a start date string, an end date string, a section (i.e. 'world')
	Also given articles dict of all articles (to check if we have each result saved)
	  e.g. load_pickle('../open/data/articles.p')
	Returns list of articles (and their headlines, etc.) for which we have data saved
	Format is:
	[{'date': u'2014-02-13T18:47:52Z',
	  'headline': u'Execution of Arab Iranian poet Hashem Shaabani condemned by rights groups',
	  'id': u'world/2014/feb/13/iran-middleeast',
	  'standfirst': u'Poet and leading member of banned cultural organisation run by Ahwazi Arab minority reported hanged after public confession'},
	 {'date': u'2014-02-18T19:21:00Z',
	  'headline': u"Iran won't discuss military programme, say officials",
	  'id': u'world/2014/feb/18/mohammad-javad-zarif-iran-political-will-final-nuclear-agreement',
	  'standfirst': u"Iran's foreign minister and senior negotiator say only nuclear issues will be discussed as next round of talks begins in Vienna"}]
	Process:
	Forms query string
	Requests a search from Guardian API and receives results
	Filters results for ones that we have within our database/pickle
	Picks out X (return_number) according to relevance ordering from Guardian
	Reorder by date
	"""
	from urllib import quote_plus as clean_url
	import urllib2
	import json

	# Query format
	# "http://content.guardianapis.com/search?api-key=test&page-size=100&q=germany%20football§ion=world&from-date=2014-01-01&to-date=2014-10-27"
	
	main = 'http://content.guardianapis.com/search?'
	parameters = [
		'api-key=uu4qhyqqknrkhrsmahfwr2qs',
		'page-size=%s' %guardian_page_size, 
		'q=%s' %clean_url(query),		
		'from-date=%s' %start_date,
		'to-date=%s' %end_date,
		# 'show-fields=standfirst'
	]
	if section:
		parameters.append('section=%s' %section)
	request = create_REST_request(main, parameters)
	response = urllib2.urlopen(request).read()
	page_data = json.loads(response);
	try:
		article_set = page_data['response']['results']
	except:
		print "Failed to retrieve result set."
		return None
	print "Received %s results from Guardian." %page_data['response']['total']
	print article_set

	# Check if each article is in articles pickle / in database (TODO: currently pickle)
	if pickle_or_database == 'pickle':
		filtered_article_set = [x for x in article_set 
								# Only show if in articles file
								if x['id'] in articles
								# Only show if 2+ articles in future_articles list
								if len(articles[x['id']]['f'])>=2]		
	elif pickle_or_database == 'database':
		# TODO
		None
	print "\nThese are the articles we have saved data for previously:"
	print filtered_article_set

	# Reduce to the number that we want to return to user, if we have more than this
	short_article_set = filtered_article_set[0:return_number]

	# Sort by date
	sorted_article_set = sorted(short_article_set, key=lambda x: x['webPublicationDate'])
	print "\nThis is the article set sorted by date:"
	print sorted_article_set

	# Return in correct format
	return [{
		'id':x['id'],
		'headline':x['webTitle'].replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"'),
		'date':x['webPublicationDate']
	} for x in sorted_article_set]

# cosine_similarity_matrix = load_pickle('../open/data/articles_cosine_similarities.p')
# r = search_guardian_by_query(
# 	query = 'china democracy',
# 	cosine_similarity_matrix = cosine_similarity_matrix,
# 	start_date='2013-01-01',
# 	end_date='2014-03-01',
# 	guardian_page_size=100
# 	)
