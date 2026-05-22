# Changelog

## v4.0.0

### New Features

- **`StreamChart`** — browser-based chart served over HTTP/WebSocket.
  - `StreamChart` starts a FastAPI + uvicorn server; open the printed URL in any browser.
  - Requires optional dependencies: `pip install lightweight-charts[stream]`
  - Token-authenticated WebSocket handshake (close 4001 on auth failure).
  - Automatic script replay on browser reconnect.
  - `run_script_and_get` supported with 5-second timeout.
  - Single-client guard (close 4002 on second simultaneous connection).
  - `Content-Security-Policy` header on `stream.html` response.
  - Network-access warning when binding to a non-loopback host.
