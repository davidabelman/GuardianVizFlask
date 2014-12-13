// Script dealing with the 'setup' for the visualisation
// Finding guardian articles, selecting a seed


// Submit guardian search when submit button pressed
$('#guardian_search_terms_submit').click( function(e) {
	e.preventDefault();
	e.stopImmediatePropagation();

	// Send data to AJAX to get Guardian results
	var query = $('#guardian_search_terms_input').val();
	var start_date = $('#startdate').val();
	var end_date = $('#enddate').val();

	// Check data is OK
	if (query.length == 0) {
		alert("Please make sure to enter a search query (currently blank).");
		return
	}
	if (end_date.slice(0,4)<2012) {
		alert("End date is before 2012. Note that you can only search articles after 1st January 2012.");
		return;
	}
	if (new Date(end_date)<new Date(start_date)) {
		alert("Start date is after end date. Please select a valid date range.");
		return;
	}
	if ( (new Date(end_date)-new Date(start_date))/1000/24/3600 < 7) {
		alert("Your start and end dates are quite close (within a week). Please expand the time between the dates.");
		return;
	}

	$.ajax( {
        url: '/_butterfly_search_guardian',
        data: JSON.stringify ({
          'query':query,
          'start_date':start_date,
          'end_date':end_date,
        }, null, '\t'),
        contentType: 'application/json;charset=UTF-8',
        type: "POST",
        success: function(response) {
          // Returns status=1 and userID
          response = JSON.parse(response);
          status = response['status']
          data = response['data']
          if (status=='1') {
            // Successfully retrieved new data
            console.log("Got data from AJAX:", data)
            // Add results to pane
            for (i=0; i<data.length; i++) {
            	html_to_add = '<div class="seed_div" python_id='+data[i]['id']+'>'
            	html_to_add += '<p class="seed_date">'+data[i]['date'].slice(0,10)+'<p>'
            	html_to_add += '<h4 class="seed_headline">'+data[i]['headline']+'<h4>'
            	html_to_add += '</div>'
            	current_html = $('#results_div').html()            	
            	$('#results_div').html(current_html + html_to_add)
            }
            // Make links clickable (which will hide div, start visualisation)
            make_seed_articles_clickable()

            // Show results pane
            $('#results_div').fadeIn(100)            
          }
          else if (status=='0') {
            // No articles found...
            console.log("Status 0, no search results")
            alert("Sorry, no articles were found! Try expanding your date range, or choosing different search terms.")
          }
        },
        fail: function() {
          console.log("Serverside error")
          alert("Serverside error")
        } // end success callback
      }); // end ajax
})


function make_seed_articles_clickable() {
	// Hide seed display when an article is selected, and start visualisation
	$('.seed_div').click( function(e) {
		e.preventDefault();
		e.stopImmediatePropagation();

		console.log("Clicked a seed article...")
		// ID of clicked article
		var python_id = $(this).attr('python_id')
		console.log(python_id)


		// Get data to start visualisation with...
		$.ajax( {
        url: '/_return_clean_article_by_id',
        data: JSON.stringify ({
          'python_id':python_id
          //'start_date':
          //'end_date':
        }, null, '\t'),
        contentType: 'application/json;charset=UTF-8',
        type: "POST",
        success: function(response) {
          // Returns status=1 and userID
          response = JSON.parse(response);
          status = response['status']
          data = response['data']
          if (status=='1') {
            // Successfully retrieved new data
            console.log("Got data from AJAX:", data)

            // Start visualisation based on data received
          //   var start_node = {id: data['id'],
		        // python_id: 'world/2013/feb/27/iran-turning-point-nuclear-talks',
		        // headline:'NSA files: UK and US at odds over destruction of Guardian hard drives',
		        // headline_short:'NSA files: UK and US at odds...',
		        // standfirst:'White House says it would be "difficult to imagine" US authorities adopting GCHQ tactics',
		        // date:'21 Aug 2013',
		        // image:'http://static.guim.co.uk/sys-images/Guardian/Pix/pictures/2013/8/20/1377030430592/Josh-Earnest-003.jpg',
		        // readmore:'<a href="http://www.theguardian.com/world/2013/aug/20/nsa-david-miranda-guardian-hard-drives">Click here to read more on the Guardian website</a>'};
			nodes.push(data);
			links.push();
			start();

            // Hide the seed screen and show visualisation
            $('#guardian_search_div').hide( function() {
				$('#visualisation_div').fadeIn(300);
			})

            // Show results pane
            $('#results_div').fadeIn(100)            
          }
          else {
            // Error...            
            alert("Error... status not 1")
          }
        },
        fail: function() {
          console.log("Serverside error")
          alert("Serverside error")
        } // end success callback
      }); // end ajax


	})
}