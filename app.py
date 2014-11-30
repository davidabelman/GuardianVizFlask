from flask import Flask, render_template, request
# from flask.ext.script import Manager

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

if __name__ == '__main__':
	app.run()

