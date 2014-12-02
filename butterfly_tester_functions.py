import general_functions
from butterfly_main import *

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