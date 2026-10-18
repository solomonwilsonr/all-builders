"""Native navigation integration checks; run after smoke.mjs on a debug install."""
import os
import re
import subprocess
import xml.etree.ElementTree as ET

ADB = os.environ.get('ADB', 'adb')

def adb(*args):
    return subprocess.check_output([ADB, *args], text=True, timeout=30)

def state():
    adb('shell', 'uiautomator', 'dump', '/sdcard/safeshelf-nav.xml')
    return ET.fromstring(adb('shell', 'cat', '/sdcard/safeshelf-nav.xml'))

def tap_label(label):
    node = next(n for n in state().iter('node') if n.get('text') == label or n.get('content-desc') == label)
    x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.get('bounds')))
    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))

def selected(label):
    assert any(n.get('content-desc') == f'{label}, selected' for n in state().iter('node')), f'{label} must be selected'

def back_to(label):
    # Android consumes Back to dismiss an open keyboard before navigating.
    for _ in range(2):
        adb('shell', 'input', 'keyevent', '4')
        if any(n.get('content-desc') == f'{label}, selected' for n in state().iter('node')):
            return
    raise AssertionError(f'Back must return to {label}')

adb('shell', 'am', 'start', '-n', 'org.safeshelf.android/.MainActivity', '-a', 'android.intent.action.SEND', '-t', 'text/plain', '--es', 'android.intent.extra.TEXT', 'https://www.amazon.in/dp/B0CFFBZ23F')
selected('Check')
back_to('Home')
tap_label('My Shelf')
selected('My Shelf')
tap_label('Close My Shelf')
selected('Check')
tap_label('My Shelf')
back_to('Check')
back_to('Home')
tap_label('Product link or question')
adb('shell', 'input', 'text', 'Check%smy%scharger')
tap_label('Open product check')
selected('Check')
assert any(n.get('text') == 'Check my charger' for n in state().iter('node')), 'Home question must be prefilled in Check'
back_to('Home')
print('PASS: shelf Close and Android Back return to Check; next Back returns Home; Home question is handed to Check for review.')
