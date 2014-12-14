// Script dealing with the 'setup' for the visualisation
// Finding guardian articles, selecting a seed

// Submit random search when random button pressed
$('#random_seed_article').click( function(e) {
	e.preventDefault();
	e.stopImmediatePropagation();

	// Send AJAX request
	$.ajax( {
        url: '/_butterfly_search_random',
        
        contentType: 'application/json;charset=UTF-8',
        type: "POST",
        success: function(response) {
          // Returns status=1 and userID
          var response = JSON.parse(response);
          var status = response['status'];
          var data = response['data'];
          if (status=='1') {
            // Successfully retrieved new data
            console.log("Got data from AJAX:", data)
            
            // Clear current results
            $('#results_list').html('')

            // Add results to pane
            for (i=0; i<data.length; i++) {
            	html_to_add = '<div class="seed_div" python_id='+data[i]['id']+'>'
            	html_to_add += '<p class="seed_date">'+data[i]['date'].slice(0,10)+'<p>'
            	html_to_add += '<h4 class="seed_headline">'+data[i]['headline']+'<h4>'
            	html_to_add += '</div>'
            	current_html = $('#results_list').html()            	
            	$('#results_list').html(current_html + html_to_add)
            }
            // Make links clickable (which will hide div, start visualisation)
            make_seed_articles_clickable()

            // Show results pane
            $('#results_div').fadeIn(100)        
          }
          else if (status=='0') {
            // No articles found...
            console.log("Status 0, no search results")
            alert("Sorry, there has been an unknown error.")
          }
        },
        fail: function() {
          console.log("Serverside error")
          alert("Serverside error")
        } // end success callback
      }); // end ajax
})


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
		alert("Please check end date is a valid date, and that it occurs in 2012 or after.");
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

	// Change text of submit button to 'searching...'
	$('#guardian_search_terms_submit').html('Searching...')

	// Send AJAX request
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
          var response = JSON.parse(response);
          var status = response['status'];
          var data = response['data'];
          if (status=='1') {
            // Successfully retrieved new data
            console.log("Got data from AJAX:", data)
            
            // Clear current results
            $('#results_list').html('')

            // Add results to pane
            for (i=0; i<data.length; i++) {
            	html_to_add = '<div class="seed_div" python_id='+data[i]['id']+'>'
            	html_to_add += '<p class="seed_date">'+data[i]['date'].slice(0,10)+'<p>'
            	html_to_add += '<h4 class="seed_headline">'+data[i]['headline']+'<h4>'
            	html_to_add += '</div>'
            	current_html = $('#results_list').html()            	
            	$('#results_list').html(current_html + html_to_add)
            }
            // Make links clickable (which will hide div, start visualisation)
            make_seed_articles_clickable()

            // Show results pane
            $('#results_div').fadeIn(100) 

            // Change button text to 'Search!' again            
			$('#guardian_search_terms_submit').html('Search!')           
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