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
  var stateElem = document.getElementById("state");
  stateElem.classList.add("working");

  var disable = function (input) {
    input.readOnly = true;
    input.tabIndex = "-1";
  };
  var inputs = document.forms.state.elements;
  [].forEach.call(inputs, disable);
}

var enableInputs = function () {
  var stateElem = document.getElementById("state");
  stateElem.classList.remove("working");

  var enable = function (input) {
    if (input.classList.contains("PI-control")) {
      input.readOnly = false;
      input.tabIndex = "0";
    }
  };

  var inputs = document.forms.state.elements;
  [].forEach.call(inputs, enable);
}

var updateState = function () {
  disableInputs();

  var stateIFrame = document.getElementsByName("hidden_iframe")[0];
  stateIFrame.onload = function (ev) {
    var text = stateIFrame.contentDocument.body.innerText;
    showState(JSON.parse(text));
  }
}

var showState = function (stateJSON) {
  var format = function (f) {
    return (typeof(f) == "number") ? f.toFixed(3) : f;
  };

  stateJSON['error'] = stateJSON['target'] - stateJSON['temperature'];

  d3.selectAll("form#state>input")
    .attr("value", function () {
      return format(stateJSON[this.id]) });
  enableInputs();
};

var getState = function () {
  var url = "/state";
  d3.json(url)
    .on("load", showState)
    .on("error", function (req) {
      debug("xhr (for " + url + ") failed with status " + req.status);})
    .get();
};

disableInputs();  // set tabIndex=-1 for inputs (tab won't focus to input)
enableInputs();   // remove tabIndex from settable inputs
getState();
var getStateInterval = setInterval("getState()", 30000);

