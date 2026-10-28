"""
Olho ASCII que segue o mouse  |  ESPAÇO: olho <-> coração  |  ESC: sair

Dependências:
    pip install -r requirements.txt   (na raiz do projeto)

Ideia geral (3 passos):
  1. A tela é uma grade de "células" (COLS x ROWS). Cada célula recebe UM caractere.
  2. Para cada célula calculamos uma luminosidade (0..1) e uma cor com fórmulas
     matemáticas (olho, coração, estrelas). A luminosidade escolhe o caractere
     (" .:-=+*#%@") e a cor pinta esse caractere.
  3. Tudo é feito com arrays do numpy (sem laços célula por célula), então roda a 60 FPS.
"""
import math
import sys

import numpy as np
import pygame

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------
COLS, ROWS = 130, 58          # tamanho da grade de caracteres
FONT_SIZE = 14
RAMP = " .:-=+*#%@"           # do mais "vazio" ao mais "cheio"
FPS = 60
TEMPO_TRANSICAO = 1.8         # segundos para olho <-> coração

# ----------------------------------------------------------------------------
# JANELA E FONTE
# ----------------------------------------------------------------------------
pygame.init()
_caminho = pygame.font.match_font("menlo,dejavusansmono,consolas,couriernew,liberationmono")
font = pygame.font.Font(_caminho, FONT_SIZE) if _caminho else pygame.font.Font(None, FONT_SIZE + 4)
CW, CH = font.size("M")       # largura e altura de uma célula, em pixels
W, H = COLS * CW, ROWS * CH
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Eye - Space")


def construir_atlas():
    """Desenha cada caractere da RAMP uma vez e guarda como matriz (n, CW, CH)."""
    atlas = np.zeros((len(RAMP), CW, CH), np.float32)
    for i, ch in enumerate(RAMP):
        if ch == " ":
            continue
        surf = font.render(ch, True, (255, 255, 255))
        # a forma do caractere fica no canal ALFA (o RGB é branco em todos os pixels)
        a = pygame.surfarray.array_alpha(surf).astype(np.float32) / 255
        atlas[i, :min(CW, a.shape[0]), :min(CH, a.shape[1])] = a[:CW, :CH]
    return atlas


ATLAS = construir_atlas()

# ----------------------------------------------------------------------------
# COORDENADAS DE CADA CÉLULA  (X: -1..1 na largura, Y: para cima, mesma escala)
# ----------------------------------------------------------------------------
_px = (np.arange(COLS) + 0.5) * CW
_py = (np.arange(ROWS) + 0.5) * CH
X, Y = np.meshgrid(_px, _py)
X = ((X - W / 2) / (W / 2)).astype(np.float32)
Y = (-(Y - H / 2) / (W / 2)).astype(np.float32)

rng = np.random.default_rng(7)
RUIDO = rng.random((ROWS, COLS)).astype(np.float32)   # usado na dissolução


# ----------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ----------------------------------------------------------------------------
def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(c1, c2, t):
    """Mistura duas cores RGB; t é uma matriz (ROWS, COLS) entre 0 e 1."""
    c1 = np.asarray(c1, np.float32)
    c2 = np.asarray(c2, np.float32)
    return c1 * (1 - t[..., None]) + c2 * t[..., None]


def cor_const(rgb):
    return np.broadcast_to(np.asarray(rgb, np.float32), (ROWS, COLS, 3))


# ----------------------------------------------------------------------------
# CAMADA 1: O OLHO
# ----------------------------------------------------------------------------
def camada_olho(t, gx, gy, abertura):
    """
    gx, gy   : direção do olhar (-1..1)
    abertura : 1 = olho aberto, 0 = fechado (piscada)
    Retorna (luminosidade, cor) de cada célula.
    """
    EW = 0.80                                   # meia-largura do olho
    u = X / EW
    forma = np.clip(1 - u ** 2, 0, None) ** 0.85   # curva de amêndoa
    alt = 0.58 * max(abertura, 0.04)
    topo = alt * forma * (1 + 0.25 * gy)           # pálpebra superior
    base = -alt * 0.70 * forma * (1 - 0.25 * gy)   # pálpebra inferior
    dentro = (Y < topo) & (Y > base) & (np.abs(u) < 1)

    # --- pele ao redor -----------------------------------------------------
    vinheta = np.clip(1.15 - (X ** 2 + (Y / 0.75) ** 2) * 0.9, 0.15, 1)
    pele_L = (0.20 + 0.04 * np.sin(X * 40) * np.sin(Y * 55)) * vinheta
    forma_ext = np.clip(1 - (u / 1.25) ** 2, 0, None)
    y_dobra = 0.11 + alt * forma_ext * (1 + 0.25 * gy)
    dobra = np.exp(-((Y - y_dobra) / 0.016) ** 2) * np.sqrt(forma_ext)
    pele_L = pele_L + 0.45 * dobra * vinheta
    pele_C = cor_const([235, 140, 115])

    # --- esclera (branco do olho) -----------------------------------------
    sombra_topo = np.clip((topo - Y) / 0.12, 0, 1)       # sombra da pálpebra
    esc_L = 0.95 * (0.45 + 0.55 * sombra_topo ** 0.7) * (1 - 0.35 * u ** 2)
    cantos = np.clip((np.abs(u) - 0.78) * 4.5, 0, 1)      # cantos avermelhados
    esc_C = mix([235, 232, 228], [225, 95, 85], cantos)

    # --- íris e pupila -----------------------------------------------------
    icx, icy = gx * 0.25, gy * 0.15                      # centro da íris
    dx, dy = X - icx, Y - icy
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    Ri = 0.34
    Rp = 0.13 + 0.014 * math.sin(t * 1.7)                # pupila "respira"
    rn = r / Ri
    fibras = 0.5 + 0.5 * np.sin(ang * 34 + 3.0 * np.sin(ang * 5 + rn * 6))
    ir_C = mix([245, 165, 55], [110, 45, 18], np.clip(rn, 0, 1) ** 0.8)
    ir_L = (0.55 + 0.45 * fibras) * (0.85 + 0.35 * np.exp(-((rn - 0.45) / 0.08) ** 2))
    ir_L = ir_L * (1 - 0.75 * smoothstep(0.82, 1.0, rn))   # anel escuro na borda
    ir_L = ir_L * (0.55 + 0.45 * sombra_topo ** 0.7)
    ir_L = np.clip(ir_L * 0.85, 0, 1)
    ir_L = np.where(r < Rp, 0.0, ir_L)                    # pupila = vazio

    no_iris = rn < 1.0
    L = np.where(no_iris, ir_L, esc_L)
    C = np.where(no_iris[..., None], ir_C, esc_C)

    # --- reflexo de luz ----------------------------------------------------
    brilho = np.exp(-(((X - (icx - 0.10)) ** 2 + (Y - (icy + 0.10)) ** 2) / 0.0020))
    L = np.maximum(L, brilho)
    C = np.where((brilho > 0.35)[..., None], cor_const([255, 255, 255]), C)

    # --- linha dos cílios --------------------------------------------------
    borda = (np.abs(Y - topo) < 0.02) | (np.abs(Y - base) < 0.012)
    L = np.where(borda, L * 0.35, L)

    return np.where(dentro, L, pele_L), np.where(dentro[..., None], C, pele_C)


# ----------------------------------------------------------------------------
# CAMADA 2: O CORAÇÃO (equação implícita) que bate
# ----------------------------------------------------------------------------
def camada_coracao(t):
    b = (t * 1.3) % 1.0
    pulso = 1 + 0.07 * math.exp(-8 * b) + 0.04 * math.exp(-8 * ((b - 0.25) % 1.0))
    s = 0.55 * pulso
    hx = X / s
    hy = Y / s + 0.12
    f = (hx ** 2 + hy ** 2 - 1) ** 3 - hx ** 2 * hy ** 3     # f < 0 => dentro
    dentro = f < 0
    prof = np.clip(-f, 0, 1) ** 0.45
    L = 0.30 + 0.70 * prof
    L = L + 0.35 * np.exp(-(((hx + 0.45) ** 2 + (hy - 0.55) ** 2) / 0.05))
    L = np.where(dentro, np.clip(L, 0, 1), 0.0)
    C = mix([255, 70, 140], [255, 190, 215], np.clip((prof - 0.4) / 0.6, 0, 1))
    return L, C


# ----------------------------------------------------------------------------
# CAMADA 3: ESTRELAS que piscam
# ----------------------------------------------------------------------------
NE = 110
_st_r = rng.integers(0, ROWS, NE)
_st_c = rng.integers(0, COLS, NE)
_st_fase = rng.uniform(0, 6.28, NE)
_st_vel = rng.uniform(1.0, 3.5, NE)
_st_grande = rng.random(NE) > 0.75
_st_rosa = rng.random(NE) < 0.5
ROSA, AZUL = (255, 150, 200), (200, 220, 255)


def camada_estrelas(t):
    L = np.zeros((ROWS, COLS), np.float32)
    C = np.full((ROWS, COLS, 3), 255, np.float32)
    for i in range(NE):
        b = 0.5 + 0.5 * math.sin(t * _st_vel[i] + _st_fase[i])
        cor = ROSA if _st_rosa[i] else AZUL
        pontos = [(0, 0, 1.0)]
        if _st_grande[i] and b > 0.3:       # brilho em cruz
            pontos += [(0, 1, .55), (0, -1, .55), (1, 0, .55), (-1, 0, .55), (0, 2, .3), (0, -2, .3)]
        for dr, dc, k in pontos:
            rr, cc = _st_r[i] + dr, _st_c[i] + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS and b * k > L[rr, cc]:
                L[rr, cc] = b * k
                C[rr, cc] = cor
    return L, C


# ----------------------------------------------------------------------------
# COMPOSIÇÃO + DESENHO NA TELA
# ----------------------------------------------------------------------------
def compor(t, gx, gy, abertura, s):
    """s = 0 (só olho) ... 1 (só coração). Mistura as 3 camadas."""
    Le, Ce = camada_olho(t, gx, gy, abertura)
    Lh, Ch = camada_coracao(t)
    Ls, Cs = camada_estrelas(t)

    # o olho se desfaz célula por célula (ordem aleatória)
    limite = s * 1.15 - 0.05
    Le = Le * np.clip((RUIDO - limite) * 6, 0, 1)
    # o coração "se forma" célula por célula
    h = np.clip((s - 0.35) / 0.65, 0, 1)
    Lh = Lh * np.clip((h * 1.3 - RUIDO) * 5, 0, 1)
    # estrelas: aparecem na transição e ficam por perto do coração
    Ls = Ls * (smoothstep(0, 0.35, s) * (0.55 + 0.45 * math.sin(math.pi * s)))

    Ls_all = np.stack([Le, Lh, Ls])
    Cs_all = np.stack([Ce, Ch, Cs])
    venc = Ls_all.argmax(0)                                   # camada mais clara vence
    L = np.take_along_axis(Ls_all, venc[None], 0)[0]
    C = np.take_along_axis(Cs_all, venc[None, ..., None], 0)[0]
    return L, C


def desenhar(L, C):
    """Converte (luminosidade, cor) por célula em pixels, tudo vetorizado."""
    idx = (np.clip(L, 0, 1) ** 0.85 * (len(RAMP) - 1) + 0.5).astype(int)
    mask = ATLAS[idx]                                          # (ROWS, COLS, CW, CH)
    mask = mask.transpose(1, 2, 0, 3).reshape(COLS * CW, ROWS * CH)
    # só o "tom" da cor; o brilho vem da densidade do caractere
    tom = C / (C.max(axis=2, keepdims=True) + 1e-6) * 255
    tom = np.repeat(np.repeat(tom.transpose(1, 0, 2), CW, 0), CH, 1)
    img = (mask[..., None] * tom).astype(np.uint8)
    pygame.surfarray.blit_array(screen, img)


# ----------------------------------------------------------------------------
# LOOP PRINCIPAL
# ----------------------------------------------------------------------------
def main():
    clock = pygame.time.Clock()
    t = 0.0
    gx = gy = 0.0                 # olhar suavizado
    modo_coracao = False
    s_lin = 0.0                   # progresso linear da transição (0..1)
    prox_piscada, ini_piscada = 2.5, -1.0

    while True:
        dt = clock.tick(FPS) / 1000
        t += dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                modo_coracao = not modo_coracao

        # --- olhar: segue o mouse (ou passeia sozinho se o mouse sair) -----
        if pygame.mouse.get_focused():
            mx, my = pygame.mouse.get_pos()
            alvo_x = np.clip((mx - W / 2) / (W / 2) * 1.6, -1, 1)
            alvo_y = np.clip(-(my - H / 2) / (H / 2) * 1.6, -1, 1)
        else:
            alvo_x, alvo_y = 0.6 * math.sin(t * 0.7), 0.4 * math.sin(t * 1.1)
        k = 1 - math.exp(-dt * 12)
        gx += (alvo_x - gx) * k
        gy += (alvo_y - gy) * k

        # --- piscada aleatória --------------------------------------------
        if t > prox_piscada and ini_piscada < 0:
            ini_piscada = t
        abertura = 1.0
        if ini_piscada >= 0:
            p = (t - ini_piscada) / 0.22
            if p >= 1:
                ini_piscada, prox_piscada = -1.0, t + 2 + 3 * abs(math.sin(t * 7.3))
            else:
                abertura = 1 - math.sin(math.pi * p)

        # --- transição suave olho <-> coração ------------------------------
        passo = dt / TEMPO_TRANSICAO
        s_lin = min(1.0, s_lin + passo) if modo_coracao else max(0.0, s_lin - passo)
        s = s_lin * s_lin * (3 - 2 * s_lin)

        L, C = compor(t, gx, gy, abertura, s)
        desenhar(L, C)
        pygame.display.flip()


if __name__ == "__main__":
    main()
