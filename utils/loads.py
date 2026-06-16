import os, json, tempfile
from datetime import datetime


def _atomic_save(path, data):
    """Write data to a temp file then atomically replace the target.
    If the write fails, the original file is untouched."""
    dir_ = os.path.dirname(os.path.abspath(path)) or '.'
    try:
        fd, tmp = tempfile.mkstemp(dir=dir_, prefix='.tmp_')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            os.unlink(tmp)
            raise
        os.replace(tmp, path)  # atomic on POSIX
    except Exception as e:
        print(f"[save error] {path}: {e}")
        raise


def _load_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"[load error] {path}: {e}")
        return default


def lautomod():
    return _load_json('automod.json')

def saveauto(settings):
    _atomic_save('automod.json', settings)


def lantiswear():
    return _load_json('antiswear.json')

def saveantiswear(settings):
    _atomic_save('antiswear.json', settings)


msgs = {}


arf = 'autorespond.json'
ard = _load_json(arf)

def saveard():
    _atomic_save(arf, ard)


areactdf = 'autoreact.json'
areactd = _load_json(areactdf)

def saveareactd():
    _atomic_save(areactdf, areactd)


def lmedia(mediafile):
    data = _load_json(mediafile)
    if not isinstance(data, dict):
        return {}
    for guild_id in data:
        if not isinstance(data[guild_id], list):
            data[guild_id] = []
    return data

def savemedia(mediafile, data):
    _atomic_save(mediafile, data)

mdch = lmedia('media.json')
bymd = lmedia('mediabypass.json')


def lafk():
    return _load_json('afk.json')

def saveafk(afkd):
    _atomic_save('afk.json', afkd)

def kalaloda(iso_str):
    dt = datetime.fromisoformat(iso_str)
    return int(dt.timestamp())


autorolef = 'autorole.json'

def lautorole():
    return _load_json(autorolef)

def saveautorole(data):
    _atomic_save(autorolef, data)

autoroleconfig = lautorole()
if 'humans' not in autoroleconfig:
    autoroleconfig['humans'] = []
if 'bots' not in autoroleconfig:
    autoroleconfig['bots'] = []


antinukef = 'antinuke.json'
antid = _load_json(antinukef)

def lantinuke():
    return _load_json(antinukef)

def saveanti(data):
    _atomic_save(antinukef, data)


vcrolef = 'vcrole.json'
vcdata = _load_json(vcrolef)

def lvcrole():
    return _load_json(vcrolef)

def savevcrole(data):
    _atomic_save(vcrolef, data)


jtcf = 'jtc.json'

def ljtc():
    return _load_json(jtcf)

def savejtc(data):
    _atomic_save(jtcf, data)


welcomef = 'welcome.json'

def lwelcome():
    return _load_json(welcomef)

def savewelcome(data):
    _atomic_save(welcomef, data)


rrf = 'reactionrole.json'

def lrr():
    return _load_json(rrf)

def saverr(data):
    _atomic_save(rrf, data)