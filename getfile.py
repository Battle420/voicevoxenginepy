import requests


def simplesynthesis(url, speaker):
    site = url

    headers = {
        'Content-Type': 'application/json',
    }

    params = {
        'speaker': speaker,
    }

    with open('query.json') as f:
        data = f.read().encode('utf-8')

    try:
        response = requests.post(f'{site}/synthesis', params=params,
                                 headers=headers, data=data)
    except requests.ConnectionError:
        print("No connection")
        exit()

    if response.status_code == 200 and 'audio/wav' \
            in response.headers.get('Content-Type', ''):
        with open('audio.wav', mode='bw') as f:
            f.write(response.content)
