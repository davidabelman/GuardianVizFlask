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
	print "======"
	print "Status for %s" %options.current_articles_path
	print "======"

	articles = load_pickle(filename = options.current_articles_path)
	cosine_similarities = load_pickle(filename = options.current_articles_path_cosine_similarites)

	# Number of articles crawled
	print "Articles crawled:", len(articles)

	# Date range for articles
	print "First article date:", min([articles[x]['date'] for x in articles])
	print "Latest article date:", max([articles[x]['date'] for x in articles])

	# Number of articles analysed for cosine similarity
	print "Cosine similarities calculated:", len(cosine_similarities)


