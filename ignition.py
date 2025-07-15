# ignition.py
import time
import math

def blend(color1, color2, t):
    """Mistura color1 e color2, t entre 0 (só color1) e 1 (só color2)."""
    return tuple(int(c1 * (1 - t) + c2 * t) for c1, c2 in zip(color1, color2))

def almost_white(color, percent_white=0.8):
    """Devolve a cor original puxada para branco (ex: 0.8 = 80% branco)."""
    return blend(color, (255, 255, 255), percent_white)

def scale_color(color, factor):
    return tuple(min(255, int(c * factor)) for c in color)

def ignition_explosion(pixels, saber_color, mixer=None, volume=1.0):
    import audiocore
    """
    pixels: objeto NeoPixel já inicializado
    saber_color: cor principal do sabre (tu podes usar COLORS[SABER_COLOR])
    """

    # Carrega o som curto grave
    if mixer:
        try:
            blip_wave = audiocore.WaveFile(open("/sounds/z_grave.wav", "rb"))
            blip_expl = audiocore.WaveFile(open("/sounds/0_on.wav", "rb"))
        except Exception as e:
            print("Erro ao carregar som z_grave.wav:", e)
            blip_wave = None
    else:
        blip_wave = None

    def play_blip():
        if mixer and blip_wave:
            try:
                #mixer.voice[1].stop()
                mixer.voice[1].play(blip_wave, loop=False)
                mixer.voice[1].level = volume
            except Exception as e:
                print("Erro ao tocar blip:", e)
    def play_expl():
        if mixer and blip_expl:
            try:
                #mixer.voice[0].stop()
                mixer.voice[1].play(blip_expl, loop=False)
                mixer.voice[1].level = volume
            except Exception as e:
                print("Erro ao tocar blip:", e)

    explosion_color = almost_white(saber_color, percent_white=0.8)

    NUM_PIXELS = len(pixels)
    CENTER_IDX = NUM_PIXELS // 2
    CENTER_BRIGHTNESS = 0.0

    DELAY_START = 0.02
    DELAY_END = 0.0001
    CENTER_BRIGHTNESS_STEP = 0.02
    THRESHOLD = 0.9
    MAX_ADVANCING = 6
    CYCLES_PER_INCREMENT = 3
    CENTER_MAX_WIDTH = 7

    pixels.fill((0, 0, 0))
    pixels.show()

    advancing_multiple = 1
    gradual_increase = False
    cycles_since_increment = 0

    side_brightness = 0.0
    SIDE_BRIGHTNESS_STEP = CENTER_BRIGHTNESS_STEP
    side_start = False

    while CENTER_BRIGHTNESS < THRESHOLD:
        progress = CENTER_BRIGHTNESS / THRESHOLD
        delay = DELAY_START * math.exp(-9 * progress) + DELAY_END * (1 - math.exp(-9 * progress))
        if delay <= DELAY_END + 0.0001:
            gradual_increase = True
        if not side_start and CENTER_BRIGHTNESS >= 0.4:
            side_start = True
            side_brightness = 0.0
        play_blip() 
        i = 0
        while i <= CENTER_IDX:
           
            if i - advancing_multiple >= 0:
                for j in range(i - advancing_multiple, i):
                    if 0 <= j < NUM_PIXELS:
                        pixels[j] = (0, 0, 0)
            for j in range(i, i + advancing_multiple):
                if 0 <= j < NUM_PIXELS:
                    pixels[j] = saber_color

            center_width = 1 + int((CENTER_BRIGHTNESS / THRESHOLD) * (CENTER_MAX_WIDTH - 1))
            half_width = center_width // 2

            for k in range(-half_width, half_width + 1):
                idx = CENTER_IDX + k
                if 0 <= idx < NUM_PIXELS:
                    if k == 0 or (center_width % 2 == 0 and k == -1):
                        if CENTER_BRIGHTNESS < 0.4:
                            factor = CENTER_BRIGHTNESS / 0.4
                            pixels[idx] = scale_color(saber_color, factor)
                        else:
                            blend_t = (CENTER_BRIGHTNESS - 0.4) / (THRESHOLD - 0.4)
                            blend_t = min(1.0, max(0.0, blend_t))
                            pixels[idx] = scale_color(blend(saber_color, explosion_color, blend_t), 0.4)
                    else:
                        if not side_start:
                            pixels[idx] = (0, 0, 0)
                        else:
                            if side_brightness < 0.4:
                                factor = side_brightness / 0.4
                                pixels[idx] = scale_color(saber_color, factor)
                            else:
                                factor = min(1.0, (side_brightness - 0.4) / (THRESHOLD - 0.4) * (1.0 - 0.4) + 0.4)
                                pixels[idx] = scale_color(saber_color, factor)
            
            pixels.show()
            if delay > 0:
                time.sleep(delay)
            i += advancing_multiple
        
        CENTER_BRIGHTNESS = min(THRESHOLD, CENTER_BRIGHTNESS + CENTER_BRIGHTNESS_STEP)
        if side_start:
            if side_brightness < THRESHOLD:
                side_brightness = min(THRESHOLD, side_brightness + SIDE_BRIGHTNESS_STEP)
        if gradual_increase and advancing_multiple < MAX_ADVANCING:
            cycles_since_increment += 1
            if cycles_since_increment >= CYCLES_PER_INCREMENT:
                advancing_multiple += 1
                cycles_since_increment = 0
    play_expl()
    for j in range(CENTER_IDX, NUM_PIXELS):
        if j < NUM_PIXELS:
            pixels[j] = explosion_color
            if j-1 >= 0:
                pixels[j-1] = saber_color
        mirror = CENTER_IDX - (j - CENTER_IDX)
        if 0 <= mirror < NUM_PIXELS:
            pixels[mirror] = explosion_color
            if mirror+1 < NUM_PIXELS:
                pixels[mirror+1] = saber_color
        pixels.show()
        time.sleep(0.005)

    pixels.fill(saber_color)
    pixels.show()

def ignition_scan(pixels, saber_color, mixer=None, volume=1.0, final=False):
    import time
    import audiocore
    if mixer:
        try:
            blip_wave = audiocore.WaveFile(open("/sounds/z_grave.wav", "rb"))
            blip_expl = audiocore.WaveFile(open("/sounds/0_on.wav", "rb"))
        except Exception as e:
            print("Erro ao carregar som z_grave.wav:", e)
            blip_wave = None
    else:
        blip_wave = None

    def play_blip():
        if mixer and blip_wave:
            try:
                #mixer.voice[1].stop()
                mixer.voice[1].play(blip_wave, loop=False)
                mixer.voice[1].level = volume
            except Exception as e:
                print("Erro ao tocar blip:", e)
    def play_expl():
        if mixer and blip_expl:
            try:
                #mixer.voice[0].stop()
                mixer.voice[1].play(blip_expl, loop=False)
                mixer.voice[1].level = volume
            except Exception as e:
                print("Erro ao tocar blip:", e)
    
    explosion_color = almost_white(saber_color, percent_white=0.5)
    NUM_PIXELS = len(pixels)
    if final is False:
        # Limpa todos os LEDs antes de iniciar o scan
        pixels.fill((0, 0, 0))
        pixels.show()
    play_expl()
    # "Fóton" vai do punho (0) até a ponta (NUM_PIXELS-1)
    for i in range(NUM_PIXELS):
        # Preenche atrás do fóton com a cor do sabre
        if i > 9:
            pixels[i - 10] = saber_color
        # Acende o fóton (branco) na posição atual
        pixels[i] = (explosion_color)
#        pixels.show()
#        play_blip()
        # Após o blip, pinta o fóton com a cor do sabre
        pixels.show()
        time.sleep(0.001)

    # Garante que todos os LEDs estejam acesos ao final
    pixels.fill(saber_color)
    pixels.show()

def ignition_reverse_scan_with_photons(pixels, saber_color, mixer=None, volume=1.0):
    import time
    import audiocore
    if mixer:
        try:
            blip_wave = audiocore.WaveFile(open("/sounds/z_grave.wav", "rb"))
            blip_expl = audiocore.WaveFile(open("/sounds/0_on.wav", "rb"))
        except Exception as e:
            print("Erro ao carregar som z_grave.wav:", e)
            blip_wave = None
    else:
        blip_wave = None

    def play_blip():
        if mixer and blip_wave:
            try:
                #mixer.voice[1].stop()
                mixer.voice[1].play(blip_wave, loop=False)
                mixer.voice[1].level = volume
            except Exception as e:
                print("Erro ao tocar blip:", e)
    def play_expl():
        if mixer and blip_expl:
            try:
                #mixer.voice[0].stop()
                mixer.voice[1].play(blip_expl, loop=False)
                mixer.voice[1].level = volume
            except Exception as e:
                print("Erro ao tocar blip:", e)
    explosion_color = almost_white(saber_color, percent_white=0.5)
    NUM_PIXELS = len(pixels)
    pixels.fill((0, 0, 0))
    pixels.show()

    scan_idx = NUM_PIXELS - 1  # scan começa na ponta

    DELAY = 0.00  # velocidade constante

    while scan_idx >= 0:
        play_blip()
        # Lança um fóton do punho
        photon = 0
        while photon < scan_idx:
            # Calcula o fator de brilho (1% a menos por pixel)
            
            
            # Desenha: limpa o anterior do fóton
            if 0 <= photon - 2 < NUM_PIXELS:
                pixels[photon - 2] = (0, 0, 0)
            # Desenha o fóton com brilho reduzido
            if 0 <= photon < NUM_PIXELS:
                pixels.brightness = 1.0 - (photon * 0.01)  # reduz brilho a cada pixel
                pixels[photon] = explosion_color
            #
            pixels.show()
            time.sleep(DELAY)
            photon += 2

        # Quando o fóton alcança o scan, recua o scan
        scan_idx -= 2
    ignition_scan(pixels, saber_color, mixer, volume, True)
  #  play_expl()
    # No final, acende tudo com a cor do sabre
    pixels.fill(saber_color)
    pixels.show()