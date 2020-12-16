/*
 * D3 VISUALIZATION STUFF
 *
 * Codice tratto in gran parte da:
 * https://www.d3-graph-gallery.com
 */


function formatPandasDataTime(data, formatData) {
 var formatTime = d3.timeFormat(formatData);
 var nested_data = d3.nest()
  .key(function(d) { dt = d3.isoParse(d.datetime); ymd = formatTime(dt);
    return ymd; })
  .sortKeys(d3.ascending)
  .rollup(function(leaves) {
      return d3.sum(leaves, function(d){ return 1; });
  })
  .entries(data);

  return nested_data;
}

function formatPandasData(data, type) {
  var filtered = data.filter(function(d) { return d.ua_platform != null; })
                      .filter(function(d) { return d.ua_browser != null; });
  var nested_data = d3.nest()
    .key(function(d) {
      if (type=='platform')
          {return d.ua_platform;}
      else if (type=='browser')
        {return d.ua_browser;}
    })
    .sortKeys(d3.ascending)
    .rollup(function(leaves) {
        return d3.sum(leaves, function(d){ return 1; });
    })
    .entries(filtered);

  return nested_data;
}


function drawLineFromPandas(elementId, unformattedData, formatData) {

  console.log("format data..");
  data = formatPandasDataTime(unformattedData, formatData);
  console.log("drawing the line..");
  // set the dimensions and margins of the graph
  var margin = {top: 30, right: 50, bottom: 50, left: 70},
      width = document.getElementById('vue-app-div').offsetWidth - margin.left - margin.right,
      height = window.innerHeight / 2 - margin.top - margin.bottom;

  console.log("fetching..", elementId);
  // append the svg object to the body of the page
  var svg = d3.select(elementId)
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

  console.log("using data:", data);
  // Add X axis --> it is a date format
  var x = d3.scaleTime()
    .domain(d3.extent(data, function(d) { return d3.timeParse(formatData)(d.key); }))
    .range([ 0, width ]);
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x));

  // Add Y axis
  var y = d3.scaleLinear()
    .domain([0, d3.max(data, function(d) { return d.value; })])
    .range([ height, 0 ]);
  svg.append("g")
    .call(d3.axisLeft(y));

  // Add the area
  svg.append("path")
    .datum(data)
    .attr("fill", "#cce5df")
    .attr("stroke", "#69b3a2")
    .attr("stroke-width", 1.5)
    .attr("d", d3.area()
      .x(function(d) { return x(d3.timeParse(formatData)(d.key)) })
      .y0(y(0))
      .y1(function(d) { return y(d.value) })
      )

  // Build color scale
  var myColor = d3.scaleSequential()
    .interpolator(d3.interpolateInferno)
    .domain([1,260])
}

function drawPieFromPandas(elementId, unformattedData, type) {

  data = formatPandasData(unformattedData, type)
  console.log("drawing the pie..");
  console.log(data);
  // set the dimensions and margins of the graph
  var margin = 40;
  var width = document.getElementById('vue-app-div').offsetWidth - margin - margin;
  var height = window.innerHeight / 1.5 - margin - margin;

  // The radius of the pieplot is half the width or half the height (smallest one). I subtract a bit of margin.
  var radius = Math.min(width, height) / 2 - margin

  // append the svg object to the div called 'my_dataviz'
  console.log("fetching ", elementId);
  var svg = d3.select(elementId)
    .append("svg")
      .attr("width", width)
      .attr("height", height)
    .append("g")
      .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

  // set the color scale
  var color = d3.scaleOrdinal()
    .domain(data)
    .range(d3.schemeSet2);



  // Three function that change the tooltip when user hover / move / leave a cell
  var mouseover = function(d) {
    Tooltip
      .style("opacity", 1)
    d3.select(this)
      .style("stroke", "black")
      .style("opacity", 1)
  }
  var mousemove = function(d) {
    Tooltip
      .html(d.data.key + "<br>" + d.data.value)
      .style("left", (d3.mouse(this)[0]) + "px")
      .style("top", (d3.mouse(this)[1]) + "px")
  }
  var mouseleave = function(d) {
    Tooltip
      .style("opacity", 0)
    d3.select(this)
      .style("stroke", "none")
      .style("opacity", 0.8)
  }


  console.log("using data ", data);
  // Compute the position of each group on the pie:
  var pie = d3.pie()
    .value(function(d) {return d.value; })
  var data_ready = pie(data)
  // Now I know that group A goes from 0 degrees to x degrees and so on.

  // shape helper to build arcs:
  var arcGenerator = d3.arc()
    .innerRadius(0)
    .outerRadius(radius)

  // Build the pie chart: Basically, each part of the pie is a path that we build using the arc function.
  svg
    .selectAll('mySlices')
    .data(data_ready)
    .enter()
    .append('path')
      .attr('d', arcGenerator)
      .attr('fill', function(d){ return(color(d.data.key)) })
      .attr("stroke", "black")
      .style("stroke-width", "2px")
      .style("opacity", 0.7)
    .on("mouseover", mouseover)
    .on("mousemove", mousemove)
    .on("mouseleave", mouseleave)

  // Now add the annotation. Use the centroid method to get the best coordinates
  svg
    .selectAll('mySlices')
    .data(data_ready)
    .enter()
    .append('text')
    .text(function(d){ return d.data.key})
    .attr("transform", function(d) { return "translate(" + arcGenerator.centroid(d) + ")";  })
    .style("text-anchor", "middle")
    .style("font-size", 17)

}


function drawLineWithDate(elementId, data, maxVal) {

  console.log("drawing the line..");
  // set the dimensions and margins of the graph
  var margin = {top: 30, right: 50, bottom: 50, left: 70},
      width = document.getElementById('vue-app-div').offsetWidth - margin.left - margin.right,
      height = window.innerHeight / 2 - margin.top - margin.bottom;

  console.log("fetching..", elementId);
  // append the svg object to the body of the page
  var svg = d3.select(elementId)
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

  console.log("using data:", data);
  console.log("and max values: ", maxVal);
  // Add X axis --> it is a date format
  var x = d3.scaleTime()
    .domain(d3.extent(data, function(d) { return d3.timeParse("%Y-%m-%d")(d.date); }))
    .range([ 0, width ]);
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x));

  // Add Y axis
  var y = d3.scaleLinear()
    .domain([0, maxVal])
    .range([ height, 0 ]);
  svg.append("g")
    .call(d3.axisLeft(y));

  // Add the area
  svg.append("path")
    .datum(data)
    .attr("fill", "#cce5df")
    .attr("stroke", "#69b3a2")
    .attr("stroke-width", 1.5)
    .attr("d", d3.area()
      .x(function(d) { return x(d3.timeParse("%Y-%m-%d")(d.date)) })
      .y0(y(0))
      .y1(function(d) { return y(d.value) })
      )
}

function drawLineWithNums(elementId, data, maxValX, maxValY) {
// set the dimensions and margins of the graph
var margin = {top: 30, right: 50, bottom: 50, left: 70},
    width = document.getElementById('vue-app-div').offsetWidth - margin.left - margin.right,
    height = window.innerHeight / 2 - margin.top - margin.bottom;

console.log("fetching..", elementId);
// append the svg object to the body of the page
var svg = d3.select(elementId)
  .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform",
          "translate(" + margin.left + "," + margin.top + ")");

  console.log("using data:", data);
  console.log("and max val x: ", maxValX);
  console.log("and max val y: ", maxValY);
// Add X axis --> it is a date format
var x = d3.scaleLinear()
  .domain([ 0, maxValX ])
  .range([ 0, width ]);
svg.append("g")
  .attr("transform", "translate(0," + height + ")")
  .call(d3.axisBottom(x));

// Add Y axis
var y = d3.scaleLinear()
  .domain([0, maxValY])
  .range([ height, 0 ]);
svg.append("g")
  .call(d3.axisLeft(y));

// Add the area
svg.append("path")
  .datum(data)
  .attr("fill", "#cce5df")
  .attr("stroke", "#69b3a2")
  .attr("stroke-width", 1.5)
  .attr("d", d3.area()
    .x(function(d) { return x(d.name) })
    .y0(y(0))
    .y1(function(d) { return y(d.value) })
    )

}

function drawPieBars(elementId, data, maxVal) {
  console.log("drawing the bar histogram..");
  // set the dimensions and margins of the graph
  var margin = {top: 30, right: 50, bottom: 50, left: 70},
      width = document.getElementById('vue-app-div').offsetWidth - margin.left - margin.right,
      height = window.innerHeight / 2 - margin.top - margin.bottom;

  console.log("fetching..", elementId);
  // append the svg object to the body of the page
  var svg = d3.select(elementId)
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");


  console.log("using data:", data);
  console.log("and max values: ", maxVal);
  // Add X axis
  var x = d3.scaleLinear()
  .domain([0, maxVal])
  .range([ 0, width]);
  svg.append("g")
  .attr("transform", "translate(0," + height + ")")
  .call(d3.axisBottom(x))
  .selectAll("text")
    .attr("transform", "translate(-10,0)rotate(-45)")
    .style("text-anchor", "end");

  // Y axis
  var y = d3.scaleBand()
  .range([ 0, height ])
  .domain(data.map(function(d) { return d.name; }))
  .padding(.1);
  svg.append("g")
  .call(d3.axisLeft(y))

  //Bars
  svg.selectAll("myRect")
  .data(data)
  .enter()
  .append("rect")
  .attr("x", x(0) )
  .attr("y", function(d) { return y(d.name); })
  .attr("width", function(d) { return x(d.value); })
  .attr("height", y.bandwidth() )
  .attr("fill", "#69b3a2")
}


  function drawPie(elementId, data) {
    console.log("drawing the pie..");
    // set the dimensions and margins of the graph
    var margin = 40;
    var width = document.getElementById('vue-app-div').offsetWidth - margin - margin;
    var height = window.innerHeight / 1.5 - margin - margin;

    // The radius of the pieplot is half the width or half the height (smallest one). I subtract a bit of margin.
    var radius = Math.min(width, height) / 2 - margin

    // append the svg object to the div called 'my_dataviz'
    console.log("fetching ", elementId);
    var svg = d3.select(elementId)
      .append("svg")
        .attr("width", width)
        .attr("height", height)
      .append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    // set the color scale
    var color = d3.scaleOrdinal()
      .domain(data)
      .range(d3.schemeSet2);

    console.log("using data ", data);
    // Compute the position of each group on the pie:
    var pie = d3.pie()
      .value(function(d) {return d.value; })
    var data_ready = pie(d3.entries(data))
    // Now I know that group A goes from 0 degrees to x degrees and so on.

    // shape helper to build arcs:
    var arcGenerator = d3.arc()
      .innerRadius(0)
      .outerRadius(radius)

    // Build the pie chart: Basically, each part of the pie is a path that we build using the arc function.
    svg
      .selectAll('mySlices')
      .data(data_ready)
      .enter()
      .append('path')
        .attr('d', arcGenerator)
        .attr('fill', function(d){ return(color(d.data.key)) })
        .attr("stroke", "black")
        .style("stroke-width", "2px")
        .style("opacity", 0.7)

    // Now add the annotation. Use the centroid method to get the best coordinates
    svg
      .selectAll('mySlices')
      .data(data_ready)
      .enter()
      .append('text')
      .text(function(d){ return d.data.key})
      .attr("transform", function(d) { return "translate(" + arcGenerator.centroid(d) + ")";  })
      .style("text-anchor", "middle")
      .style("font-size", 17)
  }
