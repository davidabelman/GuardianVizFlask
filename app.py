"""
Main web app.
Loads index page first.
Then user can select other pages.
AJAX calls also stored here.
Can turn scikit_learn on or off (currently off)
"""

from flask import Flask, render_template, request
import json
import datetime
import random
import general_functions

print "Importing articles..."
from articles_butterzip import articles

use_scikit_learn = False
if use_scikit_learn:
	# If we want to use scikit learn (i.e. we have loaded it on Heroku)
	# then we can calculate K-means scores on the fly, without creating frozen top scores
	print "WARNING: use_scikit_learn=True. This won't work on Heroku until buildpack working..."
	from butterfly_main import given_article_id_calculate_top_related
	print "Importing cosine similarity matrix..."
	from cosine_similarity_matrix_butterzip import cosine_similarity_matrix
	print "Importing lookups"
	from countid_to_guardianid import countid_to_guardianid

app = Flask(__name__)
app.debug = True


@app.route('/')
def home():
	"""
	Show main page
	"""
	print "Loading main.html"
	return render_template('visualisation_index.html')

@app.route('/butterfly_effect')
def butterfly_effect():
	"""
	Show butterfly effect page
	"""	
	print "Loading butterfly effect"
	return render_template('butterfly.html')

@app.route('/grid_2d')
def grid_2d():
	"""
	Show 2D grid page
	"""	
	print "Loading 2D grid"
	return render_template('grid.html')

@app.route('/_butterfly_get_related_articles', methods=['GET', 'POST'])
def butterfly_get_related_articles():
	"""
	Given an article ID and 'past_articles'/'future_articles' argument
	Return list of related articles to display, all in correct format
	"""
	# Get initial ID and past/future argument via AJAX
	article_id = request.json['python_id']
	print "Received ID %s from AJAX..." %article_id

	future_or_past = request.json['future_or_past']
	print "Received %s (for future_or_past) from AJAX..." %future_or_past

	# Get related article IDs
	# (Can use either scikit learn to calculate live, or look up in our articles data structure)
	if use_scikit_learn:
		ids = given_article_id_calculate_top_related(
			article_id=article_id,
			future_or_past=future_or_past,
			cosine_similarity_matrix=cosine_similarity_matrix,
			articles=articles,
			countid_to_guardianid=countid_to_guardianid)		
	else:
		# Just look up the frozen values for top kmeans picks, saved in articles file
		ids = articles[article_id][future_or_past[0]]  # i.e. ['f'] or ['p']
		print "Related articles to show are:", ids

	# Get list of the date differences from the original article clicked on		
	if future_or_past=='f':
		earlier_or_later = 'later'
	elif future_or_past=='p':
		earlier_or_later = 'earlier'
	else:
		print "Unrecognised future_or_past argument (%s)" %future_or_past
	date_differences = [str((articles[id_]['date']-articles[article_id]['date']).days)+' days ' + earlier_or_later for id_ in ids]
	# So we have IDs and their date differences: [(world/2014/.., 4 days), (world/2013/.., 12 days)...]
	ids_and_dates = zip(ids, date_differences)

	if len(ids)==0:
		print "No articles found, sending back status -1"
		return json.dumps ( {'status':-1} )
	print "Related articles found are %s" %ids

	# Get related article data and in correct format
	# (Can use either saved pickle, or look up in nosql database)
	ajax_list_of_articles = []
	for article_id,days in ids_and_dates:
		a = articles[article_id]
		article_clean = {
			'python_id':article_id,
			'id':article_id.replace('/',''),
			'headline':a['headline'].replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"'),
			'headline_short':a['headline'][0:30]+'...',
			'standfirst':a['standfirst'],
			'date':a['date'].strftime('%d %b %Y'),
			'date_difference':days,
			'image':a['thumbnail'],
			'url':'http://www.theguardian.com/'+article_id,
			'readmore':"<a href='http://www.theguardian.com/%s' target='_blank'>Click here to read more on the Guardian website</a>" %article_id
		}
		ajax_list_of_articles.append(article_clean)

	# Return data to javascript via JSON
	# [(id, headline, strapline, date, date_difference, image, url), (...), (...)]
	data = {'status':1,
			'data': ajax_list_of_articles
			}

	return json.dumps(data)

@app.route('/_butterfly_search_random', methods=['GET', 'POST'])
def butterfly_search_random():
	"""
	Pick 5 random articles to display to user
	Keeps finding random articles from buterzipped articles
	If date is OK and future articles are available, adds to set
	Once set reaches required size, return json
	"""
	collected_article_ids = []
	collected_article_dicts = []
	all_ids = [key for key in articles]

	# Get 5 suitable article IDs
	while True:
		index = random.randint(0, len(all_ids)-1)
		id_ = all_ids[index]
		# Check we haven't already taken it
		if id_ in collected_article_ids:
			continue
		# Check date is correct
		if articles[id_]['date'].year != 2012:
			continue
		# Check 3 future articles exist
		if len(articles[id_]['f']) < 3:
			continue
		collected_article_ids.append(id_)
		if len(collected_article_ids)==5:
			print "We now have 5 random articles"
			print collected_article_ids
			break

	# Send back in correct format
	for id_ in collected_article_ids:
		reduced = {'headline':articles[id_]['headline'],
					'date': '%s-%s-%s' %(articles[id_]['date'].year, articles[id_]['date'].month, articles[id_]['date'].day),
					'id':id_
					}
		collected_article_dicts.append(reduced)
	print "This is our data to return:"
	print collected_article_dicts

	# Return
	return json.dumps( {'status':'1',
						'data':collected_article_dicts})




@app.route('/_butterfly_search_guardian', methods=['GET', 'POST'])
def butterfly_search_guardian():
	"""
	Given search query and date range
	Return data from The Guardian search api
	"""
	# Allow testing functionality to skip guardian search
	testing = False
	if testing:
		import time
		time.sleep(1)
		data = {'status': '1', 'data': [{'headline': u'David Cameron to attend Bilderberg group meeting', 'date': u'2013-06-07T11:38:45Z', 'id': u'world/2013/jun/07/david-cameron-attend-bilderberg-group'}, {'headline': u'David Cameron and Europe at odds over benefit tourism issue', 'date': u'2013-10-14T23:03:00Z', 'id': u'world/2013/oct/15/david-cameron-europe-benefit-tourism'}, {'headline': u"Tamils hail David Cameron as 'god' but Sri Lankan president is not a believer", 'date': u'2013-11-15T22:12:00Z', 'id': u'world/2013/nov/15/david-cameron-visits-tamils-sri-lanka'}, {'headline': u'Sri Lanka: Cameron pushes for international war crimes inquiry', 'date': u'2013-11-16T10:47:09Z', 'id': u'world/2013/nov/16/sri-lanka-cameron-international-war-crimes-inquiry'}, {'headline': u'Sri Lanka defiant after Cameron calls for war crimes investigation', 'date': u'2013-11-17T00:00:00Z', 'id': u'world/2013/nov/16/sri-lanka-david-cameron-war-crime-allegations'}, {'headline': u'UK would welcome Chinese investment in HS2, says David Cameron', 'date': u'2013-12-03T09:47:31Z', 'id': u'world/2013/dec/03/uk-chinese-investment-hs2-david-cameron'}, {'headline': u'David Cameron: Mandela service offers world leaders chance for diplomacy', 'date': u'2013-12-10T09:35:12Z', 'id': u'world/2013/dec/10/david-cameron-mandela-service-diplomacy'}, {'headline': u'David Cameron shares bunk bed with Michael Owen on way to Afghanistan', 'date': u'2013-12-16T13:47:00Z', 'id': u'world/2013/dec/16/david-cameron-michael-owen-football-afghanistan'}, {'headline': u'David Cameron to challenge EU over surveillance drone programme plans', 'date': u'2013-12-19T00:01:17Z', 'id': u'world/2013/dec/19/david-cameron-eu-surveillance-drone-nato-security-europe'}, {'headline': u"Doctor's body repatriated as PM says Syrian regime 'must answer' for death", 'date': u'2013-12-22T19:26:26Z', 'id': u'world/2013/dec/22/british-doctor-abbas-khan-syria-cameron'}]}
		return json.dumps(data)

	# Get search query by AJAX
	query = request.json['query']
	start_date = request.json['start_date']
	end_date = request.json['end_date']

	results = general_functions.search_guardian_by_query(
		query=query,
		articles=articles,
		pickle_or_database = 'pickle',
		start_date=start_date,
		end_date=end_date,
		section='world',
		guardian_page_size=100,
		return_number=10
	)

	# Return status 0 if no results
	if len(results)>0:
		status='1'
	else:
		status='0'

	# Return results
	data = {'status':status,
			'data': results}	
	return json.dumps(data)


@app.route('/_return_clean_article_by_id', methods=['GET', 'POST'])
def return_clean_article_by_id():
	"""
	Given ID by AJAX
	Look up article in Pickle or in database
	Return clean version of headline, standfirst, image, etc. for use in butterfly visualisation
	"""
	print request.json
	# ID from AJAX
	article_id = request.json['python_id']

	# If using pickle, load article using this ID
	a = articles[article_id]
	article_clean = {
			'python_id':article_id,
			'id':article_id.replace('/',''),
			'headline':a['headline'].replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"'),
			'headline_short':a['headline'].replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"')[0:30]+'...',
			'standfirst':a['standfirst'],
			'date':a['date'].strftime('%d %b %Y'),
			'date_difference':'NA',
			'image':a['thumbnail'],
			'url':'http://www.theguardian.com/'+article_id,
			'readmore':"<a href='http://www.theguardian.com/%s' target='_blank'>Click here to read more on the Guardian website</a>" %article_id
		}

	print "Returning article data:"
	print article_clean
	return json.dumps({'status':'1', 'data':article_clean})

if __name__ == '__main__':
	app.run()

