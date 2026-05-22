(function () {
    var RETURN_PREFIX = '_~_~RETURN~_~_';
    var token = '__STREAM_TOKEN__';

    window.callbackFunction = function (msg) {
        if (ws && ws.readyState === 1) ws.send(msg);
    };

    var ws;
    function connect() {
        ws = new WebSocket('ws://' + location.host + '/ws');
        ws.onopen = function () { ws.send(token); };
        ws.onmessage = function (e) {
            if (e.data.startsWith(RETURN_PREFIX)) {
                var result = eval(e.data.slice(RETURN_PREFIX.length));
                ws.send(RETURN_PREFIX + result);
            } else {
                eval(e.data);
            }
        };
        ws.onclose = function () {
            console.log('WebSocket closed, reconnecting in 1s...');
            setTimeout(connect, 1000);
        };
        ws.onerror = function (err) {
            console.error('WebSocket error:', err);
        };
    }
    connect();
}());
