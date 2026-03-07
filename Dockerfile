FROM nikolaik/python-nodejs:python3.8-nodejs18

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ntpdate \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

RUN pip3 install --no-cache-dir --upgrade --requirement requirements.txt

# Patch pyrogram session.py directly to fix msg_id time sync issue
# The _send method uses MsgId() which calls time.time() internally
# We patch it to add server_time_offset correctly
RUN python3 -c "
import re, os

path = '/usr/local/lib/python3.8/site-packages/pyrogram/session/session.py'
with open(path, 'r') as f:
    content = f.read()

# Add NTP sync at the top of the file after imports
ntp_code = '''
import struct as _struct, socket as _socket

def _get_ntp_time():
    for srv in ['time.google.com', 'time.cloudflare.com', 'pool.ntp.org']:
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            s.settimeout(2)
            s.sendto(b\"\\x1b\" + 47 * b\"\\x00\", (srv, 123))
            d, _ = s.recvfrom(1024)
            s.close()
            t = _struct.unpack(\"!12I\", d)[10] - 2208988800
            import time as _t
            return t - int(_t.time())
        except:
            continue
    return 0

_NTP_OFFSET = _get_ntp_time()
print(f\"[SESSION] NTP offset: {_NTP_OFFSET}s\")
'''

# Insert after the last import line
lines = content.split('\n')
last_import = 0
for i, line in enumerate(lines):
    if line.startswith('import ') or line.startswith('from '):
        last_import = i

lines.insert(last_import + 1, ntp_code)
content = '\n'.join(lines)

# Patch MsgId generation to add NTP offset
# Original: msg_id = int((time() + self.server_time_offset) * 2 ** 32)
# We add _NTP_OFFSET to it
content = content.replace(
    'msg_id = int((time() + self.server_time_offset) * 2 ** 32)',
    'msg_id = int((time() + self.server_time_offset + _NTP_OFFSET) * 2 ** 32)'
)

with open(path, 'w') as f:
    f.write(content)

print('Pyrogram session.py patched successfully!')
"

CMD ["sh", "-c", "ntpdate -u time.google.com 2>/dev/null || true; python3 main.py"]
