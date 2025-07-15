import time

class BinAnimation:
    def __init__(self, filename, num_pixels, tint=(1,1,1), frame_delay=0.02, frame_skip=0, brightness=0.6):
        self.filename = filename
        self.num_pixels = num_pixels
        self.tint = tint
        self.frame_delay = frame_delay
        self.frame_skip = frame_skip
        self.frame_size = num_pixels * 3
        self.buf = bytearray(self.frame_size)
        self.file = open(filename, "rb")
        self.last_time = time.monotonic()
        self.done = False
        self.brightness = brightness  # brilho percentual (0.0 a 1.0)

    def reset(self):
        try:
            if self.file.closed:
                self.file = open(self.filename, "rb")
            else:
                self.file.seek(0)
        except Exception:
            self.file = open(self.filename, "rb")
        self.done = False
        self.last_time = 0
        # Limpa o buffer interno para garantir que não há resíduos
        for i in range(self.frame_size):
            self.buf[i] = 0

    def is_done(self):
        return self.done

    def next_frame_to_buffer(self, buffer):
        # buffer: lista de tuplas RGB, len = num_pixels
        if self.done:
            return False
        now = time.monotonic()
        if now - self.last_time < self.frame_delay:
            return True  # ainda não é hora do próximo frame
        self.last_time = now
        count = self.file.readinto(self.buf)
        if not count or count < self.frame_size:
            self.file.close()
            self.done = True
            return False
        for i in range(self.num_pixels):
            r = self.buf[i*3]
            g = self.buf[i*3+1]
            b = self.buf[i*3+2]
            # Tinting especial: só aplica tint se (R>0, G==0, B==0) ou (R==255, G==B)
            if (r > 0 and g == 0 and b == 0) or (r == 255 and g == b):
                tr = min(255, int(r * self.tint[0]))
                tg = min(255, int(r * self.tint[1])) if (g == 0 and b == 0) else min(255, int(g * self.tint[1]))
                tb = min(255, int(r * self.tint[2])) if (g == 0 and b == 0) else min(255, int(b * self.tint[2]))
                buffer[i] = (
                    int(tr * self.brightness),
                    int(tg * self.brightness),
                    int(tb * self.brightness)
                )
            elif r == g == b:
                buffer[i] = (int(r * self.brightness), int(g * self.brightness), int(b * self.brightness))
            else:
                buffer[i] = (int(r * self.brightness), int(g * self.brightness), int(b * self.brightness))
        for _ in range(self.frame_skip):
            skip = self.file.read(self.frame_size)
            if not skip or len(skip) < self.frame_size:
                self.file.close()
                self.done = True
                return False
        return True

class BinOverlay:
    """
    Overlay .bin em buffer RAM, blend de cinza, posição, transparência.
    """
    def __init__(self, filename, overlay_len, pos=0, tint=(1,1,1), transparent_color=(0,0,0), frame_delay=0.025):
        self.filename = filename
        self.overlay_len = overlay_len
        self.pos = pos
        self.tint = tint
        self.transparent_color = transparent_color
        self.frame_delay = frame_delay
        self.frame_size = overlay_len * 3
        self.buf = bytearray(self.frame_size)
        self.file = open(filename, "rb")
        self.last_time = 0
        self.done = False

    def reset(self):
        try:
            if self.file.closed:
                self.file = open(self.filename, "rb")
            else:
                self.file.seek(0)
        except Exception:
            self.file = open(self.filename, "rb")
        self.done = False
        self.last_time = 0
        # Limpa o buffer interno para garantir que não há resíduos
        for i in range(self.frame_size):
            self.buf[i] = 0

    def is_done(self):
        return self.done

    def next_frame_to_buffer(self, buffer):
        # buffer: lista de tuplas RGB, len = total de pixels
        if self.done:
            return False
        now = time.monotonic()
        if self.last_time == 0 or now - self.last_time >= self.frame_delay:
            self.last_time = now
            count = self.file.readinto(self.buf)
            if not count or count < self.frame_size:
                self.file.close()
                self.done = True
                return False
            # Aplica overlay em escala de cinza: branco = branco, preto = transparente, cinza = blend
            num_pixels = len(buffer)
            for i in range(self.overlay_len):
                pix_idx = self.pos + i
                if 0 <= pix_idx < num_pixels:
                    r = self.buf[i*3]
                    g = self.buf[i*3+1]
                    b = self.buf[i*3+2]
                    if r == 255 and g == 255 and b == 255:
                        buffer[pix_idx] = (255, 255, 255)
                    elif r == 0 and g == 0 and b == 0:
                        # transparente, não altera buffer
                        continue
                    elif r == g == b:
                        alpha = r / 255.0
                        bgc = buffer[pix_idx]
                        blended = (
                            int(bgc[0] * (1 - alpha) + 255 * alpha),
                            int(bgc[1] * (1 - alpha) + 255 * alpha),
                            int(bgc[2] * (1 - alpha) + 255 * alpha)
                        )
                        buffer[pix_idx] = blended
                    else:
                        buffer[pix_idx] = (r, g, b)
            return True
        return True  # aguarda próximo frame
