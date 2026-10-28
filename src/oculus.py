"""
ASCII Shader Engine & Interactive Eye (v3.0)
============================================

Motor de renderização procedural em ASCII em tempo real utilizando Pygame e NumPy.
Transforma campos escalares de luminosidade e matrizes de cores RGB em gráficos
de caracteres vetorizados com física de partículas e distorção espacial.

Controles Interativos:
----------------------
- [ESPAÇO] / [←][→] : Alternar entre os modos visuais (transição por dissolução)
- [1] a [6]         : Acesso direto aos modos (Olho, Coração, Galáxia, Código, Texto, Vórtice)
- [Mouse Movimento] : Olhar segue o cursor; girar rápido causa tontura; parado faz dormir
- [Clique Esquerdo] : Onda de choque com distorção espacial (clicar no olho causa irritação)
- [Segurar Clique]  : Emissor contínuo de faíscas com física
- [Botão Direito/F] : Focar olhar (estreita pálpebras e dilata a pupila)
- [Scroll Mouse]    : Zoom In / Zoom Out dinâmico na malha matemática
- [G] / [Clique Meio]: Liga/Desliga Poço Gravitacional no cursor (atrai partículas e curva o espaço)
- [E]               : Alternar expressão facial do olho (Neutro, Raiva, Cético, Melancólico)
- [C]               : Alternar tema de cores
- [R]               : Alternar rampa de caracteres ASCII (Clássico, Blocos, Binário, Minimal)
- [D]               : Alternar entre Ciclope (1 olho) e Par de Olhos (2 olhos)
- [T]               : Digitar texto customizado em tempo real
- [P]               : Ligar/Desligar rastro de partículas do mouse
- [S]               : Salvar captura de tela limpa (PNG)
- [H]               : Mostrar/Ocultar HUD e telemetria

Requisitos:
-----------
    pip install pygame numpy
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray
import pygame


# ============================================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================================

@dataclass(frozen=True)
class EngineConfig:
    """Parâmetros globais de configuração do motor gráfico."""
    font_size: int = 14
    fps: int = 60
    transition_duration: float = 1.5
    max_particles: int = 1200
    num_stars: int = 130
    glyph_charset: str = "01{}[]<>/\\|=+*#$&%;:ABCDEFabcdef23456789"


@dataclass(frozen=True)
class ColorTheme:
    """Estrutura de paleta de cores para os modos de renderização."""
    name: str
    iris_inner: Tuple[int, int, int]
    iris_outer: Tuple[int, int, int]
    skin: Tuple[int, int, int]
    sclera_edge: Tuple[int, int, int]
    accent_primary: Tuple[int, int, int]
    accent_secondary: Tuple[int, int, int]
    code_rain: Tuple[int, int, int]


THEMES: Tuple[ColorTheme, ...] = (
    ColorTheme(
        name="Âmbar",
        iris_inner=(245, 165, 55), iris_outer=(110, 45, 18), skin=(235, 140, 115),
        sclera_edge=(225, 95, 85), accent_primary=(255, 70, 140),
        accent_secondary=(255, 190, 215), code_rain=(60, 255, 120),
    ),
    ColorTheme(
        name="Oceano",
        iris_inner=(110, 225, 255), iris_outer=(10, 60, 140), skin=(120, 150, 215),
        sclera_edge=(90, 120, 210), accent_primary=(50, 130, 255),
        accent_secondary=(170, 225, 255), code_rain=(80, 220, 255),
    ),
    ColorTheme(
        name="Esmeralda",
        iris_inner=(150, 255, 120), iris_outer=(10, 90, 40), skin=(130, 200, 140),
        sclera_edge=(110, 190, 120), accent_primary=(40, 220, 120),
        accent_secondary=(190, 255, 210), code_rain=(60, 255, 100),
    ),
    ColorTheme(
        name="Rubi Carmesim",
        iris_inner=(255, 90, 70), iris_outer=(100, 5, 15), skin=(200, 85, 75),
        sclera_edge=(230, 60, 60), accent_primary=(255, 50, 60),
        accent_secondary=(255, 170, 120), code_rain=(255, 90, 60),
    ),
    ColorTheme(
        name="Cyberpunk",
        iris_inner=(255, 80, 230), iris_outer=(60, 20, 170), skin=(150, 95, 225),
        sclera_edge=(200, 80, 230), accent_primary=(255, 60, 200),
        accent_secondary=(110, 240, 255), code_rain=(0, 255, 200),
    ),
    ColorTheme(
        name="Monocromático",
        iris_inner=(240, 240, 240), iris_outer=(60, 60, 60), skin=(160, 160, 160),
        sclera_edge=(130, 130, 130), accent_primary=(200, 200, 200),
        accent_secondary=(255, 255, 255), code_rain=(220, 220, 220),
    ),
)

ASCII_RAMPS: Dict[str, str] = {
    "Clássico": " .:-=+*#%@",
    "Blocos": " ░▒▓█",
    "Binário": " .01",
    "Minimal": " ·∘○◎●",
    "Denso": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
}

EXPRESSIONS: Tuple[str, ...] = ("Neutro", "Raiva", "Cético", "Melancólico")
MODES: Tuple[str, ...] = ("olho", "coracao", "galaxia", "codigo", "vortice", "texto")
STAR_VISIBILITY: Dict[str, float] = {
    "olho": 0.0, "coracao": 0.65, "galaxia": 0.25, "codigo": 0.0, "vortice": 0.4, "texto": 0.4
}

COLOR_WHITE = (255, 255, 255)
COLOR_STAR_BLUE = (200, 220, 255)
COLOR_BLOODSHOT = (240, 40, 40)


# ============================================================================
# FUNÇÕES MATEMÁTICAS AUXILIARES
# ============================================================================

def smoothstep(edge0: float, edge1: float, x: NDArray[np.float32]) -> NDArray[np.float32]:
    """Interpolação polinomial Hermite suave entre edge0 e edge1."""
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix_colors(
    c1: Tuple[int, int, int] | NDArray[np.float32],
    c2: Tuple[int, int, int] | NDArray[np.float32],
    t: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Interpolação linear vetorizada entre duas cores RGB."""
    arr1 = np.asarray(c1, dtype=np.float32)
    arr2 = np.asarray(c2, dtype=np.float32)
    return arr1 * (1.0 - t[..., None]) + arr2 * t[..., None]


# ============================================================================
# SISTEMA DE PARTÍCULAS VETORIZADO
# ============================================================================

class ParticleSystem:
    """Gerenciador de partículas 100% vetorizado em NumPy com suporte a atratores."""

    def __init__(self, max_particles: int, cw: int, ch: int) -> None:
        self.n = max_particles
        self.cw = cw
        self.ch = ch
        self.cursor = 0

        self.pos = np.zeros((self.n, 2), dtype=np.float32)
        self.vel = np.zeros((self.n, 2), dtype=np.float32)
        self.life = np.zeros(self.n, dtype=np.float32)
        self.max_life = np.ones(self.n, dtype=np.float32)
        self.color = np.full((self.n, 3), 255.0, dtype=np.float32)
        self.gravity = np.zeros(self.n, dtype=np.float32)
        self.rng = np.random.default_rng()

    def emit(
        self,
        col: float,
        row: float,
        count: int,
        v_min: float,
        v_max: float,
        lifetime: float,
        colors: List[Tuple[int, int, int]],
        gravity_px: float = 0.0,
        angle_range: Tuple[float, float] = (0.0, 2.0 * math.pi),
    ) -> None:
        """Emite um lote de partículas na posição especificada (em células)."""
        idx = (self.cursor + np.arange(count)) % self.n
        self.cursor = (self.cursor + count) % self.n

        angles = self.rng.uniform(angle_range[0], angle_range[1], count)
        speeds = self.rng.uniform(v_min, v_max, count)

        self.pos[idx] = (col, row)
        self.vel[idx, 0] = np.cos(angles) * speeds / self.cw
        self.vel[idx, 1] = -np.sin(angles) * speeds / self.ch
        self.life[idx] = self.max_life[idx] = self.rng.uniform(lifetime * 0.6, lifetime, count)

        palette = np.asarray(colors, dtype=np.float32)
        self.color[idx] = palette[self.rng.integers(0, len(colors), count)]
        self.gravity[idx] = gravity_px / self.ch

    def update(
        self,
        dt: float,
        attractor_cell: Optional[Tuple[float, float]] = None,
    ) -> None:
        """Atualiza cinemática, gravidade vertical e atração orbital."""
        active = self.life > 0.0
        if not np.any(active):
            return

        if attractor_cell is not None:
            dx = attractor_cell[0] - self.pos[active, 0]
            dy = attractor_cell[1] - self.pos[active, 1]
            dist = np.hypot(dx, dy) + 1.5
            force = 240.0 / (dist * dist + 10.0)
            # Força centrípeta + tangencial (efeito redemoinho)
            self.vel[active, 0] += (dx / dist * force - dy / dist * force * 0.6) * dt
            self.vel[active, 1] += (dy / dist * force + dx / dist * force * 0.6) * dt
        else:
            self.vel[active, 1] += self.gravity[active] * dt

        self.pos[active] += self.vel[active] * dt
        self.vel[active] *= math.exp(-1.1 * dt)
        self.life[active] -= dt

    def render_onto(
        self,
        lum_grid: NDArray[np.float32],
        col_grid: NDArray[np.float32],
        cols: int,
        rows: int,
    ) -> None:
        """Projeta as partículas ativas nas matrizes de luminosidade e cor."""
        cc = np.floor(self.pos[:, 0]).astype(np.int32)
        rr = np.floor(self.pos[:, 1]).astype(np.int32)
        valid = (self.life > 0.0) & (cc >= 0) & (cc < cols) & (rr >= 0) & (rr < rows)

        if not np.any(valid):
            return

        brightness = np.clip(self.life[valid] / self.max_life[valid], 0.0, 1.0) ** 0.7
        np.maximum.at(lum_grid, (rr[valid], cc[valid]), brightness)
        col_grid[rr[valid], cc[valid]] = self.color[valid]


# ============================================================================
# ESTADO DA SIMULAÇÃO
# ============================================================================

@dataclass
class Shockwave:
    """Representa uma onda de choque radial no espaço do mundo."""
    x: float
    y: float
    t0: float


@dataclass
class SimulationState:
    """Armazena todo o estado mutável e cinemático da aplicação."""
    t: float = 0.0
    current_mode: str = "olho"
    target_mode: Optional[str] = None
    transition_linear: float = 0.0
    transition_smooth: float = 0.0

    theme_idx: int = 0
    ramp_idx: int = 0
    expression_idx: int = 0
    dual_eyes: bool = False
    mouse_trail: bool = True
    gravity_well: bool = False
    zoom: float = 1.0
    target_zoom: float = 1.0

    # Cinemática do olhar e mouse
    gaze: List[List[float]] = field(default_factory=lambda: [[0.0, 0.0], [0.0, 0.0]])
    mouse_world: NDArray[np.float32] = field(default_factory=lambda: np.zeros(2, dtype=np.float32))
    prev_mouse_px: Optional[Tuple[int, int]] = None
    mouse_speed: float = 0.0
    idle_time: float = 0.0
    prev_angle: float = 0.0

    # Reações orgânicas do olho
    sleepiness: float = 0.0
    surprise: float = 0.0
    focus: float = 0.0
    irritation: float = 0.0
    dizziness: float = 0.0
    dizzy_phase: float = 0.0
    eye_openness: float = 1.0
    pupil_scale: float = 1.0
    next_blink: float = 2.5
    blink_start: float = -1.0

    # Fases acumuladas para animações contínuas
    heart_phase: float = 0.0
    galaxy_phase: float = 0.0
    vortex_phase: float = 0.0

    # Efeitos e UI
    shockwaves: List[Shockwave] = field(default_factory=list)
    custom_text: str = "LEO"
    input_buffer: str = ""
    is_typing: bool = False
    show_hud: Optional[bool] = None
    screenshot_pending: bool = False
    screenshot_count: int = 0
    toast_message: str = ""
    toast_timer: float = 0.0

    @property
    def theme(self) -> ColorTheme:
        return THEMES[self.theme_idx]

    @property
    def ramp_name(self) -> str:
        return list(ASCII_RAMPS.keys())[self.ramp_idx]

    @property
    def expression(self) -> str:
        return EXPRESSIONS[self.expression_idx]

    def notify(self, message: str, duration: float = 2.2) -> None:
        """Exibe uma notificação temporária no HUD."""
        self.toast_message = message
        self.toast_timer = duration

    def eye_transforms(self) -> List[Tuple[float, float]]:
        """Retorna lista de (deslocamento_x, escala) para 1 ou 2 olhos."""
        return [(-0.50, 0.55), (0.50, 0.55)] if self.dual_eyes else [(0.0, 1.0)]


# ============================================================================
# MOTOR PRINCIPAL DE RENDERIZAÇÃO ASCII
# ============================================================================

class AsciiShaderEngine:
    """Motor principal que gerencia a janela, atlas de glifos, camadas e eventos."""

    def __init__(self, config: EngineConfig = EngineConfig()) -> None:
        pygame.init()
        self.cfg = config
        self.rng = np.random.default_rng(7)

        # Inicialização tipográfica
        font_path = pygame.font.match_font("menlo,dejavusansmono,consolas,couriernew,liberationmono")
        self.font = (
            pygame.font.Font(font_path, self.cfg.font_size)
            if font_path
            else pygame.font.Font(None, self.cfg.font_size + 4)
        )
        self.cw, self.ch = self.font.size("M")

        # Dimensionamento adaptativo da grade
        try:
            desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
        except Exception:
            desktop_w, desktop_h = 1440, 900

        target_h = min(60 * self.ch, int(desktop_h * 0.82))
        target_w = min(int(target_h * 1.12), int(desktop_w * 0.92), 136 * self.cw)
        self.cols = max(60, target_w // self.cw)
        self.rows = max(32, target_h // self.ch)
        self.width = self.cols * self.cw
        self.height = self.rows * self.ch

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("ASCII Shader Engine v3.0 — Interactive Eye")

        # Matrizes espaciais base
        px = (np.arange(self.cols) + 0.5) * self.cw
        py = (np.arange(self.rows) + 0.5) * self.ch
        x_grid, y_grid = np.meshgrid(px, py)
        self.base_x = ((x_grid - self.width / 2.0) / (self.width / 2.0)).astype(np.float32)
        self.base_y = (-(y_grid - self.height / 2.0) / (self.width / 2.0)).astype(np.float32)
        self.col_idx, self.row_idx = np.meshgrid(np.arange(self.cols), np.arange(self.rows))

        self.noise_grid = self.rng.random((self.rows, self.cols), dtype=np.float32)
        self.no_glyph = np.full((self.rows, self.cols), -1, dtype=np.int32)

        # Estado, Partículas e Atlas
        self.state = SimulationState()
        self.particles = ParticleSystem(self.cfg.max_particles, self.cw, self.ch)
        self.text_mask = self._bake_text_mask(self.state.custom_text)

        self.current_ramp_str = ASCII_RAMPS[self.state.ramp_name]
        self.atlas = self._build_atlas(self.current_ramp_str)

        # Dados pré-computados da Chuva de Código e Campo Estelar
        self.rain_vel = self.rng.uniform(5.0, 16.0, self.cols).astype(np.float32)
        self.rain_off = self.rng.uniform(0.0, self.rows + 30.0, self.cols).astype(np.float32)
        self.rain_tail = self.rng.uniform(8.0, 26.0, self.cols).astype(np.float32)

        self.star_r = self.rng.integers(0, self.rows, self.cfg.num_stars)
        self.star_c = self.rng.integers(0, self.cols, self.cfg.num_stars)
        self.star_phase = self.rng.uniform(0.0, 2.0 * math.pi, self.cfg.num_stars).astype(np.float32)
        self.star_speed = self.rng.uniform(1.0, 3.5, self.cfg.num_stars).astype(np.float32)
        self.star_big = self.rng.random(self.cfg.num_stars) > 0.75
        self.star_alt_col = self.rng.random(self.cfg.num_stars) < 0.5

        self.layer_dispatch: Dict[
            str, Callable[[NDArray[np.float32], NDArray[np.float32]], Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]]
        ] = {
            "olho": self._layer_eye,
            "coracao": self._layer_heart,
            "galaxia": self._layer_galaxy,
            "codigo": self._layer_code_rain,
            "vortice": self._layer_vortex,
            "texto": self._layer_text,
        }

    # ------------------------------------------------------------------------
    # RECURSOS E PRÉ-PROCESSAMENTO
    # ------------------------------------------------------------------------

    def _build_atlas(self, ramp: str) -> NDArray[np.float32]:
        """Constrói o tensor 3D (N, CW, CH) contendo a máscara alfa de cada glifo."""
        all_chars = ramp + self.cfg.glyph_charset
        atlas = np.zeros((len(all_chars), self.cw, self.ch), dtype=np.float32)
        for i, ch in enumerate(all_chars):
            if ch == " ":
                continue
            surf = self.font.render(ch, True, COLOR_WHITE)
            alpha = pygame.surfarray.array_alpha(surf).astype(np.float32) / 255.0
            w_lim, h_lim = min(self.cw, alpha.shape[0]), min(self.ch, alpha.shape[1])
            atlas[i, :w_lim, :h_lim] = alpha[:w_lim, :h_lim]
        return atlas

    def _bake_text_mask(self, text: str) -> NDArray[np.float32]:
        """Renderiza uma string em alta resolução e reduz para a escala da grade."""
        if not text:
            return np.zeros((self.rows, self.cols), dtype=np.float32)
        surf = pygame.Surface((self.width, self.height))
        surf.fill((0, 0, 0))
        size = int(self.height * 0.55)
        while True:
            sys_font = pygame.font.SysFont(["helveticaneue", "arial", "dejavusans"], size, bold=True)
            rendered = sys_font.render(text, True, COLOR_WHITE)
            if rendered.get_width() <= self.width * 0.9 or size <= 12:
                break
            size = int(size * 0.9)

        pos_x = (self.width - rendered.get_width()) // 2
        pos_y = (self.height - rendered.get_height()) // 2
        surf.blit(rendered, (pos_x, pos_y))
        small = pygame.transform.smoothscale(surf, (self.cols, self.rows))
        arr = pygame.surfarray.array3d(small)[:, :, 0].astype(np.float32) / 255.0
        return (np.clip(arr.T * 1.4, 0.0, 1.0) ** 0.7).astype(np.float32)

    def _const_color(self, rgb: Tuple[int, int, int]) -> NDArray[np.float32]:
        """Expande uma tupla RGB para o formato da grade (ROWS, COLS, 3)."""
        return np.broadcast_to(np.asarray(rgb, dtype=np.float32), (self.rows, self.cols, 3))

    # ------------------------------------------------------------------------
    # GERENCIAMENTO DE EVENTOS E INTERATIVIDADE
    # ------------------------------------------------------------------------

    def switch_mode(self, target: str) -> None:
        """Inicia a transição suave por ruído para outro modo visual."""
        if self.state.target_mode is None and target != self.state.current_mode:
            self.state.target_mode = target
            self.state.transition_linear = 0.0
            self.state.notify(f"Modo: {target.upper()}")

    def cycle_mode(self, step: int) -> None:
        idx = MODES.index(self.state.current_mode)
        self.switch_mode(MODES[(idx + step) % len(MODES)])

    def handle_mouse_click(self, pos: Tuple[int, int], button: int) -> None:
        """Processa cliques do mouse (ondas de choque, irritação ocular, poço gravitacional)."""
        s = self.state
        if button == 2:  # Clique do meio
            s.gravity_well = not s.gravity_well
            s.notify(f"Poço Gravitacional: {'ATIVO' if s.gravity_well else 'OFF'}")
            return

        if button != 1:
            return

        # Coordenadas normalizadas do mundo (considerando o zoom atual)
        wx = ((pos[0] - self.width / 2.0) / (self.width / 2.0)) / s.zoom
        wy = (-(pos[1] - self.height / 2.0) / (self.width / 2.0)) / s.zoom

        s.shockwaves.append(Shockwave(wx, wy, s.t))
        s.surprise = 1.0

        # Verifica se o usuário clicou diretamente dentro de algum olho para irritá-lo
        if s.current_mode == "olho":
            for ox, scale in s.eye_transforms():
                if math.hypot((wx - ox) / scale, wy / scale) < 0.55:
                    s.irritation = 1.0
                    s.notify("Olho irritado!")
                    break

        t_col = s.theme
        self.particles.emit(
            col=pos[0] / self.cw,
            row=pos[1] / self.ch,
            count=85,
            v_min=150.0,
            v_max=580.0,
            lifetime=1.35,
            colors=[t_col.accent_primary, t_col.accent_secondary, COLOR_WHITE],
            gravity_px=260.0,
        )

    def handle_keydown(self, ev: pygame.event.Event) -> bool:
        """Processa atalhos de teclado e entrada de texto. Retorna True para encerrar."""
        s = self.state
        if s.is_typing:
            if ev.key == pygame.K_RETURN:
                if s.input_buffer.strip():
                    s.custom_text = s.input_buffer
                s.is_typing = False
                self.text_mask = self._bake_text_mask(s.custom_text)
                s.notify(f"Texto definido: {s.custom_text}")
            elif ev.key == pygame.K_ESCAPE:
                s.is_typing = False
                self.text_mask = self._bake_text_mask(s.custom_text)
            else:
                if ev.key == pygame.K_BACKSPACE:
                    s.input_buffer = s.input_buffer[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(s.input_buffer) < 14:
                    s.input_buffer += ev.unicode
                self.text_mask = self._bake_text_mask(s.input_buffer + "_")
            return False

        k = ev.key
        if k == pygame.K_ESCAPE:
            return True
        elif k in (pygame.K_SPACE, pygame.K_RIGHT):
            self.cycle_mode(1)
        elif k == pygame.K_LEFT:
            self.cycle_mode(-1)
        elif pygame.K_1 <= k <= pygame.K_6:
            self.switch_mode(MODES[k - pygame.K_1])
        elif k == pygame.K_c:
            s.theme_idx = (s.theme_idx + 1) % len(THEMES)
            s.notify(f"Tema: {s.theme.name}")
        elif k == pygame.K_r:
            s.ramp_idx = (s.ramp_idx + 1) % len(ASCII_RAMPS)
            self.current_ramp_str = ASCII_RAMPS[s.ramp_name]
            self.atlas = self._build_atlas(self.current_ramp_str)
            s.notify(f"Rampa ASCII: {s.ramp_name}")
        elif k == pygame.K_e:
            s.expression_idx = (s.expression_idx + 1) % len(EXPRESSIONS)
            s.notify(f"Expressão: {s.expression}")
        elif k == pygame.K_d:
            s.dual_eyes = not s.dual_eyes
            s.notify("Dois Olhos" if s.dual_eyes else "Olho Único")
        elif k == pygame.K_g:
            s.gravity_well = not s.gravity_well
            s.notify(f"Poço Gravitacional: {'ATIVO' if s.gravity_well else 'OFF'}")
        elif k == pygame.K_p:
            s.mouse_trail = not s.mouse_trail
            s.notify(f"Rastro do Mouse: {'ON' if s.mouse_trail else 'OFF'}")
        elif k == pygame.K_s:
            s.screenshot_pending = True
        elif k == pygame.K_h:
            currently_visible = s.show_hud if s.show_hud is not None else (s.t < 14.0)
            s.show_hud = not currently_visible
        elif k == pygame.K_t and s.target_mode is None:
            s.is_typing = True
            s.input_buffer = ""
            self.text_mask = self._bake_text_mask("_")
            self.switch_mode("texto")
        return False

    # ------------------------------------------------------------------------
    # ATUALIZAÇÃO FÍSICA E CINEMÁTICA
    # ------------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Atualiza todos os estados contínuos, física do olhar e partículas."""
        s = self.state
        s.t += dt
        if s.toast_timer > 0.0:
            s.toast_timer = max(0.0, s.toast_timer - dt)

        # Interpolação suave do Zoom
        s.zoom += (s.target_zoom - s.zoom) * (1.0 - math.exp(-dt * 10.0))

        mx, my = pygame.mouse.get_pos()
        focused = pygame.mouse.get_focused()
        buttons = pygame.mouse.get_pressed()
        keys = pygame.key.get_pressed()

        # Posição do mouse no espaço do mundo
        if focused:
            target_world = np.array(
                [(mx - self.width / 2.0) / (self.width / 2.0), -(my - self.height / 2.0) / (self.width / 2.0)],
                dtype=np.float32,
            ) / s.zoom
        else:
            target_world = np.array(
                [0.6 * math.sin(s.t * 0.7), 0.3 * math.sin(s.t * 1.1)], dtype=np.float32
            )

        prev_world = s.mouse_world.copy()
        s.mouse_world += (target_world - s.mouse_world) * (1.0 - math.exp(-dt * 12.0))
        inst_speed = float(np.hypot(*(s.mouse_world - prev_world))) / max(dt, 1e-3)
        s.mouse_speed += (inst_speed - s.mouse_speed) * (1.0 - math.exp(-dt * 6.0))

        # Detecção de movimento angular rápido (causa tontura no olho)
        angle = math.atan2(float(s.mouse_world[1]), float(s.mouse_world[0]))
        ang_diff = (angle - s.prev_angle + math.pi) % (2.0 * math.pi) - math.pi
        s.prev_angle = angle
        if abs(ang_diff) / max(dt, 1e-3) > 8.5 and np.hypot(*s.mouse_world) > 0.18:
            s.dizziness = min(1.0, s.dizziness + dt * 1.6)
        else:
            s.dizziness = max(0.0, s.dizziness - dt * 0.65)
        s.dizzy_phase += dt * 11.0

        # Detecção de inatividade (sono)
        moved = s.prev_mouse_px is not None and math.hypot(mx - s.prev_mouse_px[0], my - s.prev_mouse_px[1]) > 1.5
        s.prev_mouse_px = (mx, my)
        if focused and not moved:
            s.idle_time += dt
        else:
            if moved and s.sleepiness > 0.5:
                s.surprise = 1.0
            s.idle_time = 0.0

        # Estados orgânicos
        target_sleep = float(np.clip((s.idle_time - 6.0) / 4.0, 0.0, 1.0))
        s.sleepiness += (target_sleep - s.sleepiness) * (1.0 - math.exp(-dt * 1.5))
        s.surprise = max(0.0, s.surprise - dt * 2.5)
        s.irritation = max(0.0, s.irritation - dt * 0.85)

        focus_active = buttons[2] or (keys[pygame.K_f] and not s.is_typing)
        s.focus += ((1.0 if focus_active else 0.0) - s.focus) * (1.0 - math.exp(-dt * 8.0))

        # Piscada natural (mais rápida se estiver irritado)
        blink_factor = 1.0
        if s.t > s.next_blink and s.blink_start < 0.0:
            s.blink_start = s.t
        if s.blink_start >= 0.0:
            prog = (s.t - s.blink_start) / 0.20
            if prog >= 1.0:
                s.blink_start = -1.0
                interval = 0.45 if s.irritation > 0.3 else (2.0 + 3.0 * abs(math.sin(s.t * 7.3)))
                s.next_blink = s.t + interval
            else:
                blink_factor = 1.0 - math.sin(math.pi * prog)

        s.eye_openness = (
            blink_factor
            * (1.0 + 0.22 * s.surprise + min(s.mouse_speed * 0.12, 0.18))
            * (1.0 - 0.45 * s.focus)
            * (1.0 - 0.35 * s.irritation)
            * (1.0 - 0.85 * s.sleepiness)
        )
        s.pupil_scale = (
            (1.0 - 0.35 * s.surprise)
            * (1.0 + 0.35 * s.focus)
            * (1.0 - 0.30 * s.irritation)
        )

        # Atualização do olhar de cada olho (com perturbação de tontura)
        k_smooth = 1.0 - math.exp(-dt * 12.0)
        for i, (ox, _) in enumerate(s.eye_transforms()):
            tx = float(np.clip((s.mouse_world[0] - ox) / 0.6, -1.0, 1.0))
            ty = float(np.clip(s.mouse_world[1] / 0.5, -1.0, 1.0)) - 0.6 * s.sleepiness
            if s.dizziness > 0.05:
                phase_shift = i * math.pi
                tx += 0.45 * s.dizziness * math.cos(s.dizzy_phase + phase_shift)
                ty += 0.45 * s.dizziness * math.sin(s.dizzy_phase + phase_shift)
            s.gaze[i][0] += (tx - s.gaze[i][0]) * k_smooth
            s.gaze[i][1] += (ty - s.gaze[i][1]) * k_smooth

        # Fases contínuas
        s.heart_phase += dt * (1.3 + 2.0 * s.surprise + (0.8 if s.gravity_well else 0.0))
        s.galaxy_phase += dt * (0.35 + 1.5 * s.surprise + 0.4 * s.mouse_speed)
        s.vortex_phase += dt * (1.2 + 1.8 * s.mouse_speed + (2.0 if s.gravity_well else 0.0))

        # Emissão e atualização de partículas
        col_pos, row_pos = mx / self.cw, my / self.ch
        t_col = s.theme
        if focused and s.mouse_trail and moved:
            self.particles.emit(
                col_pos, row_pos, 2, 12.0, 95.0, 0.85,
                [t_col.accent_primary, t_col.accent_secondary], gravity_px=-30.0
            )
        if focused and buttons[0]:
            self.particles.emit(
                col_pos, row_pos, 4, 200.0, 430.0, 1.05,
                [t_col.accent_secondary, COLOR_WHITE, t_col.accent_primary],
                gravity_px=500.0, angle_range=(math.pi * 0.38, math.pi * 0.62)
            )

        attractor = (col_pos, row_pos) if s.gravity_well else None
        self.particles.update(dt, attractor_cell=attractor)
        s.shockwaves = [w for w in s.shockwaves if s.t - w.t0 < 2.5]

        # Progresso de transição de modo
        if s.target_mode is not None:
            s.transition_linear = min(1.0, s.transition_linear + dt / self.cfg.transition_duration)
            if s.transition_linear >= 1.0:
                s.current_mode = s.target_mode
                s.target_mode = None
                s.transition_linear = 0.0
        s.transition_smooth = s.transition_linear ** 2 * (3.0 - 2.0 * s.transition_linear)

    # ------------------------------------------------------------------------
    # DISTORÇÃO ESPACIAL E CAMADAS PROCEDURAIS
    # ------------------------------------------------------------------------

    def _compute_warped_coords(self) -> Tuple[NDArray[np.float32], NDArray[np.float32]]:
        """Aplica zoom, refração de ondas de choque e lente gravitacional às coordenadas (X, Y)."""
        s = self.state
        xw = self.base_x / s.zoom
        yw = self.base_y / s.zoom

        # Distorção das ondas de choque
        for w in s.shockwaves:
            age = s.t - w.t0
            dx = xw - w.x
            dy = yw - w.y
            dist = np.hypot(dx, dy) + 1e-5
            ring_delta = dist - 1.2 * age
            envelope = np.exp(-((ring_delta / 0.055) ** 2)) * math.exp(-1.1 * age)
            disp = envelope * np.sin(ring_delta * 45.0) * 0.045
            xw = xw + (dx / dist) * disp
            yw = yw + (dy / dist) * disp

        # Lente de torção do Poço Gravitacional
        if s.gravity_well:
            dx = xw - s.mouse_world[0]
            dy = yw - s.mouse_world[1]
            r = np.hypot(dx, dy) + 1e-4
            pull = 0.14 * np.exp(-r * 2.8)
            swirl = 0.45 * np.exp(-r * 3.2)
            cos_s, sin_s = np.cos(swirl), np.sin(swirl)
            rx = dx * cos_s - dy * sin_s
            ry = dx * sin_s + dy * cos_s
            xw = s.mouse_world[0] + rx * (1.0 - pull)
            yw = s.mouse_world[1] + ry * (1.0 - pull)

        return xw.astype(np.float32), yw.astype(np.float32)

    def _render_single_eye(
        self,
        xw: NDArray[np.float32],
        yw: NDArray[np.float32],
        eye_idx: int,
        ox: float,
        scale: float,
        gx: float,
        gy: float,
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.bool_]]:
        """Renderiza um globo ocular completo com expressões, fibras da íris e esclera."""
        s = self.state
        t_col = s.theme
        xl, yl = (xw - ox) / scale, yw / scale
        ew = 0.80
        u = xl / ew
        almond = np.clip(1.0 - u ** 2, 0.0, None) ** 0.85

        # Modificadores de expressão facial nas pálpebras
        expr = s.expression
        slant = 0.0
        extra_open = 1.0
        if expr == "Raiva":
            sign = -1.0 if (not s.dual_eyes or eye_idx == 0) else 1.0
            slant = -0.22 * u * sign if s.dual_eyes else -0.22 * np.abs(u)
        elif expr == "Cético":
            if eye_idx == 0:
                slant = 0.14 * u
                extra_open = 1.18
            else:
                extra_open = 0.72
        elif expr == "Melancólico":
            slant = -0.18 * np.abs(u)
            extra_open = 0.85

        height_open = 0.58 * max(s.eye_openness * extra_open, 0.04)
        top_lid = height_open * almond * (1.0 + 0.25 * gy) + slant * almond
        bot_lid = -height_open * 0.70 * almond * (1.0 - 0.25 * gy) + 0.35 * slant * almond
        inside = (yl < top_lid) & (yl > bot_lid) & (np.abs(u) < 1.0)

        # Pele e dobra palpebral
        vignette = np.clip(1.15 - (xw ** 2 + (yw / 0.75) ** 2) * 0.9, 0.15, 1.0)
        skin_l = (0.20 + 0.04 * np.sin(xw * 40.0) * np.sin(yw * 55.0)) * vignette
        ext_almond = np.clip(1.0 - (u / 1.25) ** 2, 0.0, None)
        crease_y = 0.11 + height_open * ext_almond * (1.0 + 0.25 * gy) + slant * ext_almond
        crease = np.exp(-(((yl - crease_y) / 0.016) ** 2)) * np.sqrt(ext_almond)
        skin_l = skin_l + 0.45 * crease * vignette
        skin_c = self._const_color(t_col.skin)

        # Esclera (fica avermelhada nas bordas quando irritada)
        lid_shadow = np.clip((top_lid - yl) / 0.12, 0.0, 1.0)
        sclera_l = 0.95 * (0.45 + 0.55 * (lid_shadow ** 0.7)) * (1.0 - 0.35 * (u ** 2))
        edge_tint = mix_colors(t_col.sclera_edge, COLOR_BLOODSHOT, np.float32(s.irritation))
        vein_factor = np.clip((np.abs(u) - (0.78 - 0.35 * s.irritation)) * 4.5, 0.0, 1.0)
        sclera_c = mix_colors((235, 232, 228), edge_tint, vein_factor)

        # Íris e Pupila
        icx, icy = gx * 0.25, gy * 0.15
        dx, dy = xl - icx, yl - icy
        r = np.hypot(dx, dy)
        ang = np.arctan2(dy, dx)
        r_iris = 0.34
        prox = math.exp(-(math.hypot(float(s.mouse_world[0]) - ox, float(s.mouse_world[1])) ** 2) / 0.4)
        r_pupil = (0.13 + 0.014 * math.sin(s.t * 1.7)) * (0.85 + 0.45 * prox) * s.pupil_scale

        rn = r / r_iris
        fibers = 0.5 + 0.5 * np.sin(ang * 34.0 + 3.0 * np.sin(ang * 5.0 + rn * 6.0))
        iris_c = mix_colors(t_col.iris_inner, t_col.iris_outer, np.clip(rn, 0.0, 1.0) ** 0.8)
        iris_l = (0.55 + 0.45 * fibers) * (0.85 + 0.35 * np.exp(-(((rn - 0.45) / 0.08) ** 2)))
        iris_l = iris_l * (1.0 - 0.75 * smoothstep(0.82, 1.0, rn))
        iris_l = np.clip(iris_l * (0.55 + 0.45 * (lid_shadow ** 0.7)) * 0.85, 0.0, 1.0)
        iris_l = np.where(r < r_pupil, 0.0, iris_l)

        in_iris = rn < 1.0
        lum = np.where(in_iris, iris_l, sclera_l)
        col = np.where(in_iris[..., None], iris_c, sclera_c)

        # Reflexo especular e linha dos cílios
        spec = np.exp(-(((xl - (icx - 0.10)) ** 2 + (yl - (icy + 0.10)) ** 2) / 0.0020))
        lum = np.maximum(lum, spec)
        col = np.where((spec > 0.35)[..., None], self._const_color(COLOR_WHITE), col)
        lashes = (np.abs(yl - top_lid) < 0.02) | (np.abs(yl - bot_lid) < 0.012)
        lum = np.where(lashes, lum * 0.35, lum)

        return (
            np.where(inside, lum, skin_l).astype(np.float32),
            np.where(inside[..., None], col, skin_c).astype(np.float32),
            inside,
        )

    def _layer_eye(
        self, xw: NDArray[np.float32], yw: NDArray[np.float32]
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]:
        combined = None
        for idx, (ox, scale) in enumerate(self.state.eye_transforms()):
            lum, col, inside = self._render_single_eye(xw, yw, idx, ox, scale, *self.state.gaze[idx])
            if combined is None:
                combined = (lum, col, inside)
            else:
                l0, c0, d0 = combined
                combined = (
                    np.where(d0, l0, np.where(inside, lum, np.maximum(l0, lum))),
                    np.where(d0[..., None], c0, np.where(inside[..., None], col, c0)),
                    d0 | inside,
                )
        assert combined is not None
        return combined[0], combined[1], self.no_glyph

    def _layer_heart(
        self, xw: NDArray[np.float32], yw: NDArray[np.float32]
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]:
        s = self.state
        t_col = s.theme
        b = s.heart_phase % 1.0
        pulse = 1.0 + 0.07 * math.exp(-8.0 * b) + 0.04 * math.exp(-8.0 * ((b - 0.25) % 1.0))
        scale = 0.55 * pulse
        cx, cy = s.mouse_world * 0.15
        hx = (xw - cx) / scale
        hy = (yw - cy) / scale + 0.12
        implicit = (hx ** 2 + hy ** 2 - 1.0) ** 3 - (hx ** 2) * (hy ** 3)
        depth = np.clip(-implicit, 0.0, 1.0) ** 0.45
        spec = 0.35 * np.exp(-(((hx + 0.45) ** 2 + (hy - 0.55) ** 2) / 0.05))
        lum = np.where(implicit < 0.0, np.clip(0.30 + 0.70 * depth + spec, 0.0, 1.0), 0.0)
        col = mix_colors(t_col.accent_primary, t_col.accent_secondary, np.clip((depth - 0.4) / 0.6, 0.0, 1.0))
        return lum.astype(np.float32), col, self.no_glyph

    def _layer_galaxy(
        self, xw: NDArray[np.float32], yw: NDArray[np.float32]
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]:
        s = self.state
        t_col = s.theme
        cx, cy = s.mouse_world * 0.30
        x, y = xw - cx, (yw - cy) * 1.35
        r = np.hypot(x, y) + 1e-4
        theta = np.arctan2(y, x)
        phase = 2.0 * (theta + 3.0 * np.log(r + 0.05)) - s.galaxy_phase
        arms = (0.5 + 0.5 * np.cos(phase)) ** 2.5
        density = 1.7 * np.exp(-((r / 0.85) ** 2)) * (0.12 + 0.88 * arms) + 1.4 * np.exp(-((r / 0.10) ** 2))
        twinkle = 0.75 + 0.25 * np.sin(s.t * 3.0 + self.noise_grid * 40.0)
        lum = np.clip(density * twinkle, 0.0, 1.0)
        lum = np.where(lum < 0.08, 0.0, lum)
        col = mix_colors(t_col.accent_secondary, t_col.accent_primary, smoothstep(0.05, 0.7, r))
        core = np.exp(-((r / 0.12) ** 2))[..., None]
        col = col * (1.0 - core) + np.array([255.0, 240.0, 210.0], dtype=np.float32) * core
        return lum.astype(np.float32), col.astype(np.float32), self.no_glyph

    def _layer_code_rain(
        self, xw: NDArray[np.float32], yw: NDArray[np.float32]
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]:
        s = self.state
        t_col = s.theme
        head = (s.t * self.rain_vel + self.rain_off) % (self.rows + self.rain_tail + 12.0)
        dist = head[None, :] - self.row_idx
        tail = np.clip(1.0 - dist / self.rain_tail[None, :], 0.0, 1.0)
        lum = np.where(dist >= 0.0, tail ** 1.5, 0.0)

        # Lanterna interativa usando as coordenadas distorcidas (xw, yw)
        dx = xw - s.mouse_world[0]
        dy = yw - s.mouse_world[1]
        flashlight = np.exp(-(dx ** 2 + dy ** 2) / (2.0 * 0.22 ** 2))
        flicker = 0.5 + 0.5 * np.sin(s.t * 9.0 + self.noise_grid * 30.0)
        lum = np.clip(lum * (1.0 + 1.8 * flashlight), 0.0, 1.0)
        lum = np.maximum(lum, 0.45 * flashlight * flicker).astype(np.float32)

        is_tip = ((dist >= 0.0) & (dist < 1.5))[..., None]
        col = np.where(is_tip, self._const_color(COLOR_WHITE), self._const_color(t_col.code_rain))
        step = np.floor(s.t * 8.0 + self.col_idx * 0.37).astype(np.int64)
        ng = len(self.cfg.glyph_charset)
        glyphs = ((self.col_idx * 7919 + self.row_idx * 104729 + step * 31) % ng).astype(np.int32)
        return lum, col, np.where(lum > 0.04, glyphs, -1)

    def _layer_vortex(
        self, xw: NDArray[np.float32], yw: NDArray[np.float32]
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]:
        """Camada 6: Túnel de plasma hipnótico interativo."""
        s = self.state
        t_col = s.theme
        dx = xw - s.mouse_world[0] * 0.45
        dy = yw - s.mouse_world[1] * 0.45
        r = np.hypot(dx, dy) + 1e-4
        ang = np.arctan2(dy, dx)

        rings = np.sin(2.2 / (r + 0.08) - s.vortex_phase * 2.5 + np.sin(ang * 4.0 + s.t))
        spokes = np.cos(ang * 6.0 + r * 8.0 - s.vortex_phase * 1.5)
        plasma = (0.5 + 0.5 * rings) * (0.5 + 0.5 * spokes)
        horizon = smoothstep(0.03, 0.16, r) * np.exp(-r * 0.65)
        lum = np.clip(plasma * horizon * 1.65, 0.0, 1.0).astype(np.float32)

        mix_factor = 0.5 + 0.5 * np.sin(r * 6.0 - s.vortex_phase + ang * 2.0)
        col = mix_colors(t_col.accent_primary, t_col.accent_secondary, mix_factor)
        photon_ring = np.exp(-(((r - 0.12) / 0.025) ** 2))[..., None]
        col = np.clip(col + np.array(COLOR_WHITE, dtype=np.float32) * photon_ring * 0.75, 0.0, 255.0)
        return lum, col.astype(np.float32), self.no_glyph

    def _layer_text(
        self, xw: NDArray[np.float32], yw: NDArray[np.float32]
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]:
        s = self.state
        t_col = s.theme
        wave = 0.85 + 0.15 * np.sin(s.t * 2.5 + xw * 5.0 + yw * 3.0)
        lum = (self.text_mask * wave).astype(np.float32)
        col = mix_colors(t_col.accent_primary, t_col.accent_secondary, 0.5 + 0.5 * np.sin(xw * 3.0 + s.t * 1.5))
        return lum, col, self.no_glyph

    def _layer_stars_vectorized(self) -> Tuple[NDArray[np.float32], NDArray[np.float32]]:
        """Renderiza o campo estelar cintilante de forma 100% vetorizada em NumPy."""
        s = self.state
        t_col = s.theme
        lum = np.zeros((self.rows, self.cols), dtype=np.float32)
        col = np.full((self.rows, self.cols, 3), 255.0, dtype=np.float32)

        b = 0.5 + 0.5 * np.sin(s.t * self.star_speed + self.star_phase)
        star_colors = np.where(
            self.star_alt_col[:, None],
            np.asarray(t_col.accent_secondary, dtype=np.float32),
            np.asarray(COLOR_STAR_BLUE, dtype=np.float32),
        )

        # Pontos centrais das estrelas
        lum[self.star_r, self.star_c] = b
        col[self.star_r, self.star_c] = star_colors

        # Brilho em cruz para estrelas maiores
        big_mask = self.star_big & (b > 0.3)
        if np.any(big_mask):
            br = self.star_r[big_mask]
            bc = self.star_c[big_mask]
            bb = b[big_mask]
            bcol = star_colors[big_mask]
            offsets = ((0, 1, 0.55), (0, -1, 0.55), (1, 0, 0.55), (-1, 0, 0.55), (0, 2, 0.3), (0, -2, 0.3))
            for dr, dc, k in offsets:
                rr = np.clip(br + dr, 0, self.rows - 1)
                cc = np.clip(bc + dc, 0, self.cols - 1)
                val = bb * k
                better = val > lum[rr, cc]
                lum[rr[better], cc[better]] = val[better]
                col[rr[better], cc[better]] = bcol[better]

        return lum, col

    # ------------------------------------------------------------------------
    # COMPOSIÇÃO E RENDERIZAÇÃO FINAL
    # ------------------------------------------------------------------------

    def compose_scene(self) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.int32]]:
        """Combina modo ativo, transição, estrelas, partículas e ondas de choque."""
        s = self.state
        xw, yw = self._compute_warped_coords()

        la, ca, ga = self.layer_dispatch[s.current_mode](xw, yw)
        layers = [(la, ca, ga)]
        star_vis = STAR_VISIBILITY[s.current_mode]

        if s.target_mode is not None:
            prog = s.transition_smooth
            lb, cb, gb = self.layer_dispatch[s.target_mode](xw, yw)
            la = la * np.clip((self.noise_grid - (prog * 1.15 - 0.05)) * 6.0, 0.0, 1.0)
            h = np.clip((prog - 0.35) / 0.65, 0.0, 1.0)
            lb = lb * np.clip((h * 1.3 - self.noise_grid) * 5.0, 0.0, 1.0)
            layers = [(la, ca, ga), (lb, cb, gb)]
            star_vis = (
                star_vis * (1.0 - prog)
                + STAR_VISIBILITY[s.target_mode] * prog
                + 0.55 * math.sin(math.pi * prog)
            )

        le, ce = self._layer_stars_vectorized()
        layers.append((le * float(np.clip(star_vis, 0.0, 1.0)), ce, self.no_glyph))

        l_stack = np.stack([item[0] for item in layers])
        c_stack = np.stack([item[1] for item in layers])
        g_stack = np.stack([item[2] for item in layers])

        winner = l_stack.argmax(axis=0)
        lum = np.take_along_axis(l_stack, winner[None], axis=0)[0]
        col = np.take_along_axis(c_stack, winner[None, ..., None], axis=0)[0]
        glyph = np.take_along_axis(g_stack, winner[None], axis=0)[0]

        # Camada superior de efeitos (partículas e cristas de ondas de choque)
        l_fx = np.zeros((self.rows, self.cols), dtype=np.float32)
        c_fx = np.full((self.rows, self.cols, 3), 255.0, dtype=np.float32)
        self.particles.render_onto(l_fx, c_fx, self.cols, self.rows)

        Xz, Yz = self.base_x / s.zoom, self.base_y / s.zoom
        for w in s.shockwaves:
            dtw = s.t - w.t0
            ring = (
                np.exp(-(((np.hypot(Xz - w.x, Yz - w.y) - 1.2 * dtw) / 0.04) ** 2))
                * math.exp(-1.1 * dtw)
            ).astype(np.float32)
            better = ring > l_fx
            l_fx = np.where(better, ring, l_fx)
            c_fx = np.where(better[..., None], self._const_color(s.theme.accent_secondary), c_fx)

        use_fx = l_fx > lum
        return (
            np.where(use_fx, l_fx, lum),
            np.where(use_fx[..., None], c_fx, col),
            np.where(use_fx, -1, glyph),
        )

    def blit_ascii(
        self, lum: NDArray[np.float32], col: NDArray[np.float32], glyph: NDArray[np.int32]
    ) -> None:
        """Transforma as matrizes da grade em pixels na tela via indexação vetorizada do Atlas."""
        ramp_len = len(self.current_ramp_str)
        idx = (np.clip(lum, 0.0, 1.0) ** 0.85 * (ramp_len - 1) + 0.5).astype(np.int32)
        use_glyph = glyph >= 0
        idx = np.where(use_glyph, ramp_len + glyph, idx)

        mask = self.atlas[idx]  # (ROWS, COLS, CW, CH)
        mask = mask.transpose(1, 2, 0, 3).reshape(self.cols * self.cw, self.rows * self.ch)

        tone = col / (col.max(axis=2, keepdims=True) + 1e-6) * 255.0
        tone = tone * np.where(use_glyph, np.clip(lum, 0.0, 1.0) ** 0.8, 1.0)[..., None]
        tone = np.repeat(np.repeat(tone.transpose(1, 0, 2), self.cw, axis=0), self.ch, axis=1)

        pygame.surfarray.blit_array(self.screen, (mask[..., None] * tone).astype(np.uint8))

    def draw_hud(self, fps: float) -> None:
        """Renderiza o painel de ajuda, barra de digitação e notificações Toast."""
        s = self.state
        hud_visible = s.show_hud if s.show_hud is not None else (s.t < 14.0)

        lines: List[str] = []
        if s.is_typing:
            lines = [f"Digite o texto: {s.input_buffer}_    [Enter confirma | Esc cancela]"]
        elif hud_visible:
            lines = [
                "ESPAÇO / ← → : Modo    1-6 : Direto    Scroll : Zoom    G / Meio : Gravidade",
                "C : Tema    R : Rampa ASCII    E : Expressão    D : 1/2 Olhos    T : Texto",
                "P : Rastro  S : Foto (PNG)     H : Ocultar HUD  Clique no olho : Irritar",
                (
                    f"Modo: {s.current_mode.upper()} | Tema: {s.theme.name} | "
                    f"Rampa: {s.ramp_name} | Expr: {s.expression} | "
                    f"Zoom: {s.zoom:.2f}x | {fps:.0f} FPS"
                ),
            ]

        if lines:
            pad_w = max(self.font.size(line)[0] for line in lines) + 24
            box_h = len(lines) * self.ch + 14
            box = pygame.Surface((pad_w, box_h), pygame.SRCALPHA)
            box.fill((8, 8, 12, 185))
            pygame.draw.rect(box, (*s.theme.accent_primary, 140), box.get_rect(), 1)
            for i, line in enumerate(lines):
                color = s.theme.accent_secondary if i == len(lines) - 1 and not s.is_typing else (225, 225, 230)
                box.blit(self.font.render(line, True, color), (12, 7 + i * self.ch))
            y_pos = 10 if not s.is_typing else self.height - box_h - 10
            self.screen.blit(box, (10, y_pos))

        # Notificação Toast no canto superior direito
        if s.toast_timer > 0.0 and s.toast_message:
            alpha = int(min(1.0, s.toast_timer * 2.0) * 230)
            tw, th = self.font.size(s.toast_message)
            toast_surf = pygame.Surface((tw + 24, th + 12), pygame.SRCALPHA)
            toast_surf.fill((15, 15, 20, int(alpha * 0.85)))
            pygame.draw.rect(toast_surf, (*s.theme.accent_secondary, alpha), toast_surf.get_rect(), 1)
            txt_surf = self.font.render(s.toast_message, True, COLOR_WHITE)
            txt_surf.set_alpha(alpha)
            toast_surf.blit(txt_surf, (12, 6))
            self.screen.blit(toast_surf, (self.width - toast_surf.get_width() - 12, 10))

    # ------------------------------------------------------------------------
    # LOOP DE EXECUÇÃO
    # ------------------------------------------------------------------------

    def run(self) -> None:
        """Inicia o loop principal de eventos e renderização a 60 FPS."""
        clock = pygame.time.Clock()
        while True:
            dt = min(clock.tick(self.cfg.fps) / 1000.0, 0.05)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif ev.type == pygame.KEYDOWN:
                    if self.handle_keydown(ev):
                        pygame.quit()
                        sys.exit()
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button in (1, 2):
                        self.handle_mouse_click(ev.pos, ev.button)
                elif ev.type == pygame.MOUSEWHEEL:
                    self.state.target_zoom = float(
                        np.clip(self.state.target_zoom * (1.12 ** ev.y), 0.55, 2.50)
                    )
                    self.state.notify(f"Zoom: {self.state.target_zoom:.2f}x", duration=1.2)

            self.update(dt)
            lum, col, glyph = self.compose_scene()
            self.blit_ascii(lum, col, glyph)

            if self.state.screenshot_pending:
                self.state.screenshot_count += 1
                stamp = datetime.now().strftime("%H%M%S")
                filename = f"ascii_eye_{stamp}_{self.state.screenshot_count:02d}.png"
                pygame.image.save(self.screen, filename)
                self.state.screenshot_pending = False
                self.state.notify(f"Salvo: {filename}")

            self.draw_hud(clock.get_fps())
            pygame.display.flip()


if __name__ == "__main__":
    engine = AsciiShaderEngine()
    engine.run()