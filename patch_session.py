import os

path = '/usr/local/lib/python3.8/site-packages/pyrogram/session/session.py'

with open(path, 'r') as f:
    content = f.read()

ntp_code = """
import struct as _struct, socket as _socket, time as _time_mod

def _get_ntp_time():
    for srv in ['time.google.com', 'time.cloudflare.com', 'pool.ntp.org']:
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            s.settimeout(2)
            s.sendto(b'\\x1b' + 47 * b'\\x00', (srv, 123))
            d, _ = s.recvfrom(1024)
            s.close()
            t = _struct.unpack('!12I', d)[10] - 2208988800
            return t - int(_time_mod.time())
        except:
            continue
    return 0

_NTP_OFFSET = _get_ntp_time()
print(f"[SESSION] NTP offset applied: {_NTP_OFFSET}s")
"""

# Insert NTP code after last import line
lines = content.split('\n')
last_import = 0
for i, line in enumerate(lines):
    if line.startswith('import ') or line.startswith('from '):
        last_import = i

lines.insert(last_import + 1, ntp_code)
content = '\n'.join(lines)

# Patch msg_id calculation to use NTP offset
old = 'msg_id = int((time() + self.server_time_offset) * 2 ** 32)'
new = 'msg_id = int((time() + self.server_time_offset + _NTP_OFFSET) * 2 ** 32)'

if old in content:
    content = content.replace(old, new)
    print("msg_id line patched!")
else:
    print("WARNING: msg_id line not found, searching...")
    for i, line in enumerate(lines):
        if 'msg_id' in line and 'server_time_offset' in line:
            print(f"  Line {i}: {line}")

with open(path, 'w') as f:
    f.write(content)

print('patch_session.py: Done!')
