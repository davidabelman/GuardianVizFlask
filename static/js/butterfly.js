COUNT = 0
ITERATION = 0

function make_nodes_hoverable(hoverout) {
  // This is run at each iteration (i.e. when new nodes are added)
  // This will ensure that when a node is hovered:
  //  --we display headline and story info in the panel
        d3.selectAll('.node').on('mouseover', 
          function(d) {
            update_panel(d)  // Which will extract d.headline, d.strapline etc. and display in the side panel
          })
        if (hoverout) {
          d3.selectAll('.node').on('mouseout', 
          function(d) {
            clearpanel(d)  // Which will extract d.headline, d.strapline etc. and display in the side panel
          })
        }
}

function update_panel(d) {
  // Add article data to panel (e.g. on hover over)
  $('#headline').text(d.headline)
  $('#strapline').text(d.strapline)
  $('#date').text(d.date)
}
function clearpanel(d) {
  // Remove article data from panel (e.g. on hover out)
  $('#headline').text('')
  $('#strapline').text('')
  $('#date').text('')
}

function make_nodes_clickable() {
  // This is run at each iteration (i.e. when new nodes are added)
  // This will ensure that when a node is clicked:
  //  --we run AJAX to get related nodes
  //  --the new nodes are pushed to the nodes/links matrix
  //  --the clicked node has its colour changed

    $(".node").click( function(e) {
      // Remove previous 'make_circles_clickable' action
      // (so we don't get multiple nodes added)
      e.preventDefault();
      e.stopImmediatePropagation();      

      // If node already clicked, do nothing
      var class_clicked = $(this).attr('class')
      console.log("Clicked class:", class_clicked)
      if (class_clicked.search('clicked')>=0) {
        return false
      }

      // Set force charge and friction
      // Initialsed previously with weak charge to avoid bouncing off screen
        setTimeout( function() {
          force.charge(-3000).friction(0.7).linkDistance(170)
        },1000)
      

      // Detect what was clicked
      var id_clicked = $(this).attr('id')
      console.log("Clicked id:", id_clicked)      

      // Pick the node we just clicked
      var clicked_node = nodes.filter( function(n) {return n.id==id_clicked} )[0]
      console.log("Data of clicked:", clicked_node)
      
      // Create new nodes based on AJAX call (TODO)
      COUNT += 1
      var new_node = {id: String(COUNT),
                      headline:'Vietnam awarded top country'+String(COUNT),
                      strapline:'The strapline data goes here too',
                      date:'3 Jun 2013',
                      date_difference:'+4 days'
                    }    
      COUNT += 1
      var new_node_2 = {id: String(COUNT), 
                      headline:'China enters waters'+String(COUNT),
                      strapline:'The strapline data goes here too',
                      date:'6 Jun 2013',
                      date_difference:'+2 days'
                    }  
      COUNT += 1
      var new_node_3 = {id: String(COUNT),
                      headline:'Yen down against Dong'+String(COUNT),
                      strapline:'The strapline data goes here too',
                      date:'1 Jun 2013',
                      date_difference:'+17 days'
                    }    
      
      // Add the new node(s) and connect to an old node
      nodes.push(new_node, new_node_2, new_node_3);
      links.push(
        {source: clicked_node, target: new_node},
        {source: clicked_node, target: new_node_2},
        {source: clicked_node, target: new_node_3});

      // Add 'clicked' class to node just clicked
      var current_classes = $('#'+id_clicked).attr('class')
      var new_classes = current_classes + ' clicked'
      $('#'+id_clicked).attr('class', new_classes)

      // Recalculate
      start();
  })
}


function start() {
  // This loops through data and creates 'g' groups for all added elements on each iteration of the code
  // Also alters formatting and SVG size
  ITERATION+=1

  // Increase size of SVG by 5% on each run through, just to allow more room for network
  height = height*1.05
  width = width*1.05
  svg.attr('height', height).attr('width', width)

  // Remove 'fresh_node_label' class from all text
  // Previously class would be 'fresh_node_label link_label'
  // Change to just 'link_label'
  // We will then add 'fresh_node_label' to new ones only, they will be bold
  $('.fresh_node_label').attr('class', 'node_label')

  // Links and link labels
  link = link.data(force.links(),function(d) { return d.source.id + "-" + d.target.id; });

  // Link labels
  link
    .enter()
    .append('g')
    .attr('class','link_label_group')  
    .append('text')
    .attr("dx", 12)
    .attr("dy", ".35em")  
    .attr('class', 'link_label')
    .text(function(d){return d.target.date_difference});
  
  // Links
  link
    .enter()
    .append('g')
    .attr('class', 'link_group')
    .insert("line", "g")
    .attr("class", "link");

  link.exit().remove();

  // Nodes and node labels
  node = node.data(force.nodes(), function(d) { return d.id;});

  // Node labels
  if (ITERATION==1) {
  // First iteration, make the label blue by adding #starter_label ID
  node   
    .enter()
    .append('g')
    .attr('class','node_label_group')     
    .append('text')
    .attr('class', 'node_label fresh_node_label') 
    .attr('id', 'starter_label')
    .text(function(d) { return d.headline });
  }
  else {
  // Other iterations, don't add ID of #starter_label
  node   
    .enter()
    .append('g')
    .attr('class','node_label_group')     
    .append('text')
    .attr('class', 'node_label fresh_node_label') 
    .text(function(d) { return d.headline });
  }

  // Node labels (dates)
  node   
    .enter()
    .append('g')
    .attr('class','node_label_group')     
    .append('text')
    .attr('class', 'node_date') 
    .text(function(d) { return d.date });

  // Nodes
  node
    .enter()
    .append('g')
    .attr('class','node_group')
    .append("circle")
    .attr("class", function(d) { return "node"})
    .attr("id", function(d) { return d.id; })    
    .attr("r", 16)
    .call(force.drag);

  node.exit().remove();

  force.start();
  make_nodes_clickable()
  make_nodes_hoverable(hoverout=false)

}

function tick() {
  // This runs on every tick of the animation, moving around the positions of nodes/text etc.
  // Node positions
  var shift_x = ITERATION*10
  var shift_y = ITERATION*20


  svg
    .selectAll('.node')
    .attr("cx", function(d) { return d.x + shift_x; })
    .attr("cy", function(d) { return d.y + shift_y; })

  // Node label positions
  svg
    .selectAll('.node_label')
    .attr("x", function(d) { return d.x+19 + shift_x; })
    .attr("y", function(d) { return d.y+9 + shift_y; })

  // Node date label positions
  svg
    .selectAll('.node_date')
    .attr("x", function(d) { return d.x+19 + shift_x; })
    .attr("y", function(d) { return d.y-4 + shift_y; })

  // Line positions
  svg
    .selectAll('.link')
    .attr("x1", function(d) { return d.source.x + shift_x; })
    .attr("y1", function(d) { return d.source.y + shift_y; })
    .attr("x2", function(d) { return d.target.x + shift_x; })
    .attr("y2", function(d) { return d.target.y + shift_y; });

  // Line label positions
  svg
    .selectAll('.link_label')
    .attr("x", function(d) { return ((d.source.x+d.target.x)/2)-5 + shift_x; })
    .attr("y", function(d) { return (d.source.y+d.target.y)/2 + shift_y; })
}



// *********** Run on script start ***********
// SVG height an width
var width = $(window).width()*1.05,
    height = $(window).height()*1.05;

var nodes = [],
    links = [];

// Set physics options
var force = d3.layout.force()
      .nodes(nodes)
      .links(links)
      .charge(-170)
      .friction(0.4)
      .linkDistance(220)
      .size([width, height])
      .on("tick", tick);

// Create SVG
var svg = d3.select("#butterfly_pane").append("svg")
    .attr("width", width)
    .attr("height", height);

var node = svg.selectAll(".node"),
    link = svg.selectAll(".link");

// First of all, add initial node
var a = {id: "starter",
        headline:'This is a headline',
        strapline:'The strapline data goes here too',
        date:'1 Feb 2012'};
nodes.push(a);
links.push();
start();


