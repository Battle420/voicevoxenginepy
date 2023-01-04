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

        styleids = decodedj['style_infos']

        index = -1
        for x in styleids:
            index = index + 1
            icon_binary = base64.b64decode(x['icon'])
            styleindex = decodedj['style_infos'][index]['id']
            path = 'speakers/{}/styles/{}'.format(i, styleindex)

            if not os.path.exists(path):
                os.makedirs(path)

            with open('{}/{}.png'.format(path, styleindex), 'bw') as f:
                f.write(icon_binary)

            samples = (decodedj['style_infos'][index]['voice_samples'])
            sampleindex = -1
            for y in samples:
                sampleindex = sampleindex + 1
                samplebinary = base64.b64decode(samples[sampleindex])

                with open('{}/sample{}.wav'.format(path, sampleindex), 'bw') \
                        as f:
                    f.write(samplebinary)
