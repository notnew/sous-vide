var settableVars = ["target", "offset", "kp", "ki"];

var debug = function (value) {
  var myDIV = document.getElementById("debug");
  myDIV.innerHTML = value;
};

var updateState = function () {
  var data = "";
  var varCount = settableVars.length;
  for (var i=0; i < varCount; i++) {
    name = settableVars[i];
    elem = document.getElementById(name);
    if (data)
      data += "&" + name + "=" + elem.value;
    else
      data = name + "=" + elem.value;
  }

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/", true);
  xhr.onload = function () {
    json = JSON.parse(this.responseText);
    showState(this.responseText);
    debug("state: " + this.responseText);
  };
  xhr.send(data);
};

var showState = function (text) {
  var showStateVar = function (varName, value) {
    elem = document.getElementById(varName);
    if (elem) {
      if (elem.value)
        elem.value = value;
      else
        elem.innerHTML = value;
    };
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

