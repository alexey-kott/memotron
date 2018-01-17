import json
import re
import requests as req

response = req.get("https://pikabu.ru/hot")

# print(response.text)
response = req.get("https://pikabu.ru/hot?twitmode=1&page=1&of=v2")
print(response.text)

# text = json.loads(response.text)
# text = re.sub(r'\s+', '', raw_text)

# print(json.dumps(response, indent=4, sort_keys=True))