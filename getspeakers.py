import requests
import json
import base64
import os

url = 'http://localhost:50021'

try:
    response = requests.get('{}/speakers'.format(url))
except requests.ConnectionError:
    print("No connection")
    exit()
if response.status_code == 200 and 'application/json' \
            in response.headers.get('Content-Type', ''):
    with open('speakers.json', 'bw') as f:
        f.write(response.content)


with open('speakers.json') as j:
    data = json.load(j)
speakeruuid = ([item["speaker_uuid"] for item in data])


for i in speakeruuid:
    params = {
            'speaker_uuid': i
        }
    try:
        response = requests.get('{}/speaker_info'.format(url), params=params)
    except requests.ConnectionError:
        print("No connection")
        exit()

    if response.status_code == 200 and 'application/json' \
            in response.headers.get('Content-Type', ''):
        path = 'speakers/{}'.format(i)
        if not os.path.exists(path):
            os.makedirs(path)

        with open('speakers/{}/{}.json'.format(i, i), 'bw') as f:
            f.write(response.content)

        with open('speakers/{}/{}.json'.format(i, i)) as j:
            decodedj = json.load(j)

        image_binary = base64.b64decode(decodedj["portrait"])
        with open('speakers/{}/{}.png'.format(i, i), 'wb') as f:
            f.write(image_binary)
