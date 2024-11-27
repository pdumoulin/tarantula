var buttonPress = function (index) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', encodeURI('remote/' + index));
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.onload = function () {
        if (xhr.status === 204) {
            // TODO - update button colors
        }
        else {
            alert('Error! response code was ' + xhr.status);
        }
    };
    xhr.send();
};
