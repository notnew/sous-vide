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
    return (typeof(f) === "number") ? f.toFixed(5) : f;
  };

  stateJSON['error'] = stateJSON['target'] - stateJSON['temperature'];

  d3.selectAll("#state>input")
    .property("value", function () {
      return format(stateJSON[this.id]) });
  enableInputs();

  d3.select("svg.history")
    .datum( function (history) {
      history.push(stateJSON);
      return history;
    });

  graph();
};

var requestState = function (url) {
  url = (url) ? url : "/state";
  return d3.json(url)
    .on("load", showState)
    .on("error", function (req) {
      debug("xhr (for " + url + ") failed with status " + req.status);});
};

var getHistory = function() {
  requestState("/history")
    .on("load", function (history) {
      d3.select("#history").datum(history);
      graph();
    })
    .get();
}

var graph = function () {
  var graphs = d3.select("#history");
  var history = graphs.datum();

  var sampleTime = function (sample) { return sample.sample_time * 1000 };

  var start_time = sampleTime(history[0]);
  var end_time = sampleTime(history[history.length - 1]);
  var timescale = d3.time.scale()
      .range([0,1])
      .domain([start_time, end_time]);

  var timeline =   function (id) {
    var min = d3.min(history, function (sample) { return sample[id]; });
    var max = d3.max(history, function (sample) { return sample[id]; });
    var range = max - min;
    min = min - (0.05 * range);
    max = max + (0.05 * range);
    var scale = d3.scale.linear().domain([max, min]);
    return d3.svg.line()
      .x( function(sample) { return timescale(sampleTime(sample)) })
      .y( function(sample) {
        return scale(sample[id]) });
  }

  graphs.select("#temperatures path.temperature")
        .attr("d", timeline('temperature', 70, 110));

  graphs.select("#recent").select("path.target")
        .attr("d", timeline('target', 70, 110));

  graphs.select("#recent path.heater")
        .attr("d", timeline('setting', 0, 1));

}

disableInputs();  // set tabIndex=-1 for inputs (tab won't focus to input)
enableInputs();   // remove tabIndex from settable inputs
requestState().get();
var getStateInterval = setInterval("requestState().get()", 30000);
getHistory();

