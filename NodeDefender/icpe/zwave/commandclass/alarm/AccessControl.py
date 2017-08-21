icons = {'16' : 'fa fa-bell', '17' : 'fa fa-bell-slash-o',\
         '1' : 'fa fa-bell', '0' : 'fa fa-bell-slash-o'}

field = {'type' : bool, 'readonly' : True, 'name' : 'Door/Window'}

info = {'number' : '06', 'name' : 'AccessControl', 'commandclass' : 'alarm'}

def event(payload):
    data = {'field' : field, 'info' : info}
    data['value'] = payload['evt']
    data['state'] = True if data['value'] == '16' else False
    data['icon'] = icons[data['value']]
    return data

def icon(value):
    return icons[value]
