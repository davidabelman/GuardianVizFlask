"""
==============================
Butterfly effect visualisation
==============================

Usage:
>>> python butterfly_main [incremental|fresh]
- 'incremental' argument will add any incremental articles to the cosine similarity matrix, and recalculate any k-means clustering for the last 180 days. If we are running this regularly we can just run on incremental mode, which will take the latest pulled articles from the Guardian and add the relevant info to our butterzip data
- 'fresh' argument will completely calculate all cosine similarities and k-means clustering from afresh. We can run this whenever we like - it may just take a while!
Files are written to output which will be used by the heroku/flask app. The main one of these outputs is called 'articles_butterzip.py'.

Notes on methodology:
1) Similarity value found between all pairs of articles based on tag, headline, and strapline. These are found by cosine similarity, and pairwise values are stored in sparse format (any values below threshold ignored). Note we also disregard certain types of article, and those with low number of FB shares. We only need to store values if they are above a certain threshold. These are all calculated on a one off basis at first, and as new articles are crawled, we need to calculate pairwise similarity with all existing articles and store these values (i.e. run with incremental_add=True). Note that for each value stored, we need to store it either within 'future_articles' or 'past_articles'.	

2) For all similar articles (say 50 of them) we run K-means and form 2 or 3 topics of similar articles. Number of topics may depend on how many similar articles there are. We then pick out the most relevant article from each group (currently just done by maximal cosine similarity, though could use pagerank or facebook shares or date, etc.). This process can be done live (i.e. given list of similar articles, do the k-means clustering on web server) though due to issues with sklearn on Heroku, currently we run with use_sklearn=False, so these values are all also precalculated and stored to be looked up at runtime. This does make things faster too at runtime. The disadvantage is that we have to recalculate the k-means clustering frequently, as older articles need to link to newer articles. Thus we can't add incrementally - we have to go back 90+ days to recalculate k-means clustering on all the new to medium aged articles.

3) We use this data on the Flask app by loading a Python module containing the correct dictionaries etc. We don't use a database as this is just a proof of concept, though that would be preferable! Everything can only fit in memory if we do some compressing, called 'butterzip' for the purposes of this project. 
	--> articles pickle turned to articles_butterzip pickle (only stores the relevant information in the file, as well as k-means clustering results), and saved as a python module
	--> cosine_sim_matrix turned to cosine_sim_matrix_butterzip pickle (also uses lookup codes instead of ID), and then saved as python module. Note that this isn't used at runtime if we're doing the use_sklearn=False method, as we already have the k-means results within the articles_butterzip, so no need to recalculate using lists of similar articles. However, they are saved within the butterzip calculation just for completeness.


TODO:
- Use TFIDF instead of cosine similarity? Probably not - too slow.
- Use LDA instead of K-means?
- Should pick best article from k-means cluster based on more than just cosine similarity
	(i.e. pagerank, facebook popularity, etc.)
- Automatically crawl from latest date up until 2 days ago??
- Crawl all data from 1st Jan 2012 to 31st July 2012. Incrementally add cosines, and recalculate K-means ONLY for articles older than 750 days
- Do a final pull of data in December up to yesterday
- Prep (correct width) images for CV website
- Update CV website
- Finish intro page for speech synthesis, turn into a flask app, upload

"""

import time
import sys
import re
WORD = re.compile(r'\w+')
import math
import pprint
from collections import Counter
import options
reload(options)
import datetime
import general_functions
stopwords = general_functions.create_stopword_list(extra_words = options.tfidf_extra_stopwords)
debug = False


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
	import re
	check = id_str
	#TODO:make into regex
	match = re.search('(video|gallery|picture|interactive|commentisfree|blog|live|shortcuts)', check)
	if match:
		return True
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
	 

def create_cosine_similarity_pickle_all_articles(threshold=0.3, incremental_add=True, fb_share_minimum=10):
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
		# u = raw_input('>> ')
		u = 'y'
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

		# Skip if Facebook share rate too low
		fb_shares = articles[id1]['facebook']['snapshot_of_total']
		try:
			if int(fb_shares)<fb_share_minimum:
				print "Skipping article, FB shares too low"
				continue
		except:
			print "Skipping article, FB shares not crawled yet"
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
			# Skip if same article
			if id1==id2:
				continue
			# Skip if low FB shares
			fb_shares = articles[id2]['facebook']['snapshot_of_total']
			try:
				if int(fb_shares)<fb_share_minimum:
					continue
			except:			
				continue
			# Skip if bad article type
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
def create_butterzip_files(use_scikit_learn=False):
	""""
	1) Creates articles_butterzip.p and articles_butterzip.py:
		... these only contain articles in the cosine_similarity_matrix
		... these only contain fields used in the butterfly viz (id, headline, strapline, image, date) 
		... these also contain frozen k-means results so we don't have to calculate live (TODO: only future articles included for now to save on memory)

	2) Creates cosine_similarity_matrix_butterzip.py, which is a copy of cosine_similarity_matrix but uses simpler IDs (from lookup). Also need to create the lookup both ways for this.


	"""

	print "Creating butterzip files..."

	# Load main articles and cosine similarites pickles created previously
	articles = general_functions.load_pickle(filename = options.current_articles_path)
	cosine_similarity_matrix = general_functions.load_pickle(filename = options.current_articles_path_cosine_similarites)
	frozen_kmeans_future = general_functions.load_pickle(filename = options.current_articles_path_frozen_kmeans_future)
	frozen_kmeans_past = general_functions.load_pickle(filename = options.current_articles_path_frozen_kmeans_past)

	# 1) Create new articles (articles_butterzip)
	articles_butterzip = {}
	for id_ in cosine_similarity_matrix:
		if use_scikit_learn:
			article_barebones = {
				'headline':articles[id_]['headline'],
				'standfirst':articles[id_]['standfirst'],
				'date':articles[id_]['date'],
				'thumbnail':articles[id_]['thumbnail'],
				'tags':articles[id_]['tags'],
			}
		else: 
			article_barebones = {
				'headline':articles[id_]['headline'],
				'standfirst':articles[id_]['standfirst'],
				'date':articles[id_]['date'],
				'thumbnail':articles[id_]['thumbnail'],
				'f':frozen_kmeans_future[id_]  # frozen kmeans - also add past articles on another line here under 'p' key (TODO)
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
	
	# We need to create lookups for both ways
	# i.e. guardianid_to_countid = {'world/2014/Nov...':1, 'world/2014/Dec...':2,}
	# i.e. countid_to_guardianid = {1:'world/2014/Nov...', 2:'world/2014/Dec...',}
	guardianid_to_countid = {}
	countid_to_guardianid = {}
	counter = 0
	for id_ in cosine_similarity_matrix:
		counter+=1
		guardianid_to_countid[id_]=counter
		countid_to_guardianid[counter]=id_

	general_functions.write_to_python_module(
		data = guardianid_to_countid,
		variable_name = 'guardianid_to_countid',
		filename = '../flask/guardianid_to_countid.py')	
	general_functions.write_to_python_module(
		data = countid_to_guardianid,
		variable_name = 'countid_to_guardianid',
		filename = '../flask/countid_to_guardianid.py')	

	# And now we create a cosine_similarity_matrix_butterzip (i.e. reduced cosine_similarity_matrix) using these IDs
	cosine_similarity_matrix_butterzip = {}
	for id_ in cosine_similarity_matrix:
		# Get list of future articles and past articles for this ID within c_s_m
		future_articles = cosine_similarity_matrix[id_]['future_articles']
		past_articles = cosine_similarity_matrix[id_]['past_articles']
		# Convert these guardianids to countids within the lists
		future_articles_butterzip = dict ( [ (guardianid_to_countid[key], future_articles[key]) for key in future_articles if key in guardianid_to_countid] )
		past_articles_butterzip = dict ( [ (guardianid_to_countid[key], past_articles[key]) for key in past_articles if key in guardianid_to_countid] )
		# Save entries to butterzipped new cosine_similarity_matrix dict
		# Use 'f' instead of 'future_articles'
		# Use 'p' instead of 'past_articles'
		cosine_similarity_matrix_butterzip[id_] = {
			'f':future_articles_butterzip,
			'p':past_articles_butterzip
		}

	general_functions.write_to_python_module(
		data = cosine_similarity_matrix_butterzip,
		variable_name = 'cosine_similarity_matrix',
		filename = '../flask/cosine_similarity_matrix_butterzip.py')

	

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
		id_out = given_article_id_calculate_top_related(id_, t, m, a)
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


def given_article_id_calculate_top_related(article_id, future_or_past, cosine_similarity_matrix, articles, countid_to_guardianid=None):
	"""
	Given an article ID (e.g. 'world/2013/aug/19/...') and either 'past_articles' or 'future_articles'
	Look up article in cosine_similarity matrix to find related IDs in past or future
	Load all related IDs into a mini article set
	Convert contents to TFIDF form
	Carry out KMeans clustering with appropriate K value
	Pull out top article for each cluster
	"""
	# Related article IDs in the form:
	# {43: 59, 901: 54,}   
	related_articles_and_scores = cosine_similarity_matrix[article_id][future_or_past]

	# If we supply a lookup here, we need to lookup non-abbreviated keys.
	# If not, we don't use the lookup, keep related_articles_and_scores as it is
	if countid_to_guardianid:
		# Related article IDs in the form:
		# {u'world/2012/dec/27/central-african-republic-rebels-capital': 59, u'world/2012/dec/28/central-african-republis-us-embassy': 54,}  
		# i.e. convert the counterid to a guardianid

		related_articles_and_scores = dict( [ (countid_to_guardianid[key], related_articles_and_scores[key]) for key in related_articles_and_scores] )	

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


def create_frozen_kmeans_lookup(articles,
		cosine_similarity_matrix,
		future_or_past,
		days_ago_start=90,
		days_ago_end=0,
		incremental_add=True):
	"""
	If we don't want to calculate kmeans clusters at run-time, we can calculate in advance
	This function carries this out
	For each article in cosine_similarity_matrix we calculate the top 2 or 3 articles to show via k-means
	We save everything to a pickle (which can later be 'butterzipped')
	Format is like this, i.e. each article in cosine_sim_matrix is a key with related articles as list:
	{
		'world/2014/nov...': ['world/2015/jan/...', 'world/2014/dec/...'],
		'world/2014/oct...': ['world/2015/feb/...', 'world/2014/dec/...'],
	}
	We can select the number of days to go back. We should always go back 90 (atleast 90!) so that older articles can 'find' any newer articles we have added in the 90 days after it. If incremental_add = False, number of days is set at 9999.
	"""
	# Ensure argument correct
	assert future_or_past=='future_articles' or future_or_past=='past_articles', 'future_or_past variable must be "future_articles" or "past_articles"'
	# Path at which we will save/load pickle:
	if future_or_past == 'future_articles':
		save_path = options.current_articles_path_frozen_kmeans_future
	elif future_or_past == 'past_articles':
		save_path = options.current_articles_path_frozen_kmeans_past
	
	# We will fill out a dictionary
	# If we aren't adding incrementally we start from afresh
	if not incremental_add:
		frozen_kmeans = {}
		days_ago_start = 9999
		days_ago_end = 0
		print "Incremental add is set to False. Creating a new pickle."
	# If we want to add incrementally, we load the existing pickle (if exists)
	else:
		frozen_kmeans = general_functions.load_pickle(save_path)
		if frozen_kmeans==None:
			print "WARNING: Creating new pickle - no file found at %s" %(save_path)
			frozen_kmeans = {}

	# Counters, ids_to_calculate (only articles newer than a certain date)
	counter = 0
	ids_to_calculate = [id_ for id_ in cosine_similarity_matrix
		if (datetime.datetime.today()-articles[id_]['date']).days <= days_ago_start
		if (datetime.datetime.today()-articles[id_]['date']).days >= days_ago_end ]	
	total = len(ids_to_calculate)
	print "We will calculate top K-means results for %s articles (i.e. those between %s and %s days ago)" %(total, days_ago_start, days_ago_end)


	# Loop through all articles in cosine_similarity_matrix
	for article_id in ids_to_calculate:
		counter +=1
		# Find top ID for each cluster via K-means functionality
		ids = given_article_id_calculate_top_related(
			article_id=article_id,
			future_or_past=future_or_past,
			cosine_similarity_matrix=cosine_similarity_matrix,
			articles=articles)
		# Save these to our data structure
		frozen_kmeans[article_id] = ids
		print "Saved %s/%s [%s]" %(counter, total, article_id)

		if counter%100==0:
			general_functions.save_pickle(data = frozen_kmeans,
				filename = save_path)

	general_functions.save_pickle(data = frozen_kmeans,
				filename = save_path)



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



if __name__ == '__main__':
	assert len(sys.argv)==2, 'Usage: butterfly_main.py [fresh|incremental]'
	assert sys.argv[1]=='fresh' or sys.argv[1]=='incremental', 'Usage: butterfly_main.py [fresh|incremental]'

	if sys.argv[1]=='fresh':
		incremental_add = False
	else:
		incremental_add = True

	# Depending on status of incremental_add:
	# If False: Create a NEW cosine similarity dictionary and save as pickle for ALL articles
	# If True: Update the cosine similarity dictionary and save as pickle for incremental articles
	# Filter out articles with less than X facebook shares
	# Only save cosine similarities above Y threshold value
	if True:
		print "COSINE SIMILARITY CALCULATIONS:"
		create_cosine_similarity_pickle_all_articles(threshold=0.4, incremental_add=incremental_add, fb_share_minimum=20)

	# If we don't want to calculate the top K-means clusters at run-time, we can save the IDs beforehand by running this. Number of days to re-calculate should be 90 or above when calculating for 'future' articles, as we need to 'catch' new articles coming in within the historial articles' related lists.
	# If incremental add is false, we recreate the whole matrix (with number of days set at 9999)
	if True:
		print "KMEANS CLUSTERING CALCULATIONS:"
		create_frozen_kmeans_lookup(
			articles=general_functions.load_pickle(options.current_articles_path),
			cosine_similarity_matrix=general_functions.load_pickle(options.current_articles_path_cosine_similarites),
			future_or_past='future_articles',
			days_ago_start=1800, #should be 180 or so
			days_ago_end=750, # should be 0
			incremental_add=incremental_add)

	# Create a smaller articles pickle, and python module, based on articles in cosine similarity dict, and only including relevant fields. Also create 
	if True:
		print "COMPRESSING FILES (BUTTERZIP) FOR USE ON HEROKU"
		create_butterzip_files(use_scikit_learn=False)
