import requests
import json
import base64
import os


def updatespeakers(url):

    site = url

    try:
        response = requests.get(f'{site}/speakers')
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

    for speaker in speakeruuid:
        params = {
                'speaker_uuid': speaker
            }
        try:
            response = requests.get(f'{site}/speaker_info',
                                    params=params)
        except requests.ConnectionError:
            print("No connection")
            exit()

        if response.status_code == 200 and 'application/json' \
                in response.headers.get('Content-Type', ''):
            path = f'speakers/{speaker}'
            if not os.path.exists(path):
                os.makedirs(path)

            with open(f'speakers/{speaker}/{speaker}.json', 'bw') as f:
                f.write(response.content)

            with open(f'speakers/{speaker}/{speaker}.json') as j:
                decodedj = json.load(j)

            image_binary = base64.b64decode(decodedj["portrait"])
            with open(f'speakers/{speaker}/{speaker}.png', 'wb') as f:
                f.write(image_binary)

            styleids = decodedj['style_infos']

            index = -1
            for x in styleids:
                index = index + 1
                icon_binary = base64.b64decode(x['icon'])
                styleindex = decodedj['style_infos'][index]['id']
                path = f'speakers/{speaker}/styles/{styleindex}'

                if not os.path.exists(path):
                    os.makedirs(path)

                with open(f'{path}/{styleindex}.png', 'bw') as f:
                    f.write(icon_binary)

                samples = (decodedj['style_infos'][index]['voice_samples'])
                sampleindex = -1
                for y in samples:
                    sampleindex = sampleindex + 1
                    samplebinary = base64.b64decode(samples[sampleindex])

                    with open(f'{path}/sample{sampleindex}.wav',
                              'bw') as f:
                        f.write(samplebinary)
