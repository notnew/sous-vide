var settableVars = ["target", "offset", "kp", "ki"];

var debug = function (value) {
  var myDIV = document.getElementById("debug");
  myDIV.innerHTML = value;
};

var disableInputs = function () {
  var stateElem = document.getElementById("state");
  stateElem.classList.add("working");

  var disable = function (input) { input.readOnly = true; };
  inputs = document.forms.state.elements;
  [].forEach.call(inputs, disable);
}

var enableInputs = function () {
  var stateElem = document.getElementById("state");
  stateElem.classList.remove("working");

  var enable = function (input) {
    if (input.classList.contains("PI-control"))
      input.readOnly = false;
  };

  inputs = document.forms.state.elements;
  [].forEach.call(inputs, enable);
}

var updateState = function () {
  var data = "";
  var varCount = settableVars.length;
  for (var i=0; i < varCount; i++) {
    name = settableVars[i];
    elem = document.getElementById(name);
    if (!elem) continue;
    if (elem.tagName.toLowerCase() == "input" && elem.value) {
      var pair = elem.name + "=" + elem.value;
      if (data)
        pair = "&" + pair;
      data += pair;
    }
  }

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/", true);
  xhr.onload = function () {
    json = JSON.parse(this.responseText);
    showState(this.responseText);
    enableInputs();
    debug("state: " + this.responseText);
  };
  xhr.send(data);
  disableInputs();
};

var showState = function (text) {
  var showStateVar = function (varName, value) {
    elem = document.getElementById(varName);
    if (!elem) return;
    if (elem.tagName.toLowerCase() == "input")
      elem.value = value;
    else
      elem.innerHTML = value;
  };

  var stateJSON = JSON.parse(text);

  var stateVars = settableVars.concat(["temperature", "setting", "proportional"]);
  var varCount = stateVars.length;
  for (var i=0; i < varCount; i++) {
    name = stateVars[i];
    showStateVar(name, stateJSON[name].toFixed(4));
  }
  var err = stateJSON['target'] - stateJSON['temperature'];
  showStateVar('error', err.toFixed(3));
};

