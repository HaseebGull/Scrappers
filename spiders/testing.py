data = '''{
  "client" : "someone";
  "server" : ["s1"; "s2"];
  "timestamp" : 1000000;
  "content" : "hello; world"
}'''

import json
dec = json.JSONDecoder(strict=False).decode(data.replace(';', '\t,'))
enc = json.dumps(dec)
out = json.loads(enc.replace('\\t,  ' ' '))
print(out)