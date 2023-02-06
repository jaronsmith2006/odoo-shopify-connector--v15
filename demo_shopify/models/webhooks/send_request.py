import requests
import json
webhook_url = 'http://127.0.0.1:5000/test_webhook'
data = {'name': 'TANVI'}
requests.post(webhook_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
