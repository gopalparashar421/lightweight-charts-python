(function () {
    var RETURN_PREFIX = '_~_~RETURN~_~_';
    var token = '__STREAM_TOKEN__';
    var MAX_RELOADS = 5;
    var RELOAD_KEY = 'lwcStreamReloadCount';

    window.callbackFunction = function (msg) {
        if (ws && ws.readyState === 1) ws.send(msg);
    };

    var ws;
    var established = false;

    function connect() {
        established = false;
        var scheme = location.protocol === 'https:' ? 'wss://' : 'ws://';
        ws = new WebSocket(scheme + location.host + '/ws');
        ws.onopen = function () {
            established = true;
            try { sessionStorage.removeItem(RELOAD_KEY); } catch (e) {}
            ws.send(token);
        };
        ws.onmessage = function (e) {
            if (e.data.startsWith(RETURN_PREFIX)) {
                var result = eval(e.data.slice(RETURN_PREFIX.length));
                ws.send(RETURN_PREFIX + result);
            } else {
                eval(e.data);
            }
        };
        ws.onclose = function (ev) {
            // 4002 = single-client guard — short backoff + retry, not reload
            // (avoids reload storms while the previous socket is clearing).
            if (ev && ev.code === 4002) {
                console.log('WebSocket rejected (4002), retrying in 500ms...');
                setTimeout(connect, 500);
                return;
            }
            if (established) {
                var count = 0;
                try {
                    count = parseInt(sessionStorage.getItem(RELOAD_KEY) || '0', 10) || 0;
                } catch (e) {}
                if (count < MAX_RELOADS) {
                    try { sessionStorage.setItem(RELOAD_KEY, String(count + 1)); } catch (e) {}
                    console.log('WebSocket closed after session; reloading for fresh context...');
                    location.reload();
                    return;
                }
                try { sessionStorage.removeItem(RELOAD_KEY); } catch (e) {}
                console.log('WebSocket closed; reload bound exceeded, retrying in 2s...');
                setTimeout(connect, 2000);
                return;
            }
            console.log('WebSocket closed, reconnecting in 1s...');
            setTimeout(connect, 1000);
        };
        ws.onerror = function (err) {
            console.error('WebSocket error:', err);
        };
    }
    connect();
}());
