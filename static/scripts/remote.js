
var sendCode = function (remote, button) {
  var xhr = new XMLHttpRequest();
  var url = 'ir_press?remote=' + encodeURI(remote) + '&button=' + encodeURI(button);
  xhr.open('GET', url)
  xhr.onload = function (response) {
    var responseCode = response.target.status;
    if (responseCode !== 200) {
      alert('Error! response code was ' + responseCode);
    }
  };
  xhr.send();
};
