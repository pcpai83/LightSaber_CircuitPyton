import json
import audiocore
import time
import supervisor
import storage
# Verifica status USB e ajusta comportamento


def settings_menu(
    mixer, 
    pixels, 
    set_rgb_led, 
    COLORS, 
    switch,
    pin2, 
    user_settings, 
    VOLUMES, 
    PixelSubset, 
    WHITE
):
    SETTINGS = [
        {
            "name": "COR",
            "values": [
                ("Red", COLORS[0]),
                ("Orange", COLORS[1]),
                ("Amber", COLORS[2]),
                ("Aqua", COLORS[3]),
                ("Jade", COLORS[4]),
                ("Magenta", COLORS[5]),
                ("Teal", COLORS[6]),
                ("Gold", COLORS[7]),
                ("Yellow", COLORS[8]),
                ("Green", COLORS[9]),
                ("Cyan", COLORS[10]),
                ("Blue", COLORS[11]),
                ("Purple", COLORS[12]),
            ],
            "sound": "Color.wav",
        },
        {
            "name": "Brilho",
            "values": [("Min", 0.1), ("Med", 0.5), ("Max", 0.8)],
            "sound": "Brightness.wav",
        },
        {
            "name": "Volume",
            "values": [("Off", 0.0), ("Min", 0.1), ("Med", 0.5), ("Max", 1.0)],
            "sound": "Volume.wav",
        },
        {
            "name": "Swing",
            "values": [("Min", 260), ("Med", 130), ("Max", 65)],
            "sound": "Swing.wav",
        },
        {
            "name": "Clash",
            "values": [("Min", 127), ("Med", 100), ("Max", 60)],
            "sound": "Clash.wav",
        },
        {
            "name": "Anim",
            "values": [("On", True), ("Off", False)],
            "sound": "Anim.wav",
        },
    ]
    from user_settings import save_settings
    option_idx = 0
    value_idxs = [
        user_settings.get("COR", 0),
        user_settings.get("Brilho", 2),
        user_settings.get("Volume", 2),
        user_settings.get("Swing", 1),
        user_settings.get("Clash", 1),
        user_settings.get("Anim", 0),
    ]
    in_option = False

    def play_setting_wav(filename, loop=False, voice=1, level=0.8):
        try:
            wave_file = open(f"/s_settings/{filename}", "rb")
            wave = audiocore.WaveFile(wave_file)
            #mixer.voice[voice].stop()
            mixer.voice[voice].play(wave, loop=loop)
            if level is not None:
                mixer.voice[voice].level = level
        except Exception as e:
            print("Erro ao tocar som:", filename, e)

    def ensure_background():
        if not mixer.voice[0].playing:
            play_setting_wav("Settings_backsound.wav", loop=True, voice=0)

    play_setting_wav("Settings.wav", loop=False, voice=1)
    play_setting_wav("Settings_backsound.wav", loop=True, voice=0)
    while mixer.voice[1].playing:
        time.sleep(0.1)
    play_setting_wav(SETTINGS[option_idx]["sound"], voice=1)
    current_color = SETTINGS[0]["values"][value_idxs[0]][1]
    pixels.fill(current_color)
    set_rgb_led(current_color)
    pixels.show()

    while True:
        switch.update()
        ensure_background()

        storage.remount("/", readonly=False)

        # Muda para o próximo setting com long press
        if switch.long_press:
            option_idx = (option_idx + 1) % len(SETTINGS)
            # Para qualquer som anterior na voz 0
            mixer.voice[1].stop()
            # Toca o som do setting na voz 1
            play_setting_wav(SETTINGS[option_idx]["sound"], voice=1)
            # Toca imediatamente o som do valor na mesma voz (o valor irá sobrepor o nome do setting se pressionar rápido, mas a navegação fica instantânea)
            value_label = SETTINGS[option_idx]["values"][value_idxs[option_idx]][0]
            if mixer.voice[1].playing:
                pass # Se já estiver tocando, não toca novamente
            else:
                play_setting_wav(value_label + ".wav", voice=1)
            in_option = False
            time.sleep(0.3)  # debounce


        # Muda o valor do setting atual com short press
        if switch.short_count == 1:
            

            value_count = len(SETTINGS[option_idx]["values"])
            value_idxs[option_idx] = (value_idxs[option_idx] + 1) % value_count
            value_label = SETTINGS[option_idx]["values"][value_idxs[option_idx]][0]
            key = SETTINGS[option_idx]["name"]
#            play_setting_wav(value_label + ".wav")  # Toca o som primeiro
            
           # Depois salva (não bloqueia o início do som)
            # Atualiza cor e brilho ao mudar cor ou brilho
            if SETTINGS[option_idx]["name"] == "COR":
                # Pula a cor vermelha (índice 0) ao navegar
                idx = value_idxs[option_idx]
                if idx == 0:
                    idx = 1
                    value_idxs[option_idx] = idx
                    value_label = SETTINGS[option_idx]["values"][value_idxs[option_idx]][0]
                
                cor = SETTINGS[option_idx]["values"][idx][1]
                pixels.fill(cor)
                set_rgb_led(cor)
                pixels.show()
            if SETTINGS[option_idx]["name"] == "Brilho":
                brilho = SETTINGS[option_idx]["values"][value_idxs[option_idx]][1]
                pixels.brightness = brilho
                pixels.show()
            
            user_settings[key] = value_idxs[option_idx]
            play_setting_wav(value_label + ".wav")  # Toca o som primeiro
            time.sleep(0.2)  # debounce

 
        if switch.short_count == 2:  # 2 short presses go to settings
            save_settings(user_settings)
            break



    # Salvar configurações ao sair do menu
