import requests


def jsonqueryget(url, speaker, text):
    site = url
    params = {
            'speaker': speaker,
            'text': text,
    }
    try:
        response = requests.post('{}/audio_query'.format(site), params=params)
    except requests.ConnectionError:
        print("No connection")
        exit()

    if response.status_code == 200 and 'application/json' \
            in response.headers.get('Content-Type', ''):
        with open('query.json', 'bw') as f:
            f.write(response.content)
