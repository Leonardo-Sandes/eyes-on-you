# 👁️ eyes-on-you

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-CE-008000?style=for-the-badge&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-Vectorized-013243?style=for-the-badge&logo=numpy&logoColor=white)
![FPS](https://img.shields.io/badge/Meta-60_FPS-FF4500?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-F7DF1E?style=for-the-badge)

> **Um motor de shaders ASCII procedural e interativo em tempo real.**  
> Transforma campos escalares matemáticos, física de partículas e distorções espaciais em arte de caracteres com **Pygame CE** e **renderização vetorizada com NumPy**, com meta de **60 FPS**. O desempenho depende do computador e da resolução da janela.

```text
          . : - = + * # % @ % # * + = - : .          
    . : = * # @ % # * + = - = + * # % @ # * = : .    
  : = # @ % : .       . - + * - .       . : % @ # = :
. + @ * .           : # @ % % @ # :           . * @ +
- # % .           = @ % .     . % @ =           . % #
= @ *           . # @ :         : @ # .           * @
+ @ *           . # @ :         : @ # .           * @
- # % .           = @ % .     . % @ =           . % #
. + @ * .           : # @ % % @ # :           . * @ +
  : = # @ % : .       . - + * - .       . : % @ # = :
    . : = * # @ % # * + = - = + * # % @ # * = : .    
          . : - = + * # % @ % # * + = - : .          
```

---

## ✨ Sobre o Projeto

**eyes-on-you** não é uma animação pré-renderizada nem um conversor de vídeo para texto. É um **motor gráfico procedural** onde cada célula da tela funciona como um fragmento de shader avaliado em tempo real.

A atração principal é uma entidade ocular orgânica que observa o cursor do usuário, reage a estímulos físicos, demonstra expressões emocionais, sente sono quando ignorada, fica tonta se o cursor girar rapidamente e se irrita quando é "cutucada" diretamente. Além do olho, o motor conta com **6 cenas matemáticas interativas** que se fundem através de dissolução baseada em matrizes de ruído.

---

## 🚀 Funcionalidades Principais

### 👁️ Anatomia e Comportamento Orgânico
* **Rastreamento Ocular Suavizado:** O olhar acompanha a posição e a velocidade do cursor com interpolação exponencial amortecida.
* **Fisiologia da Pupila:** Dilatação e contração dinâmicas baseadas na distância do cursor, estado de foco, susto ou irritação.
* **Irritação Ocular (Cutucar o Olho):** Clicar diretamente sobre o globo ocular deixa a esclera avermelhada, contrai a pupila e acelera o reflexo de piscada.
* **Tontura Cinemática:** Movimentos circulares rápidos com o mouse ao redor da tela desestabilizam o olhar, fazendo as pupilas girarem em órbitas descompassadas.
* **Ciclo de Sono e Despertar:** Se o mouse ficar imóvel por alguns segundos, as pálpebras pesam até o olho adormecer. Mover o mouse novamente causa um despertar assustado.
* **Expressões Faciais (`E`):** Alteração geométrica da curvatura palpebral entre os estados **Neutro**, **Raiva**, **Cético** (uma sobrancelha arqueada) e **Melancólico**.
* **Modo Ciclope ou Binocular (`D`):** Alternância instantânea entre um olho centralizado ou um par de olhos independentes.

### 🌌 6 Modos Visuais Procedurais
1. **Olho (`1`):** Globo ocular completo com fibras radiais da íris, sombreamento da pálpebra superior, dobra cutânea, esclera e reflexo especular.
2. **Coração (`2`):** Superfície algébrica implícita com batimento cardíaco duplo (sístole/diástole) que acelera a cada clique.
3. **Galáxia (`3`):** Espiral logarítmica com núcleo incandescente e estrelas cintilantes cujo centro gravitacional acompanha o mouse.
4. **Chuva de Código (`4`):** Cascata de glifos inspirada em *Matrix*, onde o cursor atua como uma lanterna radial que ilumina e revela caracteres ocultos na escuridão.
5. **Vórtice (`5`):** Túnel de plasma interferométrico com anel de fótons que sofre distorção conforme a velocidade do cursor.
6. **Texto Dinâmico (`6` ou `T`):** Renderizador tipográfico em tempo real que converte qualquer palavra digitada pelo usuário em uma malha ASCII ondulante.

### 🌀 Física de Partículas e Distorção do Espaço-Tempo
* **Lente de Onda de Choque:** Clicar na tela não apenas desenha um anel, mas **deforma fisicamente** a malha de coordenadas $(X, Y)$, refratando qualquer cena ativa como uma gota caindo na água.
* **Poço Gravitacional (`G` ou Clique do Meio):** Transforma o cursor em uma singularidade que curva o espaço ao redor (lente gravitacional) e suga todas as partículas da tela em órbitas espirais.
* **Sistema de Partículas Vetorizado:** Até $1200$ partículas simultâneas com gravidade, atrito atmosférico, rastro de cursor e modo chafariz de faíscas.

### 🎨 Customização Visual em Tempo Real
* **6 Temas de Cores (`C`):** *Âmbar*, *Oceano*, *Esmeralda*, *Rubi Carmesim*, *Cyberpunk* e *Monocromático*.
* **5 Rampas de Densidade ASCII (`R`):** *Clássico*, *Blocos (Shader)*, *Binário*, *Minimalista* e *Denso*.
* **Câmera com Zoom Dinâmico (`Scroll`):** Aproximação e afastamento suaves de $0.55\times$ até $2.50\times$.
* **Captura Limpa (`S`):** Salva imagens `.png` na resolução da janela, sem a sobreposição do HUD, na pasta de onde o comando foi executado. No Oculus, os arquivos seguem o padrão `ascii_eye_*.png`; executando pela raiz do projeto, as capturas ficam nessa pasta.

---

## 🎮 Controles e Atalhos

### ⌨️ Teclado

| Tecla | Ação |
| :--- | :--- |
| <kbd>ESPAÇO</kbd> / <kbd>Seta Direita</kbd> / <kbd>Seta Esquerda</kbd> | Alterna entre os modos visuais com transição por dissolução |
| <kbd>1</kbd> a <kbd>6</kbd> | Acesso direto aos modos (*Olho*, *Coração*, *Galáxia*, *Código*, *Vórtice*, *Texto*) |
| <kbd>C</kbd> | Alterna o tema de cores |
| <kbd>R</kbd> | Alterna a paleta/rampa de caracteres ASCII |
| <kbd>E</kbd> | Alterna a expressão facial do olho (*Neutro*, *Raiva*, *Cético*, *Melancólico*) |
| <kbd>D</kbd> | Alterna entre **1 Olho** e **2 Olhos** |
| <kbd>G</kbd> | Liga/Desliga o **Poço Gravitacional** no cursor |
| <kbd>F</kbd> *(segurar)* | Modo Foco (estreita as pálpebras e dilata a pupila) |
| <kbd>T</kbd> | Abre o prompt para digitar um texto customizado (<kbd>Enter</kbd> confirma, <kbd>Esc</kbd> cancela) |
| <kbd>P</kbd> | Liga/Desliga o rastro de partículas do mouse |
| <kbd>S</kbd> | Salva uma captura de tela limpa em formato `.png` |
| <kbd>H</kbd> | Mostra/Oculta o painel de informações (HUD) |
| <kbd>ESC</kbd> | Encerra a aplicação |

### 🖱️ Mouse

| Interação | Efeito |
| :--- | :--- |
| **Mover o cursor** | Guia o olhar, desloca o centro das cenas e emite rastro de partículas |
| **Girar rapidamente** | Deixa o olho tonto temporariamente |
| **Deixar parado (> 6s)** | O olho começa a fechar as pálpebras e dorme |
| **Clique Esquerdo** | Dispara fogos de artifício, onda de choque refrativa e assusta o olho |
| **Clicar dentro do Olho** | Irrita o olho (esclera vermelha, pupila contraída e piscadas rápidas) |
| **Segurar Clique Esquerdo** | Ativa o emissor contínuo (chafariz de faíscas com física) |
| **Clique do Meio** | Liga/Desliga o Poço Gravitacional |
| **Botão Direito** *(segurar)* | Foca o olhar no cursor |
| **Roda do Mouse (Scroll)** | Controla o Zoom In / Zoom Out da câmera |

---

## 🛠️ Instalação e Execução

### Pré-requisitos
* **Python 3.9** ou superior.
* Pip (gerenciador de pacotes do Python).

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Leonardo-Sandes/eyes-on-you.git
   cd eyes-on-you
   ```

2. **Crie e ative um ambiente virtual (recomendado):**
   ```bash
   # Windows (Prompt de Comando)
   python -m venv .venv
   .venv\Scripts\activate

   # Windows (PowerShell): use este comando para ativar
   # .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   python -m pip install -r requirements.txt
   ```

   O arquivo instala **NumPy** e **Pygame CE**. No código, a importação continua sendo `import pygame`. Mantenha apenas `pygame-ce` no ambiente para evitar conflitos com o pacote `pygame`.

4. **Execute a aplicação:**
   ```bash
   python src/oculus.py
   ```

   Execute os comandos acima na raiz do repositório. A aplicação abre uma janela separada; o terminal permanece ocupado enquanto ela estiver rodando. Pressione `Esc` ou feche a janela para sair.

   Para experimentar as versões anteriores, execute uma delas:

   ```bash
   python src/olho_ascii.py
   python src/olho_ascii_v2.py
   ```

   Os controles e recursos detalhados neste README correspondem ao **Oculus**. As versões anteriores têm menos modos e seus próprios atalhos, descritos no início de cada script.

---

## 🧠 Arquitetura e Matemática (Under the Hood)

Com meta de **60 quadros por segundo**, o motor calcula a luminosidade, as cores e os pixels dos caracteres com operações vetorizadas do **NumPy** na CPU, em um pipeline inspirado em *Fragment Shaders*. Ainda existem laços em etapas como composição de olhos, ondas de choque, estrelas e HUD; a taxa de quadros depende do computador e da resolução da janela.

1. **Malha Espacial Normalizada e Distorção:**  
   A tela é dividida em uma grade de células $(R \times C)$. Cada célula possui coordenadas normalizadas $(X, Y) \in [-1, 1]$. Antes de avaliar qualquer cena, ondas de choque e campos gravitacionais aplicam um deslocamento vetorial $(\Delta X, \Delta Y)$ na malha:
   $$\vec{p}_{\text{warped}} = \frac{\vec{p}}{\text{zoom}} + \sum_{i} A_i(t) \sin(k \cdot d_i) \hat{r}_i$$

2. **Avaliação de Campos Escalares e Vetoriais:**  
   Cada camada visual recebe $(X, Y)$ e retorna três matrizes de dimensão $(R \times C)$:
   * **Luminosidade:** $L \in [0.0, 1.0]$
   * **Cor RGB:** $C \in [0, 255]^3$
   * **Índice de Glifo Forçado:** $G \in \mathbb{Z}$ (usado na chuva de código)

   *Exemplo — Superfície Implícita do Coração:*
   $$f(x, y) = (x^2 + y^2 - 1)^3 - x^2 y^3 < 0$$

   *Exemplo — Braços da Galáxia Espiral Logarítmica:*
   $$\phi(r, \theta, t) = 2\left(\theta + 3 \ln(r + 0.05)\right) - \omega t$$

3. **Atlas de Glifos Pré-computado e Blit Vetorizado:**  
   Na inicialização, os caracteres da fonte monoespaçada são renderizados para um tensor 3D de transparência (o atlas de formato $N_{\text{chars}} \times W_{\text{cell}} \times H_{\text{cell}}$). No Oculus, esse atlas é reconstruído ao trocar a rampa de caracteres. A cada quadro, a matriz de luminosidade $L$ indexa diretamente esse tensor, multiplica pela matriz de matiz normalizada e copia os pixels para a superfície do Pygame via `pygame.surfarray.blit_array()`. A janela é atualizada com `pygame.display.flip()`.

---

## 📂 Estrutura do Código

```text
eyes-on-you/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── src/
    ├── olho_ascii.py      # v1: olho e coração
    ├── olho_ascii_v2.py   # v2: cinco modos visuais
    └── oculus.py          # v3: versão principal, com seis modos
```

Cada versão pode ser executada de forma independente. A versão principal, `src/oculus.py`, concentra o motor em um único arquivo (*single-file architecture*), com **Type Hints** e **Dataclasses**:

* `EngineConfig` & `ColorTheme`: Estruturas imutáveis (`@dataclass(frozen=True)`) com parâmetros do motor e paletas de cores.
* `ParticleSystem`: Motor físico vetorizado com suporte a emissores direcionais, gravidade vertical e atratores orbitais.
* `SimulationState`: Gerenciamento centralizado de estados cinemáticos, temporizadores, transições e reações orgânicas.
* `AsciiShaderEngine`: Classe principal responsável pelo atlas tipográfico, distorção de espaço, cálculo das camadas matemáticas, composição de cenas e interface (HUD/Toast).

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais informações.

---

<p align="center">
  Feito com ☕, Matemática e Python.
</p>
