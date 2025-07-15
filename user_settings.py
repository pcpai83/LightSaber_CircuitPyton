# user_settings.py

import json

default_settings = {
    "COR": 3,  # AQUA
    "Brilho": 2,  # Max
    "Volume": 2,  # Med
    "Swing": 1,  # Med
    "Clash": 1,  # Med
    "Anim": 0,  # On
}

def load_settings(path="/settings.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Settings padrão carregado:", e)
        return default_settings.copy()

def save_settings(settings, path="/settings.json"):
    import storage
    with open(path, "w") as f:
        json.dump(settings, f)