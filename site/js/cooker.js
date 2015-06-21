var debug = function (value) {
  d3.select("#debug").html(value);
}

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
    return (typeof(f) === "number") ? f.toFixed(5) : f;
  };

  stateJSON['error'] = stateJSON['target'] - stateJSON['temperature'];

  d3.selectAll("#state>input")
    .property("value", function () {
      return format(stateJSON[this.id]) });
  enableInputs();

  var history = d3.select("#history").datum();
  history.push(stateJSON);
  setHistory(history);
}

var requestState = function (url) {
  url = (url) ? url : "/state";
  return d3.json(url)
    .on("load", showState)
    .on("error", function (req) {
      debug("xhr (for " + url + ") failed with status " + req.status);});
}

var getHistory = function() {
  requestState("/history")
    .on("load", setHistory)
    .get();
}

var setHistory = function(history) {
  d3.select("#history")
    .datum(history)
    .select("path")
    .each(graph);

  var recent_history = history.slice(history.length - 60);
  d3.selectAll("#history #recent path")
    .datum(recent_history)
    .each(graph);
}

var graph = function (history, i) {
  var valueName = this.id;
  var sampleTime = function (sample) { return sample.sample_time * 1000 };
  var getValue = function (sample) { return sample[valueName]; };

  var start_time = sampleTime(history[0]);
  var end_time = sampleTime(history[history.length - 1]);
  var timescale = d3.time.scale()
      .range([0,1])
      .domain([start_time, end_time]);

  var min = d3.min(history, getValue);
  var max = d3.max(history, getValue);
  var padding = (max - min) * 0.05;
  var scale = d3.scale.linear().domain([max+padding, min-padding]);

  var timeline = d3.svg.line()
      .x( function(sample) { return timescale(sampleTime(sample)) })
      .y( function(sample) { return scale(getValue(sample)) });

  d3.select(this).attr("d", timeline)

  debug("graph called for: this.id: " + this.id);
}

disableInputs();  // set tabIndex=-1 for inputs (tab won't focus to input)
enableInputs();   // remove tabIndex from settable inputs
requestState().get();
var getStateInterval = setInterval("requestState().get()", 30000);
getHistory();

