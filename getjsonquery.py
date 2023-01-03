import requests
params = {
        'speaker': '1',
        'text': 'こんにちは、音声合成の世界へようこそ',
}
try:
    response = requests.post('http://localhost:50021/audio_query',
                             params=params)
except requests.ConnectionError:
    print("No connection")
    exit()

if response.status_code == 200 and 'application/json' \
     in response.headers.get('Content-Type', ''):
    with open('query.json', 'bw') as f:
        f.write(response.content)
