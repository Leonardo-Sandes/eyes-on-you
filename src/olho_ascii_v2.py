"""
OLHO ASCII v2  -  interativo

  ESPAÇO / ← →   trocar de modo (olho, coração, galáxia, código, texto)
  1 a 5          ir direto para um modo
  C              trocar o tema de cores
  D              um olho <-> dois olhos
  T              digitar um texto (Enter confirma, Esc cancela)
  P              liga/desliga o rastro do mouse
  S              salvar uma foto (PNG)
  H              mostrar/esconder a ajuda
  Mouse          o olhar te segue; se ficar parado, o olho dorme
  Clique         fogos + susto + onda de choque     |  segurar: chafariz de faíscas
  Botão direito (ou segurar F)   focar (pupila dilata e o olho estreita)
  ESC            sair

Dependências:   pip install -r requirements.txt   (na raiz do projeto)

Ideia geral (a mesma da v1):
  1. A tela é uma grade de células; cada célula recebe UM caractere.
  2. Cada "camada" (olho, coração, galáxia...) devolve, para cada célula,
     luminosidade (0..1), cor e, às vezes, um glifo específico.
  3. A luminosidade escolhe o caractere (" .:-=+*#%@"); a cor pinta o caractere.
  4. Na troca de modo, uma matriz de ruído decide a ordem em que as células
     do modo antigo somem e as do novo aparecem.
"""
import math
import sys

import numpy as np
import pygame

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------
FONT_SIZE = 14
RAMP = " .:-=+*#%@"                                  # densidade: vazio -> cheio
GLIFOS = "01{}[]<>/\\|=+*#$&%;:ABCDEFabcdef23456789"  # usados na chuva de código
FPS = 60
TEMPO_TRANSICAO = 1.6                                # segundos entre modos

# ----------------------------------------------------------------------------
# JANELA E FONTE  (o tamanho da grade se adapta ao tamanho da sua tela)
# ----------------------------------------------------------------------------
pygame.init()
_caminho = pygame.font.match_font("menlo,dejavusansmono,consolas,couriernew,liberationmono")
font = pygame.font.Font(_caminho, FONT_SIZE) if _caminho else pygame.font.Font(None, FONT_SIZE + 4)
CW, CH = font.size("M")                              # tamanho de uma célula (px)

try:
    _tw, _th = pygame.display.get_desktop_sizes()[0]
except Exception:
    _tw, _th = 1440, 900
_Hpx = min(58 * CH, int(_th * 0.80))
_Wpx = min(int(_Hpx * 1.06), int(_tw * 0.92), 130 * CW)
COLS, ROWS = max(60, _Wpx // CW), max(30, _Hpx // CH)
W, H = COLS * CW, ROWS * CH
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Eye - Space")


def construir_atlas():
    """Desenha cada caractere (RAMP + GLIFOS) uma única vez: matriz (n, CW, CH)."""
    todos = RAMP + GLIFOS
    atlas = np.zeros((len(todos), CW, CH), np.float32)
    for i, ch in enumerate(todos):
        if ch == " ":
            continue
        surf = font.render(ch, True, (255, 255, 255))
        a = pygame.surfarray.array_alpha(surf).astype(np.float32) / 255   # forma = canal alfa
        atlas[i, :min(CW, a.shape[0]), :min(CH, a.shape[1])] = a[:CW, :CH]
    return atlas


ATLAS = construir_atlas()
NG = len(GLIFOS)

# ----------------------------------------------------------------------------
# COORDENADAS DE CADA CÉLULA  (X: -1..1 na largura; Y: para cima, mesma escala)
# ----------------------------------------------------------------------------
_px = (np.arange(COLS) + 0.5) * CW
_py = (np.arange(ROWS) + 0.5) * CH
X, Y = np.meshgrid(_px, _py)
X = ((X - W / 2) / (W / 2)).astype(np.float32)
Y = (-(Y - H / 2) / (W / 2)).astype(np.float32)
COL_IDX, LIN_IDX = np.meshgrid(np.arange(COLS), np.arange(ROWS))

rng = np.random.default_rng(7)
RUIDO = rng.random((ROWS, COLS)).astype(np.float32)        # ordem da dissolução
SEM_GLIFO = np.full((ROWS, COLS), -1, np.int32)

# ----------------------------------------------------------------------------
# TEMAS DE COR
# ----------------------------------------------------------------------------
TEMAS = [
    dict(nome="Âmbar",     iris_a=(245, 165, 55),  iris_b=(110, 45, 18), pele=(235, 140, 115),
         cantos=(225, 95, 85),   ac1=(255, 70, 140), ac2=(255, 190, 215), codigo=(60, 255, 120)),
    dict(nome="Oceano",    iris_a=(110, 225, 255), iris_b=(10, 60, 140), pele=(120, 150, 215),
         cantos=(90, 120, 210),  ac1=(50, 130, 255), ac2=(170, 225, 255), codigo=(80, 220, 255)),
    dict(nome="Esmeralda", iris_a=(150, 255, 120), iris_b=(10, 90, 40),  pele=(130, 200, 140),
         cantos=(110, 190, 120), ac1=(40, 220, 120), ac2=(190, 255, 210), codigo=(60, 255, 100)),
    dict(nome="Rubi",      iris_a=(255, 90, 70),   iris_b=(100, 5, 15),  pele=(200, 85, 75),
         cantos=(230, 60, 60),   ac1=(255, 50, 60),  ac2=(255, 170, 120), codigo=(255, 90, 60)),
    dict(nome="Neon",      iris_a=(255, 80, 230),  iris_b=(60, 20, 170), pele=(150, 95, 225),
         cantos=(200, 80, 230),  ac1=(255, 60, 200), ac2=(110, 240, 255), codigo=(255, 80, 220)),
]
BRANCO = (255, 255, 255)
AZUL_ESTRELA = (200, 220, 255)


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


def renderizar_texto(txt):
    """Desenha o texto numa tela grande e reduz para 1 pixel = 1 célula."""
    if not txt:
        return np.zeros((ROWS, COLS), np.float32)
    tela = pygame.Surface((W, H))
    tela.fill((0, 0, 0))
    tam = int(H * 0.55)
    while True:
        f = pygame.font.SysFont(["helveticaneue", "arial", "dejavusans"], tam, bold=True)
        sup = f.render(txt, True, (255, 255, 255))
        if sup.get_width() <= W * 0.9 or tam <= 12:
            break
        tam = int(tam * 0.9)
    tela.blit(sup, ((W - sup.get_width()) // 2, (H - sup.get_height()) // 2))
    pequena = pygame.transform.smoothscale(tela, (COLS, ROWS))
    arr = pygame.surfarray.array3d(pequena)[:, :, 0].astype(np.float32) / 255
    return np.clip(arr.T * 1.4, 0, 1) ** 0.7


# ----------------------------------------------------------------------------
# PARTÍCULAS (fogos, faíscas, rastro do mouse) - tudo em arrays do numpy
# ----------------------------------------------------------------------------
class Particulas:
    def __init__(self, n=900):
        self.n, self.i = n, 0
        self.pos = np.zeros((n, 2), np.float32)       # (coluna, linha), em células
        self.vel = np.zeros((n, 2), np.float32)       # células por segundo
        self.vida = np.zeros(n, np.float32)
        self.vida0 = np.ones(n, np.float32)
        self.cor = np.full((n, 3), 255, np.float32)
        self.grav = np.zeros(n, np.float32)
        self.r = np.random.default_rng()

    def emitir(self, col, lin, qtd, vmin, vmax, vida, cores, grav_px=0.0, ang=(0, 2 * math.pi)):
        """Velocidades em pixels/s (convertidas para células, que não são quadradas)."""
        idx = (self.i + np.arange(qtd)) % self.n
        self.i = (self.i + qtd) % self.n
        a = self.r.uniform(ang[0], ang[1], qtd)
        sp = self.r.uniform(vmin, vmax, qtd)
        self.pos[idx] = (col, lin)
        self.vel[idx, 0] = np.cos(a) * sp / CW
        self.vel[idx, 1] = -np.sin(a) * sp / CH       # linha cresce para baixo
        self.vida[idx] = self.vida0[idx] = self.r.uniform(vida * 0.6, vida, qtd)
        self.cor[idx] = np.asarray(cores, np.float32)[self.r.integers(0, len(cores), qtd)]
        self.grav[idx] = grav_px / CH

    def atualizar(self, dt):
        self.pos += self.vel * dt
        self.vel[:, 1] += self.grav * dt
        self.vel *= math.exp(-1.2 * dt)               # atrito do ar
        self.vida -= dt

    def desenhar(self, L, C):
        cc = np.floor(self.pos[:, 0]).astype(int)
        rr = np.floor(self.pos[:, 1]).astype(int)
        ok = (self.vida > 0) & (cc >= 0) & (cc < COLS) & (rr >= 0) & (rr < ROWS)
        b = np.clip(self.vida[ok] / self.vida0[ok], 0, 1) ** 0.7
        np.maximum.at(L, (rr[ok], cc[ok]), b)
        C[rr[ok], cc[ok]] = self.cor[ok]


# ----------------------------------------------------------------------------
# ESTADO DO PROGRAMA (tudo o que muda ao longo do tempo fica aqui)
# ----------------------------------------------------------------------------
class Estado:
    def __init__(self):
        self.t = 0.0
        self.modo_atual, self.modo_alvo = "olho", None
        self.s_lin, self.s = 0.0, 0.0                 # progresso da transição
        self.tema = 0
        self.dois_olhos = False
        self.olhar = [[0.0, 0.0], [0.0, 0.0]]         # olhar suavizado de cada olho
        self.mouse = np.zeros(2)                      # mouse em coordenadas do mundo
        self.px_ant = None
        self.vel_mouse = 0.0
        self.parado_ha = 0.0
        self.sono = 0.0                               # 0 acordado ... 1 dormindo
        self.surpresa = 0.0
        self.foco = 0.0
        self.abertura = 1.0
        self.fator_pupila = 1.0
        self.prox_piscada, self.ini_piscada = 2.5, -1.0
        self.fase_cora = 0.0
        self.fase_gal = 0.0
        self.particulas = Particulas()
        self.ondas = []                               # (x, y, instante)
        self.rastro = True
        self.texto = "LEO"
        self.buffer = ""
        self.digitando = False
        self.texto_L = renderizar_texto(self.texto)
        self.ajuda = None                             # None = automática (some após 12 s)
        self.foto_pendente = False
        self.n_fotos = 0

    # ---- atalhos ------------------------------------------------------------
    @property
    def cores(self):
        return TEMAS[self.tema]

    def posicoes_olhos(self):
        """(deslocamento x, escala) de cada olho."""
        return [(-0.50, 0.55), (0.50, 0.55)] if self.dois_olhos else [(0.0, 1.0)]

    def ir_para(self, modo):
        if self.modo_alvo is None and modo != self.modo_atual:
            self.modo_alvo, self.s_lin = modo, 0.0

    def proximo_modo(self, passo):
        i = MODOS.index(self.modo_atual)
        self.ir_para(MODOS[(i + passo) % len(MODOS)])

    # ---- entrada --------------------------------------------------------------
    def clique(self, pos):
        c = self.cores
        self.particulas.emitir(pos[0] / CW, pos[1] / CH, 80, 150, 560, 1.3,
                               [c["ac1"], c["ac2"], BRANCO], grav_px=260)
        wx, wy = (pos[0] - W / 2) / (W / 2), -(pos[1] - H / 2) / (W / 2)
        self.ondas.append((wx, wy, self.t))
        self.surpresa = 1.0

    def tecla(self, ev):
        """Devolve True se for para sair."""
        if self.digitando:
            if ev.key == pygame.K_RETURN:
                if self.buffer.strip():
                    self.texto = self.buffer
                self.digitando = False
                self.texto_L = renderizar_texto(self.texto)
            elif ev.key == pygame.K_ESCAPE:
                self.digitando = False
                self.texto_L = renderizar_texto(self.texto)
            else:
                if ev.key == pygame.K_BACKSPACE:
                    self.buffer = self.buffer[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(self.buffer) < 14:
                    self.buffer += ev.unicode
                self.texto_L = renderizar_texto(self.buffer + "_")
            return False

        k = ev.key
        if k == pygame.K_ESCAPE:
            return True
        elif k in (pygame.K_SPACE, pygame.K_RIGHT):
            self.proximo_modo(1)
        elif k == pygame.K_LEFT:
            self.proximo_modo(-1)
        elif pygame.K_1 <= k <= pygame.K_5:
            self.ir_para(MODOS[k - pygame.K_1])
        elif k == pygame.K_c:
            self.tema = (self.tema + 1) % len(TEMAS)
        elif k == pygame.K_d:
            self.dois_olhos = not self.dois_olhos
        elif k == pygame.K_p:
            self.rastro = not self.rastro
        elif k == pygame.K_s:
            self.foto_pendente = True
        elif k == pygame.K_h:
            self.ajuda = not (self.ajuda if self.ajuda is not None else self.t < 12)
        elif k == pygame.K_t and self.modo_alvo is None:
            self.digitando, self.buffer = True, ""
            self.texto_L = renderizar_texto("_")
            self.ir_para("texto")
        return False

    # ---- atualização por quadro ---------------------------------------------
    def atualizar(self, dt, mouse_px, dentro, botoes, tecla_f):
        self.t += dt
        mx, my = mouse_px
        c = self.cores

        # mouse -> coordenadas do mundo (suavizado). Fora da janela, passeia sozinho.
        if dentro:
            alvo = np.array([(mx - W / 2) / (W / 2), -(my - H / 2) / (W / 2)])
        else:
            alvo = np.array([0.6 * math.sin(self.t * 0.7), 0.3 * math.sin(self.t * 1.1)])
        antes = self.mouse.copy()
        self.mouse += (alvo - self.mouse) * (1 - math.exp(-dt * 12))
        v = math.hypot(*(self.mouse - antes)) / max(dt, 1e-3)
        self.vel_mouse += (v - self.vel_mouse) * (1 - math.exp(-dt * 6))

        # mexeu o mouse? (em pixels)
        mexeu = self.px_ant is not None and math.hypot(mx - self.px_ant[0], my - self.px_ant[1]) > 1.5
        self.px_ant = (mx, my)
        if dentro and not mexeu:
            self.parado_ha += dt
        else:
            if mexeu and self.sono > 0.5:
                self.surpresa = 1.0                    # acordou assustado!
            self.parado_ha = 0.0

        # estados emocionais suavizados
        self.sono += ((np.clip((self.parado_ha - 6) / 4, 0, 1)) - self.sono) * (1 - math.exp(-dt * 1.5))
        self.surpresa = max(0.0, self.surpresa - dt * 2.5)
        foco_alvo = 1.0 if (botoes[2] or tecla_f) else 0.0
        self.foco += (foco_alvo - self.foco) * (1 - math.exp(-dt * 8))

        # piscada aleatória
        piscada = 1.0
        if self.t > self.prox_piscada and self.ini_piscada < 0:
            self.ini_piscada = self.t
        if self.ini_piscada >= 0:
            p = (self.t - self.ini_piscada) / 0.22
            if p >= 1:
                self.ini_piscada = -1.0
                self.prox_piscada = self.t + 2 + 3 * abs(math.sin(self.t * 7.3))
            else:
                piscada = 1 - math.sin(math.pi * p)
        self.abertura = (piscada * (1 + 0.22 * self.surpresa + min(self.vel_mouse * 0.12, 0.18))
                         * (1 - 0.45 * self.foco) * (1 - 0.85 * self.sono))
        self.fator_pupila = (1 - 0.35 * self.surpresa) * (1 + 0.30 * self.foco)

        # olhar de cada olho
        k = 1 - math.exp(-dt * 12)
        for i, (ox, _) in enumerate(self.posicoes_olhos()):
            ax = float(np.clip((self.mouse[0] - ox) / 0.6, -1, 1))
            ay = float(np.clip(self.mouse[1] / 0.5, -1, 1)) - 0.6 * self.sono
            self.olhar[i][0] += (ax - self.olhar[i][0]) * k
            self.olhar[i][1] += (ay - self.olhar[i][1]) * k

        # fases que acumulam (assim a velocidade pode mudar sem "pulos")
        self.fase_cora += dt * (1.3 + 2.0 * self.surpresa)
        self.fase_gal += dt * (0.35 + 1.5 * self.surpresa + 0.4 * self.vel_mouse)

        # partículas: rastro, chafariz e atualização
        col, lin = mx / CW, my / CH
        if dentro and self.rastro and mexeu:
            self.particulas.emitir(col, lin, 2, 10, 90, 0.8, [c["ac1"], c["ac2"]], grav_px=-30)
        if dentro and botoes[0]:
            self.particulas.emitir(col, lin, 3, 200, 420, 1.0, [c["ac2"], BRANCO, c["ac1"]],
                                   grav_px=500, ang=(math.pi * 0.39, math.pi * 0.61))
        self.particulas.atualizar(dt)
        self.ondas = [w for w in self.ondas if self.t - w[2] < 2.5]

        # transição entre modos
        if self.modo_alvo is not None:
            self.s_lin = min(1.0, self.s_lin + dt / TEMPO_TRANSICAO)
            if self.s_lin >= 1.0:
                self.modo_atual, self.modo_alvo, self.s_lin = self.modo_alvo, None, 0.0
        self.s = self.s_lin * self.s_lin * (3 - 2 * self.s_lin)


# ----------------------------------------------------------------------------
# CAMADA: O OLHO  (cada olho é calculado em coordenadas "locais")
# ----------------------------------------------------------------------------
def um_olho(e, ox, esc, gx, gy):
    c = e.cores
    Xl, Yl = (X - ox) / esc, Y / esc                  # coordenadas do próprio olho
    EW = 0.80
    u = Xl / EW
    forma = np.clip(1 - u ** 2, 0, None) ** 0.85       # curva de amêndoa
    alt = 0.58 * max(e.abertura, 0.04)
    topo = alt * forma * (1 + 0.25 * gy)
    base = -alt * 0.70 * forma * (1 - 0.25 * gy)
    dentro = (Yl < topo) & (Yl > base) & (np.abs(u) < 1)

    # pele ao redor
    vinheta = np.clip(1.15 - (X ** 2 + (Y / 0.75) ** 2) * 0.9, 0.15, 1)
    pele_L = (0.20 + 0.04 * np.sin(X * 40) * np.sin(Y * 55)) * vinheta
    forma_ext = np.clip(1 - (u / 1.25) ** 2, 0, None)
    y_dobra = 0.11 + alt * forma_ext * (1 + 0.25 * gy)
    dobra = np.exp(-((Yl - y_dobra) / 0.016) ** 2) * np.sqrt(forma_ext)
    pele_L = pele_L + 0.45 * dobra * vinheta
    pele_C = cor_const(c["pele"])

    # esclera
    sombra = np.clip((topo - Yl) / 0.12, 0, 1)
    esc_L = 0.95 * (0.45 + 0.55 * sombra ** 0.7) * (1 - 0.35 * u ** 2)
    esc_C = mix([235, 232, 228], c["cantos"], np.clip((np.abs(u) - 0.78) * 4.5, 0, 1))

    # íris e pupila (a pupila dilata quando o mouse chega perto)
    icx, icy = gx * 0.25, gy * 0.15
    dx, dy = Xl - icx, Yl - icy
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    Ri = 0.34
    prox = math.exp(-(math.hypot(e.mouse[0] - ox, e.mouse[1]) ** 2) / 0.4)
    Rp = (0.13 + 0.014 * math.sin(e.t * 1.7)) * (0.85 + 0.45 * prox) * e.fator_pupila
    rn = r / Ri
    fibras = 0.5 + 0.5 * np.sin(ang * 34 + 3.0 * np.sin(ang * 5 + rn * 6))
    ir_C = mix(c["iris_a"], c["iris_b"], np.clip(rn, 0, 1) ** 0.8)
    ir_L = (0.55 + 0.45 * fibras) * (0.85 + 0.35 * np.exp(-((rn - 0.45) / 0.08) ** 2))
    ir_L = ir_L * (1 - 0.75 * smoothstep(0.82, 1.0, rn))
    ir_L = np.clip(ir_L * (0.55 + 0.45 * sombra ** 0.7) * 0.85, 0, 1)
    ir_L = np.where(r < Rp, 0.0, ir_L)

    no_iris = rn < 1.0
    L = np.where(no_iris, ir_L, esc_L)
    C = np.where(no_iris[..., None], ir_C, esc_C)

    # reflexo e cílios
    brilho = np.exp(-(((Xl - (icx - 0.10)) ** 2 + (Yl - (icy + 0.10)) ** 2) / 0.0020))
    L = np.maximum(L, brilho)
    C = np.where((brilho > 0.35)[..., None], cor_const(BRANCO), C)
    borda = (np.abs(Yl - topo) < 0.02) | (np.abs(Yl - base) < 0.012)
    L = np.where(borda, L * 0.35, L)

    return np.where(dentro, L, pele_L), np.where(dentro[..., None], C, pele_C), dentro


def camada_olho(e):
    res = None
    for k, (ox, esc) in enumerate(e.posicoes_olhos()):
        L, C, d = um_olho(e, ox, esc, *e.olhar[k])
        if res is None:
            res = (L, C, d)
        else:                                          # junta o segundo olho
            L0, C0, d0 = res
            res = (np.where(d0, L0, np.where(d, L, np.maximum(L0, L))),
                   np.where(d0[..., None], C0, np.where(d[..., None], C, C0)),
                   d0 | d)
    return res[0], res[1], SEM_GLIFO


# ----------------------------------------------------------------------------
# CAMADA: CORAÇÃO (equação implícita) - bate mais rápido quando você clica
# ----------------------------------------------------------------------------
def camada_coracao(e):
    c = e.cores
    b = e.fase_cora % 1.0
    pulso = 1 + 0.07 * math.exp(-8 * b) + 0.04 * math.exp(-8 * ((b - 0.25) % 1.0))
    s = 0.55 * pulso
    cx, cy = e.mouse * 0.15                            # o coração acompanha o mouse de leve
    hx = (X - cx) / s
    hy = (Y - cy) / s + 0.12
    f = (hx ** 2 + hy ** 2 - 1) ** 3 - hx ** 2 * hy ** 3
    prof = np.clip(-f, 0, 1) ** 0.45
    L = 0.30 + 0.70 * prof + 0.35 * np.exp(-(((hx + 0.45) ** 2 + (hy - 0.55) ** 2) / 0.05))
    L = np.where(f < 0, np.clip(L, 0, 1), 0.0)
    C = mix(c["ac1"], c["ac2"], np.clip((prof - 0.4) / 0.6, 0, 1))
    return L, C, SEM_GLIFO


# ----------------------------------------------------------------------------
# CAMADA: GALÁXIA em espiral - o centro segue o mouse e o clique acelera o giro
# ----------------------------------------------------------------------------
def camada_galaxia(e):
    c = e.cores
    cx, cy = e.mouse * 0.30
    x, y = X - cx, (Y - cy) * 1.35
    r = np.hypot(x, y) + 1e-4
    th = np.arctan2(y, x)
    fase = 2 * (th + 3.0 * np.log(r + 0.05)) - e.fase_gal    # espiral logarítmica
    braco = (0.5 + 0.5 * np.cos(fase)) ** 2.5
    dens = 1.7 * np.exp(-(r / 0.85) ** 2) * (0.12 + 0.88 * braco) + 1.4 * np.exp(-(r / 0.10) ** 2)
    brilho = 0.75 + 0.25 * np.sin(e.t * 3 + RUIDO * 40)       # cada célula pisca
    L = np.clip(dens * brilho, 0, 1)
    L = np.where(L < 0.08, 0.0, L)
    C = mix(c["ac2"], c["ac1"], smoothstep(0.05, 0.7, r))
    nucleo = np.exp(-(r / 0.12) ** 2)[..., None]
    C = C * (1 - nucleo) + np.array([255, 240, 210], np.float32) * nucleo
    return L.astype(np.float32), C, SEM_GLIFO


# ----------------------------------------------------------------------------
# CAMADA: CHUVA DE CÓDIGO - o mouse é uma lanterna que revela glifos
# ----------------------------------------------------------------------------
M_VEL = rng.uniform(5, 16, COLS)
M_OFF = rng.uniform(0, ROWS + 30, COLS)
M_CAUDA = rng.uniform(8, 26, COLS)


def camada_codigo(e):
    c = e.cores
    cabeca = (e.t * M_VEL + M_OFF) % (ROWS + M_CAUDA + 12)    # linha da "cabeça" de cada coluna
    d = cabeca[None, :] - LIN_IDX                              # distância até a cabeça
    cauda = np.clip(1 - d / M_CAUDA[None, :], 0, 1)             # 1 na cabeça, 0 no fim da cauda
    L = np.where(d >= 0, cauda ** 1.5, 0.0)

    mcol = (e.mouse[0] * W / 2 + W / 2) / CW
    mlin = (H / 2 - e.mouse[1] * W / 2) / CH
    dx, dy = (COL_IDX + 0.5 - mcol) * CW, (LIN_IDX + 0.5 - mlin) * CH
    luz = np.exp(-(dx ** 2 + dy ** 2) / (2 * 110.0 ** 2))
    pisca = 0.5 + 0.5 * np.sin(e.t * 9 + RUIDO * 30)
    L = np.clip(L * (1 + 1.8 * luz), 0, 1)
    L = np.maximum(L, 0.45 * luz * pisca).astype(np.float32)

    ponta = ((d >= 0) & (d < 1.5))[..., None]
    C = np.where(ponta, cor_const(BRANCO), cor_const(c["codigo"]))
    troca = np.floor(e.t * 8 + COL_IDX * 0.37).astype(np.int64)  # glifos mudam ~8x por segundo
    G = ((COL_IDX * 7919 + LIN_IDX * 104729 + troca * 31) % NG).astype(np.int32)
    return L, C, np.where(L > 0.04, G, -1)


# ----------------------------------------------------------------------------
# CAMADA: TEXTO que você digita (tecla T)
# ----------------------------------------------------------------------------
def camada_texto(e):
    c = e.cores
    L = (e.texto_L * (0.85 + 0.15 * np.sin(e.t * 2 + X * 5))).astype(np.float32)
    C = mix(c["ac1"], c["ac2"], 0.5 + 0.5 * np.sin(X * 3 + e.t * 1.5))
    return L, C, SEM_GLIFO


CAMADAS = {"olho": camada_olho, "coracao": camada_coracao, "galaxia": camada_galaxia,
           "codigo": camada_codigo, "texto": camada_texto}
MODOS = list(CAMADAS)
VIS_ESTRELAS = {"olho": 0.0, "coracao": 0.65, "galaxia": 0.2, "codigo": 0.0, "texto": 0.35}

# ----------------------------------------------------------------------------
# ESTRELAS que piscam (camada extra, visibilidade depende do modo)
# ----------------------------------------------------------------------------
NE = 110
_st_r = rng.integers(0, ROWS, NE)
_st_c = rng.integers(0, COLS, NE)
_st_fase = rng.uniform(0, 6.28, NE)
_st_vel = rng.uniform(1.0, 3.5, NE)
_st_grande = rng.random(NE) > 0.75
_st_cor2 = rng.random(NE) < 0.5


def camada_estrelas(e):
    c = e.cores
    L = np.zeros((ROWS, COLS), np.float32)
    C = np.full((ROWS, COLS, 3), 255, np.float32)
    for i in range(NE):
        b = 0.5 + 0.5 * math.sin(e.t * _st_vel[i] + _st_fase[i])
        cor = c["ac2"] if _st_cor2[i] else AZUL_ESTRELA
        pontos = [(0, 0, 1.0)]
        if _st_grande[i] and b > 0.3:                  # brilho em cruz
            pontos += [(0, 1, .55), (0, -1, .55), (1, 0, .55), (-1, 0, .55), (0, 2, .3), (0, -2, .3)]
        for dr, dc, k in pontos:
            rr, cc = _st_r[i] + dr, _st_c[i] + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS and b * k > L[rr, cc]:
                L[rr, cc] = b * k
                C[rr, cc] = cor
    return L, C


# ----------------------------------------------------------------------------
# COMPOSIÇÃO: modo atual + modo alvo + estrelas + partículas + ondas
# ----------------------------------------------------------------------------
def compor(e):
    s = e.s
    La, Ca, Ga = CAMADAS[e.modo_atual](e)
    camadas = [(La, Ca, Ga)]
    vis = VIS_ESTRELAS[e.modo_atual]
    if e.modo_alvo is not None:
        Lb, Cb, Gb = CAMADAS[e.modo_alvo](e)
        La = La * np.clip((RUIDO - (s * 1.15 - 0.05)) * 6, 0, 1)             # o antigo se desfaz...
        h = np.clip((s - 0.35) / 0.65, 0, 1)
        Lb = Lb * np.clip((h * 1.3 - RUIDO) * 5, 0, 1)                       # ...o novo se forma
        camadas = [(La, Ca, Ga), (Lb, Cb, Gb)]
        vis = vis * (1 - s) + VIS_ESTRELAS[e.modo_alvo] * s + 0.55 * math.sin(math.pi * s)
    Le, Ce = camada_estrelas(e)
    camadas.append((Le * float(np.clip(vis, 0, 1)), Ce, SEM_GLIFO))

    Ls = np.stack([c[0] for c in camadas])
    Cs = np.stack([c[1] for c in camadas])
    Gs = np.stack([c[2] for c in camadas])
    venc = Ls.argmax(0)                                                      # a mais clara vence
    L = np.take_along_axis(Ls, venc[None], 0)[0]
    C = np.take_along_axis(Cs, venc[None, ..., None], 0)[0]
    G = np.take_along_axis(Gs, venc[None], 0)[0]

    # por cima de tudo: partículas e ondas de choque dos cliques
    Lo = np.zeros((ROWS, COLS), np.float32)
    Co = np.full((ROWS, COLS, 3), 255, np.float32)
    e.particulas.desenhar(Lo, Co)
    for x0, y0, t0 in e.ondas:
        dtw = e.t - t0
        anel = (np.exp(-((np.hypot(X - x0, Y - y0) - 1.2 * dtw) / 0.045) ** 2)
                * math.exp(-1.1 * dtw)).astype(np.float32)
        melhor = anel > Lo
        Lo = np.where(melhor, anel, Lo)
        Co = np.where(melhor[..., None], cor_const(e.cores["ac2"]), Co)
    usa = Lo > L
    return (np.where(usa, Lo, L), np.where(usa[..., None], Co, C), np.where(usa, -1, G))


def desenhar(L, C, G):
    """Converte (luminosidade, cor, glifo) por célula em pixels, tudo vetorizado."""
    idx = (np.clip(L, 0, 1) ** 0.85 * (len(RAMP) - 1) + 0.5).astype(int)
    usa = G >= 0
    idx = np.where(usa, len(RAMP) + G, idx)                   # glifo específico (chuva de código)
    mask = ATLAS[idx]                                         # (ROWS, COLS, CW, CH)
    mask = mask.transpose(1, 2, 0, 3).reshape(COLS * CW, ROWS * CH)
    tom = C / (C.max(axis=2, keepdims=True) + 1e-6) * 255     # só o "tom"; brilho = densidade
    tom = tom * np.where(usa, np.clip(L, 0, 1) ** 0.8, 1.0)[..., None]
    tom = np.repeat(np.repeat(tom.transpose(1, 0, 2), CW, 0), CH, 1)
    pygame.surfarray.blit_array(screen, (mask[..., None] * tom).astype(np.uint8))


# ----------------------------------------------------------------------------
# AJUDA NA TELA
# ----------------------------------------------------------------------------
LINHAS_AJUDA = [
    "ESPAÇO / ← →  trocar de modo     1-5  ir direto ao modo",
    "C  tema de cores     D  um/dois olhos     T  digitar texto",
    "P  rastro do mouse   S  foto (PNG)        H  esconder ajuda",
    "Clique: fogos + susto | segurar: chafariz | botão direito ou F: focar",
    "Deixe o mouse parado por alguns segundos... o olho dorme.",
]


def desenhar_ajuda(e):
    visivel = e.ajuda if e.ajuda is not None else e.t < 12
    linhas = list(LINHAS_AJUDA) if visivel else []
    if e.digitando:
        linhas = [f"Texto: {e.buffer}_    (Enter confirma | Esc cancela)"]
    elif visivel:
        linhas.append(f"modo: {e.modo_atual}    tema: {e.cores['nome']}")
    if not linhas:
        return
    larg = max(font.size(l)[0] for l in linhas) + 20
    caixa = pygame.Surface((larg, len(linhas) * CH + 12), pygame.SRCALPHA)
    caixa.fill((0, 0, 0, 170))
    for i, l in enumerate(linhas):
        caixa.blit(font.render(l, True, (220, 220, 220)), (10, 6 + i * CH))
    screen.blit(caixa, (8, 8 if not e.digitando else H - caixa.get_height() - 8))


# ----------------------------------------------------------------------------
# LOOP PRINCIPAL
# ----------------------------------------------------------------------------
def main():
    clock = pygame.time.Clock()
    e = Estado()
    while True:
        dt = min(clock.tick(FPS) / 1000, 0.05)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif ev.type == pygame.KEYDOWN:
                if e.tecla(ev):
                    pygame.quit()
                    sys.exit()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                e.clique(ev.pos)

        e.atualizar(dt, pygame.mouse.get_pos(), pygame.mouse.get_focused(),
                    pygame.mouse.get_pressed(), pygame.key.get_pressed()[pygame.K_f] and not e.digitando)
        L, C, G = compor(e)
        desenhar(L, C, G)

        if e.foto_pendente:                                    # foto sem a ajuda por cima
            e.n_fotos += 1
            pygame.image.save(screen, f"olho_ascii_{e.n_fotos:03d}.png")
            e.foto_pendente = False
        desenhar_ajuda(e)
        pygame.display.flip()


if __name__ == "__main__":
    main()
