from flask import Flask, render_template, request
from butterfly_main import given_article_id_get_top_related
import json
import general_functions
# from flask.ext.script import Manager
use_pickles_or_database = 'pickles'
articles=general_functions.load_pickle('../open/data/articles.p')
cosine_similarity_matrix=general_functions.load_pickle('../open/data/articles_cosine_similarities.p')

app = Flask(__name__)
app.debug = True
# manager = Manager(app)

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
	# (Can use either scikit learn and pickle, or look up in nosql database)
	if use_pickles_or_database == 'pickles':
		ids = given_article_id_get_top_related(
			article_id=article_id,
			future_or_past=future_or_past,
			cosine_similarity_matrix=cosine_similarity_matrix,
			articles=articles)
		# Get list of the date differences from the original article clicked on
		date_differences = [str((articles[id_]['date']-articles[article_id]['date']).days)+' days later' for id_ in ids]
		# So we have IDs and their date differences: [(world/2014/.., 4 days), (world/2013/.., 12 days)...]
		ids_and_dates = zip(ids, date_differences)

	elif use_pickles_or_database == 'database':
		return ['TODO database functionality']

	if len(ids)==0:
		print "No articles found, sending back status -1"
		return json.dumps ( {'status':-1} )
	print "Related articles found are %s" %ids

	# Get related article data and in correct format
	# (Can use either saved pickle, or look up in nosql database)
	ajax_list_of_articles = []
	for i,days in ids_and_dates:
		a = articles[i]
		article_clean = {
			'python_id':a['id'],
			'id':a['id'].replace('/',''),
			'headline':a['headline'],
			'headline_short':a['headline'][0:30]+'...',
			'standfirst':a['standfirst'],
			'date':a['date'].strftime('%d %b %Y'),
			'date_difference':days,
			'image':a['thumbnail'],
			'url':a['url'],
			'readmore':"<a href='%s' target='_blank'>Click here to read more on the Guardian website</a>" %a['url']
		}
		ajax_list_of_articles.append(article_clean)

	# Return data to javascript via JSON
	# [(id, headline, strapline, date, date_difference, image, url), (...), (...)]
	data = {'status':1,
			'data': ajax_list_of_articles
				# [
				# 	{'python_id':'world/2013/aug/20/nsa-david-miranda-guardian-hard-drives',
				# 	'id':'world/2013/aug/20/nsa-david-miranda-guardian-hard-drives'.replace('/',''),
				# 	'headline':'Cardinal OBrien story',
				# 	'standfirst':'Standfirst from AJAX',
				# 	'date':'1 Dec 2014',
				# 	'date_difference':'+2 days',
				# 	'image':'http://static.guim.co.uk/sys-images/Guardian/Pix/pictures/2013/8/20/1377030430592/Josh-Earnest-003.jpg',
				# 	'url':'http://www.theguardian.com/world/2013/aug/20/nsa-david-miranda-guardian-hard-drives'
				# 	},
				# 	{'python_id':'world/2013/may/18/cardinal-obrien-still-danger-say-accusers',
				# 	'id': 'world/2013/may/18/cardinal-obrien-still-danger-say-accusers'.replace('/',''),
				# 	'headline':'Hard disk story',
				# 	'standfirst':'Standfirst 2 from AJAX',
				# 	'date':'2 Dec 2014',
				# 	'date_difference':'+3 days',
				# 	'image':'http://static.guim.co.uk/sys-images/Guardian/Pix/pictures/2013/8/20/1377019341697/The-remains-of-the-hard-d-005.jpg',
				# 	'url':'http://www.theguardian.com/world/2013/aug/23/nsa-prism-costs-tech-companies-paid'
				# 	}
				# ]
			}

	return json.dumps(data)


if __name__ == '__main__':
	app.run()

