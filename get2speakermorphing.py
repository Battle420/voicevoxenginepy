import requests


def synthesismorphing(url, speaker1, speaker2, morphrate):
    site = url
    headers = {
        'Content-Type': 'application/json',
    }

    params = {
        'base_speaker': speaker1,
        'target_speaker': speaker2,
        'morph_rate': morphrate
    }

    with open('query.json') as f:
        data = f.read().encode('utf-8')

    try:
        response = requests.post('{}/synthesis_morphing'.format(site),
                                 params=params, headers=headers, data=data)
    except requests.ConnectionError:
        print("No connection")
        exit()

    if response.status_code == 200 and 'audio/wav' \
            in response.headers.get('Content-Type', ''):
        with open('audio.wav', mode='bw') as f:
            f.write(response.content)
