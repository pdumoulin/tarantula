
var sendCodes = function (actions) {
  JSON.parse(actions).forEach(function (action) {
    sendCode(action[0], action[1]);
  });
};

var sendCode = function (remote, button) {
  var xhr = new XMLHttpRequest();
  var url = 'ir_press?remote=' + encodeURI(remote) + '&button=' + encodeURI(button);
  xhr.open('GET', url)
  xhr.onload = function (response) {
    var responseCode = response.target.status;
    if (responseCode !== 200) {
      alert('Error! response code was ' + responseCode + ' for ' + remote + '_' + button);
    }
  };
  xhr.send();
};
