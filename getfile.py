import requests
headers = {
    'Content-Type': 'application/json',
}

params = {
    'speaker': '1',
}


with open('query.json') as f:
    data = f.read().encode('utf-8')

try:
    response = requests.post('http://localhost:50021/synthesis', params=params,
                             headers=headers, data=data)
except requests.ConnectionError:
    print("No connection")
    exit()

if response.status_code == 200 and 'audio/wav' \
        in response.headers.get('Content-Type', ''):
    with open('audio.wav', mode='bw') as f:
        f.write(response.content)
