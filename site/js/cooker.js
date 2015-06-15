var debug = function (value) {
  var myDIV = document.getElementById("debug");
  myDIV.innerHTML = value;
};

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
  stateJSON['error'] = stateJSON['target'] - stateJSON['temperature'];

  var inputs = document.forms.state.elements;
  [].forEach.call(inputs, function (input) {
    if (input.id)
      input.value = stateJSON[input.id].toFixed(3);
  });
  enableInputs();
};


var getState = function () {
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/state", true);
  xhr.onload = function () {
    json = JSON.parse(this.responseText);
    showState(json);
  };
  xhr.send("");
}


disableInputs();  // set tabIndex=-1 for inputs (tab won't focus to input)
enableInputs();   // remove tabIndex from settable inputs
getState();
var getStateInterval = setInterval("getState()", 30000);

