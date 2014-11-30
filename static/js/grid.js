var maximumHue = 180;
var randomHue = 30;
var minimumBrightness = 5;
var randomBrightness = 1;
var minimumSaturation = 0.55;
var randomSaturation = 1;


var limit_text = function(string, N) {
	// Returns shortened text snippet to N letters
	if (string.length >= N) {
		return string.substring(0,N-1)+"...";
	}
	else {
		return string
	}
}

var smallest_element_in_list = function(list) {
	// Returns shortest text element in a list
	var best_len = 1000;
	for (var i = 0; i<list.length; i++) {
		if (list[i].length < best_len) {
			output = list[i];
			best_len = list[i].length
		}
	}
	return output;
}

var first_short_element = function(list, N) {
	// Returns first element below a certain length
	for (var i=0 ; i<list.length; i++) {
		if (list[i].length <= N) {
			return list[i]
		}
	}
	// if there are none under N, return shortest
	return smallest_element_in_list(list)
}

function randomIntFromInterval(min,max)
	// Randint
	{
	    return Math.floor(Math.random()*(max-min+1)+min);
	}

function colourByVariable(varname)
	// Recolours the visualisation (and the post-hovers) based on some variable in the data (typically 'fb', 'cluster', 'recency')
	{

		var maxValue = d3.max(dataset, function(d) { return d[varname]; });
		var minValue = d3.min(dataset, function(d) { return d[varname]; });

		var variableMaxHue = {'fb':0, 'cluster':180, 'recency':100};
		var variableMinHue = {'fb':180, 'cluster':0, 'recency':0};
		
		var recencyScale = d3.scale.linear()
							 .domain([minValue, maxValue])
							 .range([variableMinHue[varname],variableMaxHue[varname]]);

		d3.select('#grid svg').selectAll('rect')
		   .data(dataset)
		   .transition()
		   .delay(function(d) {return d['x']+d['y']*30})
		   .attr( {
		   		fill: 
		   			function(d,i) { 
		   			return d3.hsl ( recencyScale(d[varname])+(Math.random()*30), 
		   							(Math.random()*randomSaturation)+minimumSaturation ,
		   							randomIntFromInterval(minimumBrightness,minimumBrightness+randomBrightness)/10 )
		   						}
				})

		d3.select('#grid svg').selectAll('rect')
		   .data(dataset)
		   .on("mouseout", function(d) {
				   d3.select(this)
				   		.transition()
				   		.duration(350)
						.attr( {
				   		fill: 
				   			function(d,i) { 
				   			return d3.hsl ( recencyScale(d[varname])+(Math.random()*30), 
				   							(Math.random()*randomSaturation)+minimumSaturation ,
		   									randomIntFromInterval(minimumBrightness,minimumBrightness+randomBrightness)/10 )
				   						}
						})
			   })
	}


function remove_SVG_draw_squares(filename) {
	$('svg').fadeOut(100, function() 
		{ 
			$(this).remove(); 
			draw_squares(filename)
		});
}

function draw_squares() {
	var filename = '/static/json/grid/' + $('input[name=tag]:checked').val() + "_" + $('input[name=dayrange]:checked').val() + ".json"

	// Load JSON data and get going!
	d3.json(filename, function(json) {
		dataset = json; 
		//idealSize = $(window).height()*0.9
		idealSize = $('#grid').width()
		padding = 2  // Padding between squares

		// Variable on which colours will be decided
		var colour_variable = $('input[name=block_colours]:checked').val()

		// Calculate max and min values for scaling
		var maxX = d3.max(dataset, function(d) { return d['x']; });
		var maxY = d3.max(dataset, function(d) { return d['y']; });
		var maxFB = d3.max(dataset, function(d) { return d['fb']; })/3
		var minRed = d3.min(dataset, function(d) { return d['r']; })
		var maxRed = d3.max(dataset, function(d) { return d['r']; })
		var minBlue = d3.min(dataset, function(d) { return d['b']; })
		var maxBlue = d3.max(dataset, function(d) { return d['b']; })
		var minColourVariable = d3.min(dataset, function(d) { return d[colour_variable]; })
		var maxColourVariable = d3.max(dataset, function(d) { return d[colour_variable]; })

		var variableMaxHue = {'fb':0, 'cluster':180, 'recency':100};
		var variableMinHue = {'fb':180, 'cluster':0, 'recency':0};
		
		// Setting the padding Bostock way
		var margin = {top: 20, right: 0, bottom: 0, left: 0};
		var width = idealSize - margin.left - margin.right
		var height = idealSize - margin.top - margin.bottom;
		var svg = d3.select("#grid")
					.append("svg")
		   			.attr("width", width + margin.left + margin.right)
		   			.attr("height", height + margin.top + margin.bottom)
		  			.append("g")
		    		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

		//Create scale functions
		var xScale = d3.scale.linear()
							 .domain([0, maxX+1])
							 .range([0, width]);

		var yScale = d3.scale.linear()
							 .domain([0, maxX+1])
							 .range([0, height]);

		var sizeScale = d3.scale.linear()
							 .domain([0, maxFB])
							 .range([0, width/maxY]);
		
		var labelScale = d3.scale.linear()
							 .domain([3, 40])
							 .range([12, 0]);

		var hslScale = d3.scale.linear()
							 .domain([minColourVariable, maxColourVariable])
							 .range([variableMinHue[colour_variable], variableMaxHue[colour_variable]]);

		var fbScale = d3.scale.linear()
							 .domain([0, maxFB])
							 .range([0.5,0.8]);


		//Create shapes
		type='rect'
		//type = 'image'
		svg.selectAll(type)
		   .data(dataset)
		   
		   .enter()

		   .append(type)

		   .transition()

		   .delay(function(d) {return d['x']+d['y']*30})
		   //.attr("transform", "translate(250, 0) rotate(45)")  // If rotating to diamond formation
		   .attr( {
		   		x: function(d) {return xScale(d['x'])},
		   		y: function(d) {return yScale(d['y'])},
		   		width: width/(maxX+1)-padding,
		   		height: height/(maxX+1)-padding,
		   		rx: $('input[name=corner_radius]:checked').val(),
		   		// width: function(d) {return sizeScale(d['fb'])},
		   		// height: function(d) {return sizeScale(d['fb'])},
		   		// fill: function(d) {return "rgb("+Math.round(redScale(d['r']))+", "+d['g']+", "+Math.round((blueScale(d['b'])))+")"}
		   		fill: function(d) { 
		   			return d3.hsl ( hslScale(d[colour_variable])+((Math.random()*randomHue)) ,
		   											(Math.random()*randomSaturation)+minimumSaturation ,
		   											randomIntFromInterval(minimumBrightness,minimumBrightness+randomBrightness)/10 )
		   							}
		   		//'xlink:href': function(d) {return d['img']},  // Set 'rect' to 'image' if we want to show image
		   });

		   // Mouseover effects
		   svg.selectAll(type)
			   .data(dataset)
			   .on("mouseover", function(d) {
		   		d3.select(this)
		   			.attr("fill", "white");
		   		d3.select('#headline')
		   			.text(function() {return d['headline']})
		   		d3.select('#standfirst')
		   			.html(function() {return d['standfirst']})
		   		d3.select('#date')
		   			.html(function() {return d['date']})
			   })
			   .on("mouseout", function(d) {
				   d3.select(this)
				   		.transition()
				   		.duration(350)
						.attr("fill", 
							function(d) { 
					   			return d3.hsl ( hslScale(d[colour_variable])+((Math.random()*randomHue)) ,
					   											(Math.random()*randomSaturation)+minimumSaturation ,
					   											randomIntFromInterval(minimumBrightness,minimumBrightness+randomBrightness)/10 )
					   							}
								)
			   })
		   
		   // Open in a new window on click
		   .on("click", function(d) {
		   		window.open(d['url'],'_blank');
		   })

		   // Add text
			svg.selectAll("text")
			   .data(dataset)
			   .enter()
			   .append("text")
			   .transition()

		   		.delay(function(d) {return d['x']+d['y']*30})
			   .style("display", $('input[name=tag_visibility]:checked').val())
			   .text(function(d) {return first_short_element(d['tags'],5)
				})
			   .attr("x", function(d,i) {return xScale(d['x']+0.475)
			   })
			   .attr("y", function(d,i) {return yScale(d['y']+0.54)
			   })
			   .attr("font-family", "sans-serif")
			   .attr("font-size", labelScale(maxX))
			   .attr("fill", "black")
			   .attr("text-anchor", "middle")
			   .style("pointer-events", "none")


		   	
	});
	
}
