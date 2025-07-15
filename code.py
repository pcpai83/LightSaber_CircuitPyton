# SPDX-FileCopyrightText: 2023 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT
import microcontroller

microcontroller.cpu.frequency = 250_000_000  # run at 250 MHz instead of 125 MHz
import time
import os
import random
import board
import pwmio
import audiocore
import audiobusio
from adafruit_debouncer import Button
from digitalio import DigitalInOut, Direction, Pull
import neopixel
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.color import (
    RED,
    ORANGE,
    AMBER,
    AQUA,
    JADE,
    MAGENTA,
    PINK,
    TEAL,
    GOLD,
    BLACK,
    YELLOW,
    GREEN,
    CYAN,
    BLUE,
    PURPLE,
    WHITE,
)
import json
import adafruit_lis3dh
import analogio
from settings_menu import settings_menu
import simpleio
from adafruit_led_animation import helper
from adafruit_led_animation.helper import PixelSubset
from ignition import ignition_explosion,ignition_scan,ignition_reverse_scan_with_photons
import audiomixer
from adafruit_waveform import sine
import math
import array
from bin_animation import BinAnimation, BinOverlay
import supervisor

# Verifica status USB e ajusta comportamento
if supervisor.runtime.usb_connected:
    print("USB conectado - usando configurações de alto desempenho")
print(board.board_id)
print("CPU speed:", microcontroller.cpu.frequency)
for pin in dir(microcontroller.pin):
    if isinstance(getattr(microcontroller.pin, pin), microcontroller.Pin):
        print("".join(("microcontroller.pin.", pin, "\t")), end=" ")
        for alias in dir(board):
            if getattr(board, alias) is getattr(microcontroller.pin, pin):
                print("".join(("", "board.", alias)), end=" ")
    print()
# CUSTOMIZE SENSITIVITY HERE: smaller numbers = more sensitive to motion
HIT_THRESHOLD = 120
SWING_THRESHOLD = 130

COLORS = [
    RED,
    ORANGE,
    AMBER,
    AQUA,
    JADE,
    MAGENTA,
    TEAL,
    GOLD,
    YELLOW,
    GREEN,
    CYAN,
    BLUE,
    PURPLE,
    WHITE,
]

# Carregar configurações do usuário no início
default_settings = {
    "COR": 3,  # AQUA
    "Brilho": 2,  # Max
    "Volume": 2,  # Med
    "Swing": 1,  # Med
    "Clash": 1,  # Med
    "Anim": 0,  # On
}
try:
    with open("/settings.json", "r") as f:
        user_settings = json.load(f)
except Exception as e:
    print("Settings padrão carregado:", e)
    user_settings = default_settings
SABER_COLOR = user_settings.get("COR", default_settings["COR"])
BRILHO_IDX = user_settings.get("Brilho", default_settings["Brilho"])
VOLUME_IDX = user_settings.get("Volume", default_settings["Volume"])
SWING_IDX = user_settings.get("Swing", default_settings["Swing"])
CLASH_IDX = user_settings.get("Clash", default_settings["Clash"])
ANIM_IDX = user_settings.get("Anim", default_settings["Anim"])

# Definições dos valores possíveis (igual ao menu)
BRILHOS = [0.1, 0.4, 0.8]  # 0.1 = low, 0.4 = med, 0.8 = high
VOLUMES = [0.0, 0.1, 0.5, 1.0] # 0.0 = off, 0.1 = low, 0.5 = med, 1.0 = high
SWINGS = [260, 130, 65] # 260 = high, 130 = med, 65 = low
CLASHES = [127, 100, 60] # 127 = high, 100 = med, 60 = low
ANIMS = [True, False] # True = On, False = Off

# Aplicar configurações iniciais
pixels_brightness = BRILHOS[BRILHO_IDX]
pixels_brightness = max(0.01, min(0.8, pixels_brightness))  # segurança
volume = VOLUMES[VOLUME_IDX]
SWING_THRESHOLD = SWINGS[SWING_IDX]
HIT_THRESHOLD = CLASHES[CLASH_IDX]
use_anim = ANIMS[ANIM_IDX]

# enable external power pin
# provides power to the external components
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT
external_power.value = True

wavs = []
for filename in os.listdir("/sounds"):
    if filename.lower().endswith(".wav") and not filename.startswith("."):
        wavs.append("/sounds/" + filename)
wavs.sort()
print(wavs)
print(len(wavs))

audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
mixer = audiomixer.Mixer(
    voice_count=2,  # <-- agora com 2 vozes!
    sample_rate=22050,
    channel_count=1,
    bits_per_sample=16,
    samples_signed=True,
)


def play_wav(num, loop=False, channel=0):
    try:
        print(f"Tocando wav {num} no canal {channel}, loop={loop}")
        n = wavs[num]
        wave_file = open(n, "rb")
        wave = audiocore.WaveFile(wave_file)
        audio.play(mixer)
        mixer.voice[channel].play(wave, loop=loop)
        mixer.voice[channel].level = volume
    except Exception as e:
        print("Erro ao tocar wav:", e)
        return



# external button
pin = DigitalInOut(board.EXTERNAL_BUTTON)
pin.direction = Direction.INPUT
pin.pull = Pull.UP
pin2 = DigitalInOut(board.D13)
pin2.direction = Direction.INPUT
pin2.pull = Pull.UP
switch = Button(pin, long_duration_ms=1000)
switch_state = False

# external neopixels
num_pixels = 80
pixels = neopixel.NeoPixel(board.EXTERNAL_NEOPIXELS, num_pixels, auto_write=True)
pixels.brightness = 0.8

center_start = num_pixels // 2 - 5
center_end = num_pixels // 2 + 5
center_pixels = PixelSubset(pixels, center_start, center_end)
clash_pulse = Pulse(center_pixels, speed=0.01, color=WHITE, period=0.5)
clash_sparkle = Sparkle(center_pixels, speed=0.05, color=WHITE, num_sparkles=4)
rainbow = Rainbow(pixels, speed=0.05, period=2)
pulse = Pulse(pixels, speed=0.01, color=COLORS[SABER_COLOR], period=0.01)
chase = Chase(pixels, speed=0.01, color=COLORS[SABER_COLOR], size=3, spacing=1)

qw = 0  # contador para forçar atualização do display


use_sparkle = False  # Se True, usa Sparkle; senão, Pulse
def load_pack_data(pack_name):
    try:
        with open(f"/gfx/{pack_name}/pack.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar pack {pack_name}: {e}")
        # Fallback para packs clássicos: retorna estrutura vazia
        return {
            "leds": {},
            "preon": {},
            "poweron": {},
            "poweroff": {},
            "pstoff": {}
        }


# onboard LIS3DH
i2c = board.I2C()
int1 = DigitalInOut(board.ACCELEROMETER_INTERRUPT)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)
# Accelerometer Range (can be 2_G, 4_G, 8_G, 16_G)
lis3dh.range = adafruit_lis3dh.RANGE_4_G
lis3dh.set_tap(1, HIT_THRESHOLD)

red_led = pwmio.PWMOut(board.D10)
green_led = pwmio.PWMOut(board.D11)
blue_led = pwmio.PWMOut(board.D12)


def set_rgb_led(color):
    # convert from 0-255 (neopixel range) to 65535-0 (pwm range)
    red_led.duty_cycle = int(simpleio.map_range(color[0], 0, 255, 0, 65535))
    green_led.duty_cycle = int(simpleio.map_range(color[1], 0, 255, 0, 65535))
    blue_led.duty_cycle = int(simpleio.map_range(color[2], 0, 255, 0, 65535))



set_rgb_led(COLORS[SABER_COLOR])

mode = 4  # 0 = startup, 1 = default, 2 = clash, 3 = turn off, 4 = off, 5 = settings
# Variáveis de controle


swing = False
hit = False
force = True


# Função de interpolação linear para cores
# Recebe duas cores RGB e um valor t entre 0 e 1
# Retorna uma cor RGB interpolada
# Exemplo: lerp_color((255, 0, 0), (0, 0, 255), 0.5) retorna (127, 0, 127)
# onde (255, 0, 0) é vermelho e (0, 0, 255) é azul
# O valor t = 0.5 significa que a cor resultante é uma mistura igual das duas cores
# Se t = 0, retorna a primeira cor, se t = 1, retorna a segunda cor
# Se t < 0 ou t > 1, a função ainda funciona, mas extrapola as cores
# Exemplo:
# lerp_color((255, 0, 0), (0, 0, 255), -0.5) retorna (127, 0, 127)
# lerp_color((255, 0, 0), (0, 0, 255), 1.5) retorna (127, 0, 127)
# Isso pode ser útil para criar efeitos de transição suaves entre cores
def lerp_color(color1, color2, t):
    return (
        int(color1[0] + (color2[0] - color1[0]) * t),
        int(color1[1] + (color2[1] - color1[1]) * t),
        int(color1[2] + (color2[2] - color1[2]) * t),
    )

# Função auxiliar para posição aleatória do overlay
def overlay_random_pos(num_pixels, overlay_len):
    if num_pixels <= overlay_len:
        return 0
    return random.randint(0, num_pixels - overlay_len)

# Função auxiliar para posição centralizada do overlay
def overlay_center_pos(num_pixels, overlay_len):
    return max(0, (num_pixels - overlay_len) // 2)

# Define the path to the MFX (effects) binaries
MFX_PATH = "/mfx"  # Adjust this path as needed for your project


# Verifica se o arquivo de configurações existe, se não, cria com os valores padrão
print("Settings carregados:")
print("COR:", SABER_COLOR," - ",COLORS[SABER_COLOR])
print("Brilho:", BRILHO_IDX," - ",pixels.brightness)
print("Volume:", VOLUME_IDX," - ",volume)
print("Swing:", SWING_IDX," - ",SWING_THRESHOLD)
print("Clash:", CLASH_IDX," - ",HIT_THRESHOLD)
print("Anim:", ANIM_IDX," - ",use_anim)

# Configuração da leitura da bateria
vbat_voltage2 = analogio.AnalogIn(board.A0)
vbat_voltage = analogio.AnalogIn(board.A1)
def get_voltage(pin):
    return (pin.value / 65535 * 3.3 * 2) * 1.0291  # Ajuste para o divisor de tensão (2:1) e calibração (1.1x)

battery_voltage = get_voltage(vbat_voltage)
battery_voltage_old = battery_voltage  # Inicializa com o valor atual
battery_voltage2 = get_voltage(vbat_voltage2)
print("VBat voltage: {:.2f}".format(battery_voltage))
print("VBat voltage 2: {:.2f}".format(battery_voltage2))


# Packs disponíveis (subpastas em /gfx + clássicos)
gfx_effects = set(["explosion", "scan", "reverse_scan_with_photons"])
gfx_base_path = "/gfx"
for entry in os.listdir(gfx_base_path):
    full_path = gfx_base_path + "/" + entry
    if os.stat(full_path)[0] & 0x4000:
        gfx_effects.add(entry)
gfx_effects = sorted(gfx_effects)
print("Efeitos gfx encontrados:", gfx_effects)
for pack in gfx_effects:
    json_path = f"/gfx/{pack}/pack.json"
    def exists(path):
        try:
            os.stat(path)
            return True
        except OSError:
            return False
    print(f"[DEBUG] Pack: {pack}")
    if exists(json_path):
        print(f"  pack.json: OK")
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            print(f"  JSON válido!")
            for key, val in data.items():
                if isinstance(val, dict):
                    for subkey in ["bin", "wav"]:
                        if subkey in val:
                            fpath = f"/gfx/{pack}/{val[subkey]}"
                            print(f"    {key}.{subkey}: {'OK' if exists(fpath) else 'NÃO ENCONTRADO'}")
                # Se for lista de animações (não usado no seu caso atual)
                elif isinstance(val, list):
                    for idx, anim in enumerate(val):
                        for subkey in ["bin", "wav"]:
                            if subkey in anim:
                                fpath = f"/gfx/{pack}/{anim[subkey]}"
                                print(f"    {key}[{idx}].{subkey}: {'OK' if exists(fpath) else 'NÃO ENCONTRADO'}")
        except Exception as e:
            print(f"  Erro ao ler JSON: {e}")
    else:
        print(f"  pack.json: NÃO ENCONTRADO")
gfx_pack = "scan"  # ou outro pack padrão

# Exemplo: ignition_mode == 3 usa o efeito 'nuke'
# Você pode associar cada ignition_mode a um efeito, ou permitir seleção dinâmica
IGNITION_GFX_MAP = {
    3: "nuke",
    # Adicione outros modos/efeitos se quiser
}

def rgb_to_tint(color):
    return (color[0]/255, color[1]/255, color[2]/255)


ignition_mode = 0  # 0 = explosion, 1 = scan, 2 = reverse_scan_with_photons

LOW_BATTERY_LIMIT = 3.4  # ajuste conforme necessário


last_mode = None
current_animation = None
current_led_animations = []
led_anim_index = 0
pack_trocado = False
current_pack_data = None
current_leds = None
current_gfx_pack = None

def pack_json_exists(pack):
    try:
        os.stat(f"/gfx/{pack}/pack.json")
        return True
    except OSError:
        return False
usb = 0
usb_connected = False
# Inicialização dos buffers RAM
base_buffer = [(0, 0, 0)] * num_pixels
overlay_buffer = [(0, 0, 0)] * num_pixels

# Utilitário para compor overlay sobre base_buffer
def compose_buffers(base, overlay, out):
    for i in range(len(base)):
        # overlay preto = transparente
        if overlay[i] == (0, 0, 0):
            out[i] = base[i]
        else:
            out[i] = overlay[i]

while True:
#    battery_voltage2 = get_voltage(vbat_voltage2)
#    print("VBat voltage A0: {:.2f}".format(battery_voltage2))

#    battery_voltage = get_voltage(vbat_voltage)
#    print("VBat voltage A1: {:.2f}".format(battery_voltage))

#    battery_voltage2 = get_voltage(vbat_voltage2)
#    print("VBat voltage A0: {:.2f}".format(battery_voltage2))



#    qw += 1  # Força a atualização do display

#    battery_voltage = get_voltage(vbat_voltage)
#    if qw > 30: # Atualiza a cada 10 iterações
#        print("VBat voltage A1: {:.2f}".format(battery_voltage))
#        battery_voltage_old = battery_voltage  # Atualiza o valor antigo
#        qw = 0
    chase.color = COLORS[SABER_COLOR]
    switch.update()

    pixels.brightness = BRILHOS[BRILHO_IDX]

    
    x, y, z = lis3dh.acceleration
    # Atualiza histórico de X e Z
    accel_total = x * x + z * z
    
    # startup

    if mode == 0:
        mixer.voice[1].level = volume
        mixer.voice[0].level = volume
        print("Ignition pack:", gfx_pack)
        if use_anim:
            if gfx_pack == "explosion":
                ignition_explosion(pixels, COLORS[SABER_COLOR], mixer=mixer, volume=volume)
                # Aguarda o som de ignição terminar antes de prosseguir
                while mixer.voice[1].playing:
                    pass
            elif gfx_pack == "scan":
                ignition_scan(pixels, COLORS[SABER_COLOR], mixer=mixer, volume=volume)
                # Aguarda o som de ignição terminar antes de prosseguir
                while mixer.voice[1].playing:
                    pass
            elif gfx_pack == "reverse_scan_with_photons":
                ignition_reverse_scan_with_photons(pixels, COLORS[SABER_COLOR], mixer=mixer, volume=volume)
                # Aguarda o som de ignição terminar antes de prosseguir
                while mixer.voice[1].playing:
                    pass
            else:
                pack_data = load_pack_data(gfx_pack)
                preon = pack_data.get("preon")
                poweron = pack_data.get("poweron")
                if preon:
                    frame_time = preon.get("frame_time", 25) / 1000
                    wav_file = preon.get("wav", "")
                    tinting = preon.get("tinting", True)
                    if wav_file:
                        mixer.voice[1].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{wav_file}", "rb")), loop=False)
                    current_animation = BinAnimation(
                        f"/gfx/{gfx_pack}/{preon['bin']}",
                        num_pixels,
                        rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                        frame_time,
                        0
                    )
                    while not current_animation.is_done():
                        current_animation.next_frame_to_buffer(base_buffer)
                        # Opcional: envie para os LEDs se quiser mostrar durante poweron
                        pixels[:] = base_buffer
                        pixels.show()
                        switch.update()
                if poweron:
                    frame_time = poweron.get("frame_time", 25) / 1000
                    wav_file = poweron.get("wav", "")
                    tinting = poweron.get("tinting", True)
                    if wav_file:
                        mixer.voice[1].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{wav_file}", "rb")), loop=False)
                    else:
                        play_wav(0, loop=False, channel=1)

                    current_animation = BinAnimation(
                        f"/gfx/{gfx_pack}/{poweron['bin']}",
                        num_pixels,
                        rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                        frame_time,
                        0
                    )
                    while not current_animation.is_done():
                        # Substitua next_frame() por next_frame_to_buffer(base_buffer)
                        current_animation.next_frame_to_buffer(base_buffer)
                        # Opcional: envie para os LEDs se quiser mostrar durante poweron
                        pixels[:] = base_buffer
                        pixels.show()
                        switch.update()
                    mixer.stop_voice(1)
                elif preon and not poweron:
                    ignition_scan(pixels, COLORS[SABER_COLOR], mixer=mixer, volume=volume)
                elif not preon and poweron:
                    pass
                else:
                    ignition_scan(pixels, COLORS[SABER_COLOR], mixer=mixer, volume=volume)
        else:
            play_wav(0, loop=False, channel=1)
            for i in range(pixels):
                pixels[i] = COLORS[SABER_COLOR]
                pixels.show()
        # Aguarda o som de ignição terminar antes de tocar o idle
        while mixer.voice[1].playing:
            pass
        # Antes de mudar para modo 1, toca o idle correto
        pack_data = load_pack_data(gfx_pack)
        leds = pack_data.get("leds")
        mixer.voice[0].stop()
        if use_anim and leds and leds.get("wav"):
            mixer.voice[0].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{leds['wav']}", "rb")), loop=True)
        else:
            play_wav(1, loop=True, channel=0)
        mode = 1
    elif mode == 1:
        # Garante que a animação idle nunca para
        if use_anim and current_led_animations:
            current_animation = current_led_animations[0]["anim"]
        if last_mode != 1 or gfx_pack != current_gfx_pack:
            if pack_json_exists(gfx_pack):
                try:
                    current_pack_data = load_pack_data(gfx_pack)
                except Exception:
                    current_pack_data = None
                current_leds = current_pack_data.get("leds") if current_pack_data else None
            else:
                current_pack_data = None
                current_leds = None
            current_gfx_pack = gfx_pack
            # Só para idle anterior se necessário
        else:
            pack_data = load_pack_data(gfx_pack)
            leds = pack_data.get("leds")
        # Garante que a animação de LEDs é carregada sempre que necessário
        if not mixer.voice[0].playing and not mixer.voice[1].playing:
            #mixer.voice[0].stop()
            if use_anim and current_leds and current_leds.get("wav"):
                mixer.voice[0].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{current_leds['wav']}", "rb")), loop=True)
            else:
                mixer.voice[0].play(audiocore.WaveFile(open(f"/sounds/1_idle.wav", "rb")), loop=True)
        if use_anim:
            if leds and (not current_led_animations or last_mode != 1 or pack_trocado):
                # Limpa buffers/caches ao trocar de pack de animação
                current_led_animations = []
                led_anim_index = 0
                # Limpa o buffer base para evitar frames residuais
                for i in range(num_pixels):
                    base_buffer[i] = (0, 0, 0)
                # Só limpa os LEDs se já havia animação anterior
                if len(current_led_animations) > 0:
                    pixels.fill((0, 0, 0))
                frame_time = leds.get("frame_time", 25) / 1000
                bin_file = leds.get("bin")
                wav_file = leds.get("wav", "")
                # --- TINTING LOGIC ---
                tinting = leds.get("tinting", True)
                if bin_file:
                    current_led_animations.append({
                        "anim": BinAnimation(
                            f"/gfx/{gfx_pack}/{bin_file}",
                            num_pixels,
                            rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                            frame_time,
                            0
                        ),
                        "wav": wav_file,
                        "wav_played": False
                    })
            elif not leds and current_led_animations:
                #mixer.voice[1].stop()
                current_led_animations = []
                led_anim_index = 0
        # Só toca idle se não estiver tocando
        if last_mode != 1:
            led_anim_index = 0
            if use_anim and leds:
                frame_time = leds.get("frame_time", 25) / 1000
                bin_file = leds.get("bin")
                wav_file = leds.get("wav", "")
                tinting = leds.get("tinting", True)
                if bin_file:
                    current_led_animations.append({
                        "anim": BinAnimation(
                            f"/gfx/{gfx_pack}/{bin_file}",
                            num_pixels,
                            rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                            frame_time,
                            0
                        ),
                        "wav": wav_file,
                        "wav_played": False
                    })
                    # Garante limpeza do buffer interno da animação
                    current_led_animations[-1]["anim"].reset()
        if use_anim:
            # Executa animação de LEDs se houver, senão faz chase e idle padrão
            if current_led_animations:
                led_anim = current_led_animations[0]
                if led_anim["wav"] and not led_anim["wav_played"]:
                    mixer.voice[0].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{led_anim['wav']}", "rb")), loop=True)
                    led_anim["wav_played"] = True
                # Substitua next_frame() por next_frame_to_buffer(base_buffer)
                if not led_anim["anim"].next_frame_to_buffer(base_buffer) or current_animation is None:
                    frame_time = leds.get("frame_time", 25) / 1000
                    bin_file = leds.get("bin")
                    tinting = leds.get("tinting", True)
                    led_anim["anim"] = BinAnimation(
                        f"/gfx/{gfx_pack}/{bin_file}",
                        num_pixels,
                        rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                        frame_time,
                        0
                    )
                
                # Substitua next_frame() por next_frame_to_buffer(base_buffer)
                if current_animation is None:
                    current_animation = led_anim["anim"]
                current_animation.next_frame_to_buffer(base_buffer)
                # Opcional: envie para os LEDs se quiser mostrar durante poweron
                pixels[:] = base_buffer
                pixels.show()
            else:
                #mixer.voice[1].stop()  # Para qualquer som de animação anterior
                chase.animate()
        else:
            pixels.fill(COLORS[SABER_COLOR])
            pixels.show()
        x, y, z = lis3dh.acceleration
        accel_total = x * x + z * z

        if lis3dh.tapped:
            print("tapped")
            mode = "hit"
        elif accel_total >= SWING_THRESHOLD:
            print("swing")
            mode = "swing"
        if switch.short_count == 1:
            mode = "blast"
        if switch.short_count == 2:
            print("off!")
            mode = 3
            
        if switch.short_count == 3:
            mode = "blade_bleeding"

    # clash or move
    elif mode == "hit":
        # Defina o nome do arquivo binário do efeito clash
        CLASH_BIN = "hit.bin"
        # Defina o comprimento do overlay clash (ajuste conforme necessário)
        CLASH_LEN = 80

        # Clash overlay centralizado
        overlay = BinOverlay(
            f"{MFX_PATH}/{CLASH_BIN}",   # filename como primeiro argumento posicional
            CLASH_LEN,
            overlay_center_pos(num_pixels, CLASH_LEN),
            (1,1,1),
            (0,0,0),
            0.025
        )
        play_wav(random.randint(7, 14), loop=False, channel=1)
        # Verifica se há animação de LEDs base ativa (idle customizada)
        if use_anim and current_led_animations and current_led_animations[0]["anim"]:
            base_anim = current_led_animations[0]["anim"]
        else:
            base_anim = None
        while not overlay.is_done():
            if base_anim:
                current_animation.next_frame_to_buffer(base_buffer)
            elif use_anim:
                chase.animate()
            else:
                pixels.fill(COLORS[SABER_COLOR])
            for i in range(num_pixels):
                overlay_buffer[i] = (0, 0, 0)
            overlay.next_frame_to_buffer(overlay_buffer)
            composed = None
            composed = [(0, 0, 0)] * num_pixels  # Define composed buffer
            compose_buffers(base_buffer, overlay_buffer, composed)
            pixels[:] = composed
            pixels.show()
            switch.update()
        # Retoma idle ou entra em lockup se botão ainda pressionado
        if switch.value:  # não pressionado
            pack_data = load_pack_data(gfx_pack)
            leds = pack_data.get("leds")
            if use_anim and leds and leds.get("wav"):
                mixer.voice[0].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{leds['wav']}", "rb")), loop=True)
            else:
                play_wav(1, loop=True, channel=0)
            mode = 1
        else:  # botão ainda pressionado
            mode = "lockup"
    elif mode == "blast":
        # Defina o nome do arquivo binário do efeito blast
        BLAST_BIN = "blast.bin"
        # Defina o comprimento do overlay blast (ajuste conforme necessário)
        BLAST_LEN = 42

        # Blast overlay em posição aleatória
        pos = overlay_random_pos(num_pixels, BLAST_LEN)
        for i in range(num_pixels):
            overlay_buffer[i] = (0, 0, 0)
        overlay = BinOverlay(
            f"{MFX_PATH}/{BLAST_BIN}",
            BLAST_LEN,
            pos,
            (1,1,1),
            (0,0,0),
            0.01
        )
        mixer.voice[1].play(audiocore.WaveFile(open(f"/sounds/blst0{random.randint(1, 4)}.wav", "rb")), loop=False)



        # Verifica se há animação de LEDs base ativa (idle customizada)
        if use_anim and current_led_animations and current_led_animations[0]["anim"]:
            base_anim = current_led_animations[0]["anim"]
        else:
            base_anim = None
        while not overlay.is_done():
            if base_anim:                
                current_animation.next_frame_to_buffer(base_buffer)
            elif use_anim:
                chase.animate()
            else:
                pixels.fill(COLORS[SABER_COLOR])
            for i in range(num_pixels):
                overlay_buffer[i] = (0, 0, 0)
            overlay.next_frame_to_buffer(overlay_buffer)
            composed = None
            composed = [(0, 0, 0)] * num_pixels  # Define composed buffer
            compose_buffers(base_buffer, overlay_buffer, composed)
            pixels[:] = composed
            pixels.show()
            switch.update()

        mode = 1                
    elif mode == "swing":
#        mixer.voice[1].stop()
        if not mixer.voice[1].playing:
            play_wav(random.randint(16, 23), loop=False, channel=1)

        mode = 1
            # Garante que a animação idle volta após swing


    elif mode == "lockup":
        # Defina o nome do arquivo binário do efeito lockup
        LOCKUP_BIN = "lockup20x60.bin"
        # Defina o comprimento do overlay lockup (ajuste conforme necessário)
        LOCKUP_LEN = 20
        overlay.reset()
        overlay = BinOverlay(
            f"{MFX_PATH}/{LOCKUP_BIN}",
            LOCKUP_LEN,
            0,  # posição inicial, será ajustada dinamicamente
            (1,1,1),
            (0,0,0),
            0.025
        )
        play_wav(15, loop=True, channel=1)
        if use_anim and current_led_animations and current_led_animations[0]["anim"]:
            base_anim = current_led_animations[0]["anim"]
        else:
            base_anim = None

        Y_MIN = -9.8  # ponta para cima
        Y_MAX = 9.8   # ponta para baixo

        while not switch.value:
            # Atualiza animação base corretamente (idle customizada ou chase/cor fixa)
            while not overlay.is_done():
                switch.update()

                # Lê inclinação Y
                _, y, _ = lis3dh.acceleration
                # INVERTE O CÁLCULO: t=0 na base (punho), t=1 na ponta
                t = (Y_MAX - y) / (Y_MAX - Y_MIN)
                t = min(1.0, max(0.0, t))
                pos = int((num_pixels - LOCKUP_LEN) * t)
                overlay.pos = pos


                if switch.value == True:
                    break
                if base_anim:
                    if current_animation.is_done():
                        current_animation.reset()

                    current_animation.next_frame_to_buffer(base_buffer)

                    BRILHO_ANIM = 0.5    # BinAnimation (idle, base) - 60%
                    BRILHO_OVERLAY = 1.0 # BinOverlay (clash, overlay) - 100%

                    # 1) Aplica brilho só no base_buffer
                    for i in range(num_pixels):
                        r, g, b = base_buffer[i]
                        base_buffer[i] = (int(r * BRILHO_ANIM), int(g * BRILHO_ANIM), int(b * BRILHO_ANIM))

                elif use_anim:
                    chase.animate()
                else:
                    pixels.fill(COLORS[SABER_COLOR])
                for i in range(num_pixels):
                    overlay_buffer[i] = (0, 0, 0)
                overlay.next_frame_to_buffer(overlay_buffer)
                composed = None
                composed = [(0, 0, 0)] * num_pixels  # Define composed buffer
                compose_buffers(base_buffer, overlay_buffer, composed)
                pixels[:] = composed
                pixels.show()

            if overlay.is_done():
                try:
                    overlay.reset()
                except Exception:
                    overlay = BinOverlay(
                        f"{MFX_PATH}/{LOCKUP_BIN}",
                        pixels,
                        LOCKUP_LEN,
                        pos,
                        (1,1,1),
                        (0,0,0),
                        0.025
                    )
#            overlay.next_frame(bg=bg)
            switch.update()
        mixer.voice[1].stop()
        mode = 1


    ############### blade_bleeding ################
    # Modo blade_bleeding
    # A lâmina fica vermelha e o brilho varia conforme a aceleração no eixo Z



    elif mode == "blade_bleeding":  # blade_bleeding
        tinting = leds.get("tinting", True) 

        if tinting:
            print("tinting modo blade_bleeding")
            if use_anim and current_led_animations and current_led_animations[0]["anim"]:
                base_anim = current_led_animations[0]["anim"]
            else:
                base_anim = None

            # Lê o valor inicial de z como referência
            _, _, z0 = lis3dh.acceleration
            while True:
                x, y, z = lis3dh.acceleration
                # Calcula a diferença relativa ao início
                dz = z - z0
                # Imprime os valores de aceleração
#                print("Aceleração - Z: {:.2f}, Diferença Z: {:.2f}".format(z, dz))
                # Se a aceleração for negativa, z0 é maior que z, então inverte o sinal
                # Normaliza para o range 0..1 (ajuste o divisor conforme sensibilidade desejada)
                z_norm = min(1.0, max(0.0, abs(dz) / 7))  # Ajuste o divisor conforme necessário
                #print("z_norm:", z_norm)
                #sparkle = Sparkle(pixels, speed=(15/dz)/100, color=WHITE, num_sparkles= dz - 8)
                color = lerp_color(COLORS[SABER_COLOR], RED, z_norm)
                #sparkle.animate()
                if base_anim:

                    # Aplica tinting dinâmico antes de enviar ao buffer
                    current_animation.tint = rgb_to_tint(color)
                    if current_animation.is_done():
                        current_animation.reset()
                    current_animation.next_frame_to_buffer(base_buffer)
                    pixels[:] = base_buffer
                    pixels.show()
                    
                elif use_anim:
                    chase.color = color
                    chase.animate()
                else:
                    pixels.fill(COLORS[SABER_COLOR])
                pixels.show()

                switch.update()
                if switch.short_count == 1:
                    print("Saindo do modo blade_bleeding")
                    if color == RED:
                        COLORS[SABER_COLOR] = RED  # Se estiver vermelho, apaga a lâmina
                        # Retorna à cor original
                        pixels.fill(COLORS[SABER_COLOR])
                        pixels.show()
                    mode = 1
                    break
        else:
            print("Modo blade_bleeding não suporta tinting")
            mode = 1
    # turn on break
        mode = 1
    # turn off
    elif mode == 3:  # turn off
        mixer.voice[0].stop()
        if use_anim:
            if gfx_pack == "reverse_scan_with_photons":
                play_wav(2, loop=False, channel=1)
#                current_animation = BinAnimation(f"/gfx/{gfx_pack}/poweroff3.bin", pixels, num_pixels, rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1), 20/1000, 0)

                tinting = True
                frame_time = 20 / 1000
                current_animation = BinAnimation(
                    f"/gfx/{gfx_pack}/poweroff3.bin",
                    num_pixels,
                    rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                    frame_time,
                    0
                )
                while not current_animation.is_done():
                    current_animation.next_frame_to_buffer(base_buffer)
                    pixels[:] = base_buffer
                    pixels.show()
                    switch.update()
                time.sleep(0.1)
            elif gfx_pack in ["explosion", "scan"]:
                play_wav(2, loop=False, channel=1)
                pixels.fill(COLORS[SABER_COLOR])
                for i in range(num_pixels - 1, 0, -1):
                    pixels[i] = BLACK
                    pixels.show()
                    time.sleep(0.01)
                time.sleep(0.1)
            else:
                pack_data = load_pack_data(gfx_pack)
                poweroff = pack_data.get("poweroff")
                pstoff = pack_data.get("pstoff")
                
                if poweroff:
                    tinting = poweroff.get("tinting", True)
                    frame_time = poweroff.get("frame_time", 25) / 1000
                    wav_file = poweroff.get("wav", "")
                    if wav_file:
                        mixer.voice[1].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{wav_file}", "rb")), loop=False)
                    else:
                        play_wav(2, loop=False, channel=1)
                    current_animation = BinAnimation(
                        f"/gfx/{gfx_pack}/{poweroff['bin']}",
                        num_pixels,
                        rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                        frame_time,
                        0
                    )
                    while not current_animation.is_done():                        
                        # Substitua next_frame() por next_frame_to_buffer(base_buffer)
                        current_animation.next_frame_to_buffer(base_buffer)
                        # Opcional: envie para os LEDs se quiser mostrar durante poweron
                        pixels[:] = base_buffer
                        pixels.show()
                        switch.update()
                    mixer.stop_voice(1)
                else:
                    play_wav(2, loop=False, channel=1)
                    #pixels.fill(COLORS[SABER_COLOR])
                    for i in range(num_pixels - 1, 0, -1):
                        pixels[i] = BLACK
                        pixels.show()
                        time.sleep(0.01)
                    time.sleep(0.1)
                if pstoff:
                    frame_time = pstoff.get("frame_time", 25) / 1000
                    wav_file = pstoff.get("wav", "")
                    tinting = pstoff.get("tinting", True)
                    if wav_file:
                        mixer.voice[1].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/{wav_file}", "rb")), loop=False)
                    current_animation = BinAnimation(
                        f"/gfx/{gfx_pack}/{pstoff['bin']}",
                        num_pixels,
                        rgb_to_tint(COLORS[int(SABER_COLOR)]) if tinting else (1, 1, 1),
                        frame_time,
                        0
                    )
                    while not current_animation.is_done():
                        
                        current_animation.next_frame_to_buffer(base_buffer)
                        # Opcional: envie para os LEDs se quiser mostrar durante poweron
                        pixels[:] = base_buffer
                        pixels.show()
                        switch.update()
                    mixer.stop_voice(1)
        else:
            play_wav(2, loop=False, channel=1)
            #pixels.fill(COLORS[SABER_COLOR])
            for i in range(num_pixels - 1, 0, -1):
                pixels[i] = BLACK
                pixels.show()
                time.sleep(0.01)
            time.sleep(0.1)
        mode = 4
        last_mode = None  # Garante que idle será reiniciado ao ligar novamente
    # go to startup from off
    elif mode == 4:
        mixer.voice[0].stop()  # Só para idle

        if force:
            volume = 1
            play_wav(24, loop=False)
            force = False
        while mixer.voice[0].playing:
            pass
        else:
            external_power.value = False
            volume = VOLUMES[VOLUME_IDX]
        if switch.short_count == 1:
            battery_voltage = get_voltage(vbat_voltage)
            print("VBat voltage: {:.2f}".format(battery_voltage))
            if battery_voltage < LOW_BATTERY_LIMIT:
                play_wav(25, loop=False)  # wav z_fraca
                # Pisca a lâmina em vermelho enquanto a bateria estiver fraca
                for _ in range(10):
                    pixels.fill((255, 0, 0))
                    pixels.show()
                    time.sleep(0.1)
                    pixels.fill((0, 0, 0))
                    pixels.show()
                    time.sleep(0.1)
                while mixer.voice[0].playing:
                    delay = 0.1
                external_power.value = False  # desliga a lâmina#
            else:
                print("Ligando a lâmina")
                external_power.value = True
                mode = 0  # Volta para o modo de ignição
                last_mode = None  # Garante que idle será reiniciado ao ligar novamente
        
        if switch.short_count == 3:
            mixer.voice[0].stop()
            print("settings")
            mode = 5
        # Troca animação de ignição/retração com long press
        if switch.long_press:
            # Troca o gfx_pack ciclicamente
            current_idx = gfx_effects.index(gfx_pack)
            gfx_pack = gfx_effects[(current_idx + 1) % len(gfx_effects)]
            print("Ignition pack:", gfx_pack)
            # Feedback visual: pisca a lâmina na cor da animação escolhida
            mixer.voice[1].play(audiocore.WaveFile(open(f"/gfx/{gfx_pack}/font.wav", "rb")), loop=False)
            preview_colors = [WHITE, (0, 255, 255), (255, 255, 0), (255, 0, 255)]
            external_power.value = True
            for _ in range(3):
                pixels.fill(preview_colors[current_idx % len(preview_colors)])
                pixels.show()
                time.sleep(0.2)
                pixels.fill((0, 0, 0))
                pixels.show()
                time.sleep(0.2)
            external_power.value = False
            # Limpa imediatamente todos os buffers e LEDs para evitar frames residuais
            for i in range(num_pixels):
                base_buffer[i] = (0, 0, 0)
                overlay_buffer[i] = (0, 0, 0)
            # Limpa também as animações de LED para evitar frames residuais
            current_led_animations = []
            led_anim_index = 0
            # Garante que não há animação corrente
            current_animation = None

        if switch.short_count == 2: # 2 short presses show baterry level
            external_power.value = True

            # Lê a voltagem da bateria
            battery_voltage2 = get_voltage(vbat_voltage2)
            print("VBat voltage A0: {:.2f}".format(battery_voltage2))

            battery_voltage = get_voltage(vbat_voltage)
            print("VBat voltage A1: {:.2f}".format(battery_voltage))

            battery_voltage2 = get_voltage(vbat_voltage2)
            print("VBat voltage A0: {:.2f}".format(battery_voltage2))

            # Define faixa típica de 18650
            min_v = 3.4
            max_v = 4
            pct = min(1.0, max(0.0, (battery_voltage - min_v) / (max_v - min_v)))

            # Calcula quantos LEDs acender
            num_lit = int(pct * num_pixels)

            # Calcula cor do gradiente (vermelho -> amarelo -> verde)
            def lerp(a, b, t):
                return int(a + (b - a) * t)
            prev_brightness = pixels.brightness  # Save current brightness
            pixels.brightness = 0.1  # Define brilho para visualização
            for i in range(num_pixels):
                t = i / (num_pixels - 1)
                if t < 0.10:
                    # 0-10%: vermelho puro
                    r, g, b = 255, 0, 0
                elif t < 0.25:
                    # 10-25%: vermelho -> amarelo
                    local_t = (t - 0.10) / 0.15
                    r = 255
                    g = lerp(0, 255, local_t)
                    b = 0
                elif t < 0.5:
                    # 25-50%: amarelo -> verde
                    local_t = (t - 0.25) / 0.25
                    r = lerp(255, 0, local_t)
                    g = 255
                    b = 0
                elif t < 0.9:
                    # 50-90%: verde puro
                    r, g, b = 0, 255, 0
                else:
                    # 90-100%: verde -> azul
                    local_t = (t - 0.9) / 0.1
                    r = 0
                    g = lerp(255, 0, local_t)
                    b = lerp(0, 255, local_t)
                color = (r, g, b)
                if i < num_lit:
                    pixels[i] = color
                else:
                    pixels[i] = (0, 0, 0)
            pixels.show()
            # Mostra por 5 segundos
            t0 = time.monotonic()
            while time.monotonic() - t0 < 5:
                pass

            # Apaga a lâmina ao terminar
            pixels.fill((0, 0, 0))
            pixels.show()
            pixels.brightness = prev_brightness  # Restore previous brightness
            # Volta para modo off
            mode = 4

    # settings menu
    elif mode == 5:
        external_power.value = True
        print("Entrando no menu de configurações")
        settings_menu(
            mixer,
            pixels,
            set_rgb_led,
            COLORS,
            switch,
            pin2,
            user_settings,
            VOLUMES,
            PixelSubset,
            WHITE,
        )
        try:
            with open("/settings.json", "r") as f:
                user_settings = json.load(f)
        except Exception as e:
            print("Settings padrão carregado:", e)
            user_settings = default_settings
        SABER_COLOR = user_settings.get("COR", default_settings["COR"])
        BRILHO_IDX = user_settings.get("Brilho", default_settings["Brilho"])
        VOLUME_IDX = user_settings.get("Volume", default_settings["Volume"])
        SWING_IDX = user_settings.get("Swing", default_settings["Swing"])
        CLASH_IDX = user_settings.get("Clash", default_settings["Clash"])
        ANIM_IDX = user_settings.get("Anim", default_settings["Anim"])
        force = True
        mode = 3


    last_mode = mode

    last_mode = mode

