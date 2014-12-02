"""
==============================
Butterfly effect visualisation
==============================

Notes:
1) Similarity value found between all pairs of articles based on tag, headline, and strapline. These are found by cosine similarity, and pairwise values are stored [TODO: either in a sparse matrix form, if we can store this within Flask, or in a database if we have to...]. We only need to store values if they are above a certain threshold. These are all calculated on a one off basis at first, and as new articles are crawled, we need to calculate pairwise similarity with all existing articles and store these values. Note that for each value stored, we need to store it either within 'future_articles' or 'past_articles'.

1b) Once similarity matrix created as a pickle, along with article matrix, we can run a function to reduce the size of these:
	--> articles pickle turned to articles_butterzip pickle (only stores the relevant information in the file), and saved as a python module
	--> cosine_sim_matrix turned to cosine_sim_matrix_butterzip pickle (uses lookup codes instead of ID), and then saved as python module

2) For all similar articles (say 20 of them) we run some type of clustering [TODO: topic analysis, LDA, or K-means] and form 2 or 3 topics of similar articles. Number of topics may depend on how many similar articles there are.

3) For each topic we want to select the most relevant article to display to the user. This should be based on its PageRank, its Facebook shares, and its date. Details to be decided...
"""

import time
import sys
import re
WORD = re.compile(r'\w+')
import math
import pprint
from collections import Counter
import options
import datetime
import general_functions
stopwords = general_functions.create_stopword_list(extra_words = options.tfidf_extra_stopwords)
debug = True


###### CREATING THE COSINE DICTIONARY #########
def get_cosine(vec1, vec2):
    """
    Gets cosine similarity between 2 dicts
    Form of input is: {'word1':4, 'word2':2...}
    """
    # Variables must be Counters of the form {'word1':4, 'word2':2...}
    
	# Calculate numerator (return 0 if no intersection)
    intersection = set(vec1.keys()) & set(vec2.keys())
    if len(intersection)<5:
    	return 0  # Avoid unecessary further calculation...
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    # Calculate denominator
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def count_terms(word_list):
	"""
	Creates a counter dictionary of terms, e.g. {'word1':4, 'word2':2...}
	Input is a list
	"""
	assert type(word_list)==list, "Input must be a list. We have %s" %(word_list)
	return Counter(word_list)

def string_to_list(string):
	"""
	Convert string to list
	'a string of words' --> ['a', 'string', 'of', 'words']
	"""
	return WORD.findall(string)

def remove_stopwords_and_convert_lower_case(l):
	"""
	Remove stopwords from a list
	"""
	return [x.lower() for x in l if x not in stopwords]

def compare_dates(date1, date2):
	"""
	Given 2 dates, compare if date2 is in the future or past
	Return 'future' or 'past'
	"""
	assert type(date1)==datetime.datetime and type(date2)==datetime.datetime
	if date2>date1:
		return 'future'
	else:
		return 'past'

def article_type_is_bad(id_str):
	"""
	Checks id_str (ID, e.g. 'world/gallery/2013/aug/19/pipe-band-championship-2013-glasgow') for banned terms, such as 'gallery', 'video', etc.
	Returns True if any banned terms found...
	"""
	check = id_str#[0:30]  # Take only first part of ID
	#TODO:make into regex
	banned_terms = ['video', 'gallery', 'picture', 'interactive', 'commentisfree', 'blog', 'live', 'shortcuts']
	# Check each banned term
	for x in banned_terms:
		if x in check:
			return True
	# If no banned terms found
	else:
		return False

def create_vector_from_article(article, include_standfirst=False):
	"""
	Convert an article (which is a dictionary with keys of 'standfirst', 'tags', 'headline') into a count of terms within the values of these keys
	Output dictionary of counts
	Note that stopwords are removed and everything is converted to lowercase
	Example
	Input = {'headline':'John Major is grey', 'standfirst':'John Major really is', 'tags':'Major'}
	Output = {'John':2, 'Major':3, 'grey':1, 'really':1}
	"""
	headline = string_to_list(article['headline'])	
	tags = article['tags']
	if include_standfirst:
		standfirst = string_to_list(article['standfirst'])

	# Remove stopwords from headline and standfirst
	headline = remove_stopwords_and_convert_lower_case(headline)
	tags = remove_stopwords_and_convert_lower_case(tags)
	if include_standfirst:
		standfirst = remove_stopwords_and_convert_lower_case(standfirst)

	# Create list of all headline, standfirst and tags and count...
	return count_terms(headline+tags)
	if include_standfirst:
		return count_terms(headline+standfirst+tags)
	 

def create_cosine_similarity_pickle_all_articles(threshold=0.5, incremental_add=True):
	"""
	Create cosine similarity matrix for all articles currently existing
	Should only need to be run once (we can then add to it incrementally)
	Pickle will be saved to disk.
	Form of matrix is:
	{'article1': 
		{'past_articles':
			{'article5':0.71,
			 'article14': 0.88,
			 ...
			 }
		},
		{'future_articles':
			{'article9':0.99,
			 'article29': 0.73,
			 ...
			 }
		},
	}
	"""
	if incremental_add == False:
		# Everything will be recalculated from afresh
		# Check we want to overwrite the main pickle (will take a long time...)
		print "WARNING: Are you sure you wish recalculate all cosine similarity values??"
		print "This will overwrite all previous values and may take a long time."
		print "We will use *%s* as the article set." %options.current_articles_path
		print "If not, set incremental_add to True: this will only calculate new cosine pairs."
		print "Press 'y' to continue..."
		u = raw_input('>> ')
		if u!='y':
			print "** CANCELLED **"
			return None
		print "Creating cosine similarity matrix using %s" %options.current_articles_path

		# Empty variable to fill
		cosine_similarity_matrix = {}  # To fill with whole matrix

	elif incremental_add==True: 
		# We will only add the new articles and calculate pairs involving these
		cosine_similarity_matrix = general_functions.load_pickle(filename = options.current_articles_path_cosine_similarites)  # To add incremental articles to
		if cosine_similarity_matrix == None:
			print "-- WARNING: could not load similarity matrix. Does it exist already or do we need to switch off incremental mode (i.e. create new matrix)?\n"
			sys.exit()

	# Start timer
	t1 = time.time()

	# Load articles and start counter	
	articles = general_functions.load_pickle(options.current_articles_path)
	total_number = len(articles)
	counter = 0
	print "We have %s articles to loop through." %total_number

	# Loop through all articles in main collection	
	for id1 in articles:
		counter+=1
		print "Article %s/%s" %(counter, total_number)

		# Skip if article already in the cosine_similarity_matrix
		if id1 in cosine_similarity_matrix:
			print "Skipping article, already analysed"
			continue

		# Skip if article is not of type we like
		if article_type_is_bad(id1):
			print "Skipping article, bad type"
			continue

		# Load article
		article1 = articles[id1]
		article1_cosine_similarities = {'future_articles':{}, 'past_articles':{}}  # To fill with 1 row

		# Create vector (dict of counts) for the article
		article1_vector = create_vector_from_article(article1)
		if debug:			
			print "================================"
			print "article1:"
			print "Headline:", article1['headline']
			print "Tags:", article1['tags']		
			print "Vector created:", article1_vector

		# Loop through all second articles
		for id2 in articles:
			if id1==id2:
				continue
			if article_type_is_bad(id2):
				continue

			# Load article
			article2 = articles[id2]

			# Create vector (dict of counts) for the second article
			article2_vector = create_vector_from_article(article2)			
			if debug:
				print ""
				print "-- article2:"
				print "-- Headline:", article2['headline']
				print "-- Tags:", article2['tags']		
				print "-- Vector created:", article2_vector

			# Calculate crossover
			cosine = get_cosine(article1_vector, article2_vector)
			if debug:
				print "---- Cosine = %s" %cosine
			
			# Ignore second article if too low crossover
			if cosine<threshold:				
				if debug:
					print "---- Not storing, cosine too low"
				continue

			# Store in collection if crossover is over threshold
			# Stored as integer (/100) as saves 25% space
			date1, date2 = article1['date'], article2['date']
			future_or_past = compare_dates(date1, date2)
			cosine = int(cosine*100)

			if future_or_past=='future':
				article1_cosine_similarities['future_articles'][id2] = cosine
			elif future_or_past=='past':
				article1_cosine_similarities['past_articles'][id2] = cosine

			# Also add to corresponding 'other' article if it exists in the matrix already
			# Note that past/future are swapped, as we are comparing swapped dates to the above
			if id2 in cosine_similarity_matrix:
				if future_or_past=='future':
					cosine_similarity_matrix[id2]['past_articles'][id1] = cosine
				elif future_or_past=='past':
					cosine_similarity_matrix[id2]['future_articles'][id1] = cosine

		# Now we have looped through all articles, we add the line for id1 to our overall matrix
		cosine_similarity_matrix[id1] = article1_cosine_similarities
		if debug:
			print "======\n====="
			print "THIS IS THE SIMILARITY MATRIX LINE"
			pprint.pprint(cosine_similarity_matrix)

		# Save the pickle every 100 additions
		if counter%30==0:
			general_functions.save_pickle(data = cosine_similarity_matrix, filename = options.current_articles_path_cosine_similarites)

	# End for statement looping over id1. Save pickle.
	general_functions.save_pickle(data = cosine_similarity_matrix, filename = options.current_articles_path_cosine_similarites)
	
	# End timer
	t2 = time.time()
	print "TOTAL TIME:", t2 - t1


###### CREATING THE BUTTERZIP FILES #########
# These are modules containing all article and cosine_matrix information in reasonably compressed form...
def create_butterzip_files():
	""""
	1) Creates articles_butterzip.p and articles_butterzip.py:
		... these only contain articles in the cosine_similarity_matrix
		... these only contain fields used in the butterfly viz (id, headline, strapline, image, date) 
	2) Creates cosine_similarity_matrix_butterzip, which is a copy of cosine_similarity_matrix but uses simpler IDs (from lookup). Also need to create the lookup both ways for this.
	"""
	print "Creating butterzip files..."

	# Load main articles and cosine similarites pickles created previously
	articles = general_functions.load_pickle(filename = options.current_articles_path)
	cosine_similarity_matrix = general_functions.load_pickle(filename = options.current_articles_path_cosine_similarites)

	# 1) Create new articles (articles_butterzip)
	articles_butterzip = {}
	for id_ in cosine_similarity_matrix:
		article_barebones = {
			'headline':articles[id_]['headline'],
			'standfirst':articles[id_]['standfirst'],
			'date':articles[id_]['date'],
			'thumbnail':articles[id_]['thumbnail'],
			'tags':articles[id_]['tags']
		}
		articles_butterzip[id_] = article_barebones
	# Save this as a pickle and a file
	general_functions.save_pickle(
		data = articles_butterzip, 
		filename = options.current_articles_path_butterzip)
	general_functions.write_to_python_module(
		data = articles_butterzip,
		variable_name = 'articles',
		filename = '../flask/articles_butterzip.py')

	# 2) Create simpler ID version of cosine_similarity_matrix
	# TODO: for now, just saving as a Python module
	general_functions.write_to_python_module(
		data = cosine_similarity_matrix,
		variable_name = 'cosine_similarity_matrix',
		filename = '../flask/cosine_similarity_matrix_butterzip.py')

def create_python_file():
	l = [1,2,3,4]
	f = open('testing.py', 'w')
	f.write(str(l))
	f.close()


###### SELECTING TOP RELATED ARTICLES #########
"""
Given article IDs
Apply any filters (e.g. only want to look at certain date range from original)
If 3 or fewer articles just return the article IDs, or top scored one
If 4-8 articles use K=2
If 9+ articles use K=3
Perform K-means clustering on the articles with K set as above
"""

def play_with_related_articles(a=None, m=None):
	"""
	Explore related articles in the terminal...
	NB: messy code!
	"""
	if a==None and m==None:
		a=general_functions.load_pickle('data/articles.p')
		m=general_functions.load_pickle('data/articles_cosine_similarities.p')
	id_ = raw_input('Enter initial article ID. Leave blank to start with early NSA. >> ')
	if id_=='':
		id_ = 'world/2013/jun/09/nsa-prism-uk-government'
	future_or_past = raw_input('Look into the future (f) or past (p)? >> ')
	future_or_past = future_or_past[0].lower().strip()
	t = {'f':'future_articles', 'p':'past_articles'}[future_or_past]
	while True:
		id_out = given_article_id_get_top_related(id_, t, m, a)
		print chr(27) + "[2J"
		if not id_out:
			print "NO MORE ARTICLES!"
			sys.exit()		
		print "==============\nCURRENT ARTICLE:"
		print a[id_]['headline']
		print a[id_]['standfirst']
		print a[id_]['date']
		print id_
		print 
		print "==============\nRELATED ARTICLES:"
		counter = 0
		for x in id_out:
			counter += 1	
			print 				
			print counter
			print a[x]['headline']
			print a[x]['standfirst']
			if future_or_past=='f':
				earlier_later = 'later'
			else:
				earlier_later = 'earlier'
			print str((a[x]['date']-a[id_]['date']).days)+' days '+earlier_later
			print x
			print "\n-----------------"
			
		number = raw_input('Which article (1, 2, 3, etc...) shall we follow next...? >> ')
		number = int(number)-1
		id_ = id_out[number]


def given_article_id_get_top_related(article_id, future_or_past, cosine_similarity_matrix, articles):
	"""
	Given an article ID (e.g. 'world/2013/aug/19/...') and either 'past_articles' or 'future_articles'
	Look up article in cosine_similarity matrix to find related IDs in past or future
	Load all related IDs into a mini article set
	Convert contents to TFIDF form
	Carry out KMeans clustering with appropriate K value
	Pull out top article for each cluster
	"""
	# Related article IDs in the form:
	# {u'world/2012/dec/27/central-african-republic-rebels-capital': 59, u'world/2012/dec/28/central-african-republis-us-embassy': 54,}   
	related_articles_and_scores = cosine_similarity_matrix[article_id][future_or_past]

	# If we don't have many articles, just return the articles we have
	if len(related_articles_and_scores)<=3:
		return [id_ for id_ in related_articles_and_scores]

	# Loop through the IDs to create a mini article set
	# Only consider 1-90 day articles, unless there are not enough, then fill up with youngest articles
	mini_article_set = create_mini_article_set(
		main_article_id = article_id,
		related_articles_and_scores=related_articles_and_scores,
		articles = articles,
		day_range = (1,90)
		)

	# TF-IDF of articles
	ids, _, tfidf_sparse_matrix = articles_to_tfidf(mini_article_set)

	# Apply K-means clustering
	k_means = k_means_cluster(tfidf_sparse_matrix)

	# Create [ (id, kmeans_cluster, cosine_score), (id, kmeans_cluster, cosine_score) ...]
	ids_and_labels = zip (ids, k_means.labels_)
	ids_and_labels_and_scores = [(id_, label, related_articles_and_scores[id_]) for id_,label in ids_and_labels]

	# Pick top article from each cluster
	output = pick_top_id_from_each_cluster(ids_and_labels_and_scores)
	
	# Return list of IDs
	return output


def create_mini_article_set(
		main_article_id, 
		related_articles_and_scores,
		articles, 
		day_range=(1,90),
		min_no_articles = 8):
	"""
	main_article_id = 'world/2014/nov...'
	related_articles_and_scores = {u'world/2012/dec/27/central-african-republic-rebels-capital': 59, u'world/2012/dec/28/central-african-republis-us-embassy': 54,} --> related IDs, and their scores
	articles = {'world/2012/de...':{'headline':'blah', 'standfirst':'blah blah'... etc}} --> main article collection
	day_range = (1, 90) --> inclusive range of days after/before we include article (note default doesnt include same day articles, i.e. 0)
	Function returns a mini set of articles (in the form of the main articles dict)
	Only includes articles in the related_articles_and_scores dict who fulfil day_range condition
	However, if total number is below minimum threshold (min_no_articles) we fill up to this number with youngest articles possible
	"""
	mini_article_set = {}
	ids_and_day_diffs = []  # Temporary list to be filled like so: [(id, day_diff), (id, day_diff)...]
	main_article_date = articles[main_article_id]['date']
	if debug:
		print "Firstly filtering articles for date range - can we find %s articles?" %(min_no_articles)
	for id_ in related_articles_and_scores:
		# Check date difference
		related_article_date = articles[id_]['date']
		day_diff = abs ( (main_article_date-related_article_date).days )
		ids_and_day_diffs.append( (id_, day_diff) )
		if day_diff>day_range[1] or day_diff<day_range[0]:
			# Not in day range, skip
			if debug:
				print "Not including article - %s days difference..." %day_diff
			continue
		if debug:
			print "Including article - %s days difference..." %day_diff
		mini_article_set[id_] = articles[id_]

	if debug:
		print "We have %s articles found so far within date range." %(len(mini_article_set))
	if len(mini_article_set)>=min_no_articles:	
		if debug:
			print "Returning %s articles.\n"	
		return mini_article_set

	# If we still need to add more, sort by day difference, taking earliest ones
	if debug:
		print "Not enough articles - sort by date and add closest dates..."
	ids_and_day_diffs_sorted = sorted(ids_and_day_diffs, key=lambda y: y[1])[0:min_no_articles*2]

	# Loop through and add smallest day_diff articles until we have enough to return
	for id_, day_diff in ids_and_day_diffs_sorted:
		# Ignore if we already have this ID
		if id_ in mini_article_set:
			continue
		# Add article to our output
		mini_article_set[id_] = articles[id_]
		# Check if we have enough
		if len(mini_article_set)==min_no_articles:
			if debug:
				print "Reaching minimum number, returning %s articles.\n" %(len(mini_article_set))
			return mini_article_set

	# Return mini_article_set, however long it is
	if debug:
		print "Didn't reach target, returning all articles we have (%s articles).\n" %(len(mini_article_set))
	return mini_article_set


def pick_top_id_from_each_cluster(ids_and_labels_and_scores):
	"""
	Given list of IDs, cluster labels, and cosine scores, pick out the 'best' article to show for each cluster
	TODO: currently just picks most related article, but should also use PageRank, Facebook etc. which we can look up from main article dictionary...
	Returns 2 or 3 IDs in a list
	"""
	top_id_set = []
	number_of_clusters = len(set([x[1] for x in ids_and_labels_and_scores]))  # Will be 2 or 3
	# For 0, 1, 2 (i.e. cluster numbers)
	for k in range(number_of_clusters):
		# Create a list just for this cluster
		filtered = [x for x in ids_and_labels_and_scores if x[1]==k]
		# Sort by cosine score
		filtered = sorted(filtered, key=lambda x: x[2], reverse=True)
		# Pick the top one only and add to return list
		top_id = filtered[0][0]
		top_id_set.append(top_id)
	return top_id_set


def k_means_cluster(tfidf_sparse_matrix, K=None):
	"""
	Given tf-idf of an article set, apply K-means clustering
	If no K value provided, we calculate it as 2 or 3
	Returns a k_means object (which we can then call .labels_ on later...)
	"""
	from sklearn.cluster import KMeans
	import numpy as np

	# 3 clusters if more than 9 articles, 2 otherwise
	if not K:
		K = 3 if tfidf_sparse_matrix.shape[0]>=9 else 2
	k_means = KMeans(init='k-means++', n_clusters=K, n_init=20)
	k_means.fit(tfidf_sparse_matrix)
	k_means_labels = k_means.labels_
	return k_means
	
def articles_to_tfidf(articles):
	"""
	Given article set, output ids, strings of terms, TF-IDF sparse matrix
	For each article we need to create a string which is all words in article:
		e.g. 'john major wins vote john major has won the vote laadeedaa'
	Final structure going into vectoriser is tuple of these strings	
	"""
	from sklearn.feature_extraction.text import TfidfVectorizer

	ids_and_data = []

	# Loop through each article and pull out string of terms
	for id_ in articles:
		article_vector = create_vector_from_article(articles[id_], include_standfirst=True)
		article_string = convert_vector_to_string(article_vector)

		# Add this to the ids_and_data list as a tuple
		ids_and_data.append( (id_, article_string) )

	# Create tuple of all of the strings, and one of all ids too
	ids, strings = zip(*ids_and_data)

	# Apply TF-IDF to get a sparse matrix
	sparse_matrix = TfidfVectorizer(stop_words=stopwords).fit_transform(strings)

	return ids, strings, sparse_matrix

def convert_vector_to_string(vector):
	"""
	Given Counter (i.e. dict) of terms
	Convert these into one string
	"""
	output_string = ""
	for key in vector:
		for _ in range(vector[key]):
			output_string += key.replace(' ', '')
			output_string += ' '
	return output_string


# Create a NEW cosine similarity dictionary and save as pickle for ALL articles
# WARNING: incremental_add=False means we start from a blank matrix
if False:
	create_cosine_similarity_pickle_all_articles(threshold=0.3, incremental_add=False)

# Update the cosine similarity dictionary and save as pickle for incremental articles
# incremental_add=True means we only add incremental articles
if False:
	create_cosine_similarity_pickle_all_articles(incremental_add=True)

# Create a smaller articles pickle, and python module, based on articles in cosine similarity dict, and only including relevant fields
if False:
	create_butterzip_files()

# For testing purposes
if False:
	a=general_functions.load_pickle('data/articles_uk.p')
	m=general_functions.load_pickle('data/articles_uk_cosine_similarities.p')
	ids = [  (u'world/2014/jan/27/nsa-gchq-smartphone-app-angry-birds-personal-data', 82),
			 (u'world/2014/feb/02/david-miranda-detention-chilling-attack-journalism', 87),
			 (u'world/2014/feb/14/court-challenge-mass-surveillance', 99),
			 (u'world/2014/feb/18/merkel-phone-tapping-law-mi6-nigel-inkster', 103),
			 (u'world/2014/feb/19/david-miranda-detention-lawful-court-glenn-greenwald',
			  104),
			 (u'world/2014/feb/27/gchq-interception-storage-webcam-images-condemned', 112),
			 (u'world/2014/feb/27/gchq-insists-optic-nerve-program-legal-legislation-2000',
			  112),
			 (u'world/2014/feb/28/nsa-gchq-webcam-spy-program-senate-investigation', 113),
			 (u'world/2014/feb/27/gchq-nsa-webcam-images-internet-yahoo', 113),
			 (u'world/2014/mar/04/nsa-chief-keith-alexander-david-miranda', 117),
			 (u'world/2014/apr/11/journalists-nsa-guardian-polk-award-snowden', 155),
			 (u'world/2014/may/11/lack-oversight-nsa-menwith-hill', 185),
			 (u'world/2014/may/15/david-miranda-appeal-high-court-ruling-detention-heathrow',
			  189),
			 (u'world/2014/may/23/surveillance-claims-boston-college-tapes', 197),
			 (u'world/2014/jun/07/stephen-fry-denounces-uk-government-edward-snowden-nsa-revelations',
			  212),
			 (u'world/2014/jun/11/government-public-case-surveillance-state-theresa-may',
			  216),
			 (u'world/2014/jun/17/mass-surveillance-social-media-permitted-uk-law-charles-farr',
			  222),
			 (u'world/2014/jun/18/labour-merkel-nsa-phone-tapping-raf-croughton', 223),
			 (u'world/2014/jun/18/government-surveillance-watchdog-loopholes', 223),
			 (u'world/2014/jun/26/privacy-invasion-surveillance-intelligences-services-commissioner',
			  231)]
 	for id_,_ in ids:
 		print '=========' 		
		print "Finding top related for %s..." %id_
 		print given_article_id_get_top_related(article_id=id_, future_or_past='future_articles', cosine_similarity_matrix=m, articles=a)
 		print '=========\n'

# For testing purposes
if False:
	play_with_related_articles()

"""
Notes
When app starts:
- choose an example story
- or search by tag (could use guardian api or google for search if not by tag?)
- or paste in guardian URL
Create search function when app starts
2 ways: 1 using pickle for testing, but real way will probably be search database by tag 
Or enter guardian URL (and will check if it exists)

Setup
=====
Database:
-- when searching guardian and seeing if we have article, needs to do 20 or so(?) calls to database to see if each article is in it
-- 
Python modules
-- convert pickles into python modules to load within heroku
-- we can reduce size of articles just by using format {'id':{'headline':'blah', 'standfirst':'blah blah', 'thumbnail':'url'}} and only including articles for which we have cosine data
-- we can reduce size of cosine matrix by using lookup codes instead of full ids

Butterfly expansion
===============
investigate - should i be using tfidf instead of cosine similarity??
redo - 0.4ish for threshold
redo - Filter out anything saying 'live' in ID - regex
Only work with subset for a while to iron out mistakes
done - For kmeans only consider articles between 1-90 days UNLESS there are not enough (say 10) in which case take the 10 youngest articles 
maybe add this if needed - If over 20 articles, take the 20 highest cosine similarities for kmeans
Once clusters found, pick highest from each cluster as before 
-- (extension would be to take best pagerank/FB from top 3 cosine-similarities within each cluster, but don't bother)

"""