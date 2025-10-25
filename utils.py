import base64, os
from flask import url_for

def _dict_to_namespace(data):
    class Namespace:
        def __init__(self, **entries):
            self.__dict__.update(entries)
    return Namespace(**data)

def _static_file_to_datauri(filename):
    static_path = os.path.join('static', filename)
    if not os.path.exists(static_path):
        return url_for('static', filename=filename)
    with open(static_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    ext = filename.split('.')[-1]
    return f"data:image/{ext};base64,{data}"
