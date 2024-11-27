var toggle = function (index) {
    var action = null;
    var button = document.getElementById('plug' + index);
    if (button.classList.contains('statusTrue')) {
        action = false;
    }
    if (button.classList.contains('statusFalse')) {
        action = true;
    }

    if (action !== null) {
        var xhr = new XMLHttpRequest();
        xhr.open('PATCH', encodeURI('plugs/' + index));
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.onload = function () {
            if (xhr.status === 204) {
                if (action) {
                    button.classList.replace('statusFalse', 'statusTrue');
                }
                else {
                    button.classList.replace('statusTrue', 'statusFalse');
                }
            }
            else {
                button.classList.replace('statusTrue', 'statusError');
                button.classList.replace('statusFalse', 'statusError');
            }
        };
        xhr.send(JSON.stringify({'status': action}));
    }
};
