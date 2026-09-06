"""临时脚本：通过 CDP 抓取错误页截图，供 README 使用。"""
import base64
import json
import os
import time
import urllib.request

import websocket

BASE = 'http://127.0.0.1:8000'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'screenshots')


def ws_url():
    with urllib.request.urlopen('http://127.0.0.1:9333/json/version', timeout=10) as r:
        return json.load(r)['webSocketDebuggerUrl']


class Session:
    def __init__(self):
        self.browser = websocket.create_connection(ws_url(), timeout=30)
        resp = self._send('Target.createTarget', url='about:blank')
        self.session_id = None
        self.target_id = resp['result']['targetId']
        resp = self._send('Target.attachToTarget', targetId=self.target_id, flatten=True)
        self.session_id = resp['result']['sessionId']

    def _send(self, method, **params):
        self._id = getattr(self, '_id', 0) + 1
        self.browser.send(json.dumps({'id': self._id, 'method': method, 'params': params}))
        while True:
            msg = json.loads(self.browser.recv())
            if msg.get('id') == self._id:
                return msg

    def send(self, method, **params):
        self._id = getattr(self, '_id', 0) + 1
        payload = {'id': self._id, 'method': method, 'params': params, 'sessionId': self.session_id}
        self.browser.send(json.dumps(payload))
        while True:
            msg = json.loads(self.browser.recv())
            if msg.get('id') == self._id:
                if 'error' in msg:
                    raise RuntimeError(f'{method}: {msg["error"]}')
                return msg.get('result', {})

    def evaluate(self, expr):
        res = self.send('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        return res.get('result', {}).get('value')

    def goto(self, url):
        self.send('Page.navigate', url=url)
        time.sleep(2.5)

    def shot(self, name):
        res = self.send('Page.captureScreenshot', format='png')
        data = base64.b64decode(res['data'])
        with open(os.path.join(OUT, name), 'wb') as f:
            f.write(data)
        print(f'{name}: {len(data) // 1024} KB')


def main():
    s = Session()
    s.send('Page.enable')
    s.send('Runtime.enable')
    s.send('Emulation.setDeviceMetricsOverride', width=1920, height=1080, deviceScaleFactor=1, mobile=False)
    s.goto(BASE + '/not-exist-page')
    print('title:', s.evaluate('document.title'))
    s.shot('error-404.png')


if __name__ == '__main__':
    main()
