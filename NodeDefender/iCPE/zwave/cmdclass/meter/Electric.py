def Fields():
    return {'type' : 'value', 'readonly' : True, 'name' : 'watt'}

def Event(payload):
    payload.name = 'watt'
    payload.value = int(payload.data32, 0) / 10
    return payload