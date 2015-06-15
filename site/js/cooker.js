var debug = function (value) {
  var myDIV = document.getElementById("debug");
  myDIV.innerHTML = value;
};

var disableInputs = function () {
  var stateElem = document.getElementById("state");
  stateElem.classList.add("working");

  var disable = function (input) { input.readOnly = true; };
  var inputs = document.forms.state.elements;
  [].forEach.call(inputs, disable);
}

var enableInputs = function () {
  var stateElem = document.getElementById("state");
  stateElem.classList.remove("working");

  var enable = function (input) {
    if (input.classList.contains("PI-control"))
      input.readOnly = false;
  };

  var inputs = document.forms.state.elements;
  [].forEach.call(inputs, enable);
}

var updateState = function () {
  disableInputs();

  var stateIFrame = document.getElementsByName("hidden_iframe")[0];
  stateIFrame.onload = function (ev) {
    var text = stateIFrame.contentDocument.body.innerText;
    showState(text);
  }
}

var showState = function (text) {
  var stateJSON = JSON.parse(text);
  stateJSON['error'] = stateJSON['target'] - stateJSON['temperature'];

  var inputs = document.forms.state.elements;
  [].forEach.call(inputs, function (input) {
    if (input.id)
      input.value = stateJSON[input.id].toFixed(4);
  });
  enableInputs();
};

