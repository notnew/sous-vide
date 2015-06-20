var debug = function (value) {
  d3.select("#debug").html(value);
};

var debugObj = function (obj) {
  try {
    dbg = "";
    for (x in obj) {
      dbg += x + ": " + obj[x] + "<br>";
    }
    debug(dbg);
  } catch (e) {
    debug(e);
  }
}

var disableInputs = function () {
  d3.select("#state").classed("working", true)

  d3.selectAll("#state>input")
    .attr("readOnly", true)
    .attr("tabIndex", -1);
}

var enableInputs = function () {
  d3.selectAll("#state").classed("working", false)

  d3.selectAll("#state>input.PI-control")
    .attr("readOnly", null)
    .attr("tabIndex", "0");
}

var updateState = function () {
  disableInputs();

  var pairs = [];
  d3.selectAll("#state>input.PI-control").each(function () {
    pairs.push(this.id + "=" + this.value); });

  requestState().post(pairs.join("&"));

  return false;
}

var showState = function (stateJSON) {
  var format = function (f) {
    return (typeof(f) === "number") ? f.toFixed(3) : f;
  };

  stateJSON['error'] = stateJSON['target'] - stateJSON['temperature'];

  d3.selectAll("#state>input")
    .property("value", function () {
      return format(stateJSON[this.id]) });
  enableInputs();
};

var requestState = function (url) {
  url = (url) ? url : "/state";
  return d3.json(url)
    .on("load", showState)
    .on("error", function (req) {
      debug("xhr (for " + url + ") failed with status " + req.status);});
};

var graph = function (url) {
  var _graph = function (history) {
    chart = d3.select("svg.history")
      .datum( [[0, 0], [50, 50]])
      .datum(history);

    var sampleTime = function (state) { return state.sample_time * 1000 };

    var start_time = sampleTime(history[0]);
    var end_time = sampleTime(history[history.length - 1]);
    var svg_width = chart.property("width").baseVal.value;
    var svg_height = chart.attr("height");

    debugObj(svg_width);
    var timescale = d3.time.scale()
        .range([0,1])
        .domain([start_time, end_time]);

    var tempscale = d3.scale.linear()
        .range([0,1])
        .domain([110, 70]);

    temps = d3.svg.line()
      .x( function(state) { return timescale(sampleTime(state)) })
      .y( function(state) { return tempscale(state.temperature) });

    chart.select("path.temperature")
        .attr("d", temps);
  }

  requestState("/history")
      .on("load", _graph)
      .get();
}

disableInputs();  // set tabIndex=-1 for inputs (tab won't focus to input)
enableInputs();   // remove tabIndex from settable inputs
requestState().get();
var getStateInterval = setInterval("requestState().get()", 30000);
var graphInterval = setInterval("graph()", 60000);

graph();
