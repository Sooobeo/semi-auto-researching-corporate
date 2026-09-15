"""Probe OpenDART without logging the API key or authenticated URLs."""

import io
import json
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


def env_values() -> dict[str, str]:
    result = {}
    for line in Path('.env').read_text(encoding='utf-8').splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            result[key] = value.strip()
    return result


def main() -> None:
    env = env_values()
    key = env.get('OPENDART_API_KEY', '')
    if not key:
        print('OpenDART key missing')
        return
    url = env['OPENDART_BASE_URL'].rstrip('/') + '/corpCode.xml?'
    url += urllib.parse.urlencode({'crtfc_key': key})
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            status = response.status
    except Exception as exc:
        print('OpenDART request failed:', type(exc).__name__)
        return
    if not zipfile.is_zipfile(io.BytesIO(data)):
        try:
            body = json.loads(data)
            print('OpenDART response:', body.get('status'), body.get('message'))
        except (ValueError, UnicodeDecodeError):
            print('OpenDART unexpected response, bytes:', len(data))
        return
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        print('OpenDART connected:', status, 'ZIP bytes:', len(data), 'entries:', archive.namelist())


if __name__ == '__main__':
    main()
