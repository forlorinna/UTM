"""Serve the downloaded, self-contained walk build on this computer only."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Timer
import webbrowser

parser=argparse.ArgumentParser()
parser.add_argument('--port',type=int,default=4270)
parser.add_argument('--no-open',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parent
if not (root/'index.html').is_file():
    root=root/'dist'
if not (root/'index.html').is_file():
    raise SystemExit('index.html missing. Extract the walk build first.')
handler=functools.partial(SimpleHTTPRequestHandler,directory=str(root))
with ThreadingHTTPServer(('127.0.0.1',args.port),handler) as server:
    url=f'http://127.0.0.1:{server.server_port}/'
    print(url,flush=True)
    if not args.no_open:
        Timer(.35,webbrowser.open,args=[url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
