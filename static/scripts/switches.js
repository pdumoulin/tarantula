
var reload = function () {
  document.getElementById('switches').style.display = 'none';
  location.reload();
};

var toggleLights = function (index) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', encodeURI('switches'));
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function () {
        reload();
    };
    xhr.send(encodeURI('index=' + index));
};

