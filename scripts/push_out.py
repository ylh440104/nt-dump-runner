import base64
import glob
import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ.get("OUT_TOKEN")
REPO = "ylh440104/nt-dump-out"
OUT = os.environ.get("OUT_DIR", "out")
CHUNK = 24 * 1024 * 1024


def api(method, path, body=None):
    url = "https://api.github.com/repos/%s/%s" % (REPO, path)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "token " + TOKEN,
        "Accept": "application/vnd.github+json",
        "User-Agent": "nt-dump",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def push(name, blob):
    b64 = base64.b64encode(blob).decode()
    st, cur = api("GET", "contents/" + name)
    sha = cur["sha"] if st == 200 else None
    body = {"message": "add " + name, "content": b64, "branch": "main"}
    if sha:
        body["sha"] = sha
    return api("PUT", "contents/" + name, body)


files = sorted(glob.glob(os.path.join(OUT, "*.tsv"))) + sorted(glob.glob(os.path.join(OUT, "*.c")))
print("files:", [os.path.basename(f) for f in files])
for p in files:
    raw = open(p, "rb").read()
    base = os.path.basename(p)
    if len(raw) <= CHUNK:
        st, res = push(base, raw)
        print(base, len(raw), st)
    else:
        n = 0
        for i in range(0, len(raw), CHUNK):
            part = base + ".part%02d" % n
            st, res = push(part, raw[i:i + CHUNK])
            print(part, len(raw[i:i + CHUNK]), st)
            n += 1
