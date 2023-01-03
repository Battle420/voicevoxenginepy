import requests
import json

try:
    response = requests.get('http://localhost:50021/speakers')
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
        response = requests.get('http://localhost:50021/speaker_info',
                                params=params)
    except requests.ConnectionError:
        print("No connection")
        exit()

        if response.status_code == 200 and 'application/json' \
                in response.headers.get('Content-Type', ''):
            with open('speakers/{}.json'.format(i), 'bw') as f:
                f.write(response.content)
