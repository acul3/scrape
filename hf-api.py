import json

import requests

headers = {}
#headers = {"Authorization": f"Bearer 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"}
API_URL = "https://api-inference.huggingface.co/models/flax-community/gpt2-small-indonesian"

def query(payload):
    data = json.dumps(payload)
    response = requests.request("POST", API_URL, headers=headers, data=data)
    return json.loads(response.content.decode("utf-8"))

data = query({
    "inputs": "Sewindu sudah kita tak berjumpa, rinduku padamu sudah tak terkira. Aku cinta kamu",
    "parameters": {
        "max_new_tokens": 128,
        "top_k": 30,
        "top_p": 0.95,
        "temperature": 1.0,
        "repetition_penalty": 2.0,
    },
    "options": {
        "use_cache": True,
    }
})
print(data)