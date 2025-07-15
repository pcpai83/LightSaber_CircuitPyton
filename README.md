# 🔦 Sabre de Luz em CircuitPython / CircuitPython Lightsaber

[![Adafruit CircuitPython](https://img.shields.io/badge/Adafruit-CircuitPython-blue)](https://circuitpython.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Projeto por **pcpai83**

---

## 🇵🇹 Português

### Sobre

Este projeto é um **sabre de luz interativo** feito com CircuitPython 9.2.8, baseado na placa [Adafruit RP2040 Prop-Maker Feather com I2S Audio Amplifier](https://www.adafruit.com/product/4880).  
Permite brincar com luzes, sons e movimentos tal como nos filmes — tudo com um só botão, modos especiais, menu de configurações e animações incríveis!

### Funcionalidades

- **Lâmina Neopixel** (80 LEDs ou mais) com cores, brilho e efeitos personalizáveis
- **Efeitos de som realistas** (clash, swing, lockup, blast, ignição, etc.)
- **Sensor de movimento** (acelerômetro LIS3DH)
- **Botão lateral** para controlar todos os modos e menus
- **Interruptor físico ON/OFF** (energia) e carregamento USB-C
- **Menu de definições** com feedback sonoro e visual (cor, brilho, volume, animação…)
- **Modos especiais:** lockup, blade bleeding, medidor de bateria com LEDs, troca de efeito de ignição

### Como funciona

- **Só um botão para tudo:** pressões simples, múltiplas e longas, diferentes comandos consoante o estado (ligado, desligado ou menu)
- **Arquitetura modular:** fácil de alterar, adicionar sons/efeitos e modificar menus
- **Carregamento fácil:** basta abrir o “pommel” (tampa traseira) e ligar USB-C

### Requisitos

- Adafruit RP2040 Prop-Maker Feather (ou similar)
- Lâmina LED WS2812 (Neopixel)
- Alto-falante (Speaker)
- Bateria Li-Ion 18650
- Sensor LIS3DH (acelerômetro I2C)
- Botão push e interruptor ON/OFF
- CircuitPython 9.2.8 +
- Bibliotecas Adafruit CircuitPython (ver `requirements.txt`)

### Organização

```
/code.py             # Código principal do sabre
/settings_menu.py    # Lógica do menu de definições
/sounds/             # Efeitos de som (WAV)
/gfx/                # Animações gráficas (BIN, WAV)
/settings.json       # Configuração guardada do utilizador
```

### Créditos

Projeto de hardware, firmware e 3D por **pcpai83**  
Inspirado em projetos DIY de lightsaber e na comunidade Adafruit.

---

## 🇬🇧 English

### About

This project is an **interactive lightsaber** using CircuitPython 9.2.8 and the [Adafruit RP2040 Prop-Maker Feather with I2S Audio Amplifier](https://www.adafruit.com/product/4880).  
Enjoy movie-like light, sound and motion — all with a single button, special modes, onboard settings menu and cool FX animations!

### Features

- **Neopixel LED blade** (80+ LEDs), customizable color, brightness and effects
- **Realistic sound FX** (clash, swing, lockup, blast, ignition, etc.)
- **Motion sensing** (LIS3DH accelerometer)
- **Side push button** for all modes and menu navigation
- **Physical ON/OFF switch** (power) and USB-C charging
- **Settings menu** with audio/visual feedback (color, brightness, volume, animation…)
- **Special modes:** lockup, blade bleeding, LED battery meter, ignition FX cycling

### How it works

- **Single-button operation:** short, multiple and long presses trigger different actions, depending on the saber state (on/off/menu)
- **Modular software:** easy to add new sounds, FX and menu options
- **Easy charging:** just unscrew the pommel and connect USB-C

### Requirements

- Adafruit RP2040 Prop-Maker Feather (or compatible)
- WS2812 Neopixel LED blade
- Speaker
- 18650 Li-Ion battery
- LIS3DH accelerometer (I2C)
- Push button & ON/OFF switch
- CircuitPython 9.2.8 +
- Adafruit CircuitPython libraries (see `requirements.txt`)

### Structure

```
/code.py             # Main saber firmware
/settings_menu.py    # Onboard settings menu logic
/sounds/             # Sound effects (WAV)
/gfx/                # Graphical FX (BIN, WAV)
/settings.json       # User configuration file
```

### Credits

Hardware, firmware & 3D design by **pcpai83**  
Inspired by DIY lightsaber projects and the Adafruit community.

---

## 📸 Demonstração

*(Adiciona aqui GIFs, fotos ou vídeos do sabre em ação!)*

---

## 📦 Instalação rápida

1. Instalar CircuitPython 9.2.8 na Feather RP2040 Prop-Maker
2. Copiar todos os ficheiros para a placa (`code.py`, `settings_menu.py`, pastas `sounds/`, `gfx/`, etc.)
3. Colocar as bibliotecas necessárias em `lib/`
4. (Opcional) Personalizar sons e efeitos!

---

## 📝 Licença

MIT License
