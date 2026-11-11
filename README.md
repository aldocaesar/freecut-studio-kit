# FreeCut Universal Studio Kit (v6.3)

Transforma **qualquer IA multimodal (OpenBot, Claude Code, Gemini / Antigravity ou Codex / Cursor)** em um **Editor de Vídeo Sênior autônomo** para o [FreeCut (`walterlow/freecut` v15)](https://github.com/walterlow/freecut), atendendo qualquer formato (`16:9`, `9:16`, `4:5`, `1:1`) e estilo (Documentário, Explainer, Talking-Head/A-Roll, Produto/UI, Dados & Mapas), **100% gratuito e sem chaves pagas obrigatórias**.

---

## Como Funciona para Quem Recebe o Link do Bot no OpenBot

1. **Instale o bot pelo link compartilhável do OpenBot (`https://openbot.run/agents/...`)**:
   - O link instala automaticamente o perfil do **`Editor-FreeCut`**, `AGENTS.md` e as 4 skills (`doc-art-director`, `freecut-unified-engine`, `doc-motion-scenes`, `doc-lottie-overlays`).
2. **Envie o seu primeiro áudio, vídeo ou roteiro no chat**:
   - Na **1ª execução**, o bot detecta que os scripts ainda não existem na sua máquina, baixa automaticamente este repositório (`https://github.com/aldocaesar/freecut-studio-kit`) e roda `bootstrap_env.py` (instalando Python, FFmpeg, `faster-whisper`, `rembg`, `edge-tts`, o atlas cartográfico Natural Earth de 242 países e o Chromium headless).
   - Pergunta **uma única vez** se você quer cadastrar chaves opcionais (`GROQ_API_KEY`, `PEXELS_API_KEY`, `ELEVENLABS_API_KEY`) ou **seguir 100% grátis** (você pode pular e adicionar chaves depois a qualquer momento apenas pedindo no chat).
3. **Abra o projeto pronto no FreeCut**:
   - Por padrão, o bot monta e valida o projeto (`validate_freecut.py` = `PASS`) sem travar seu PC renderizando `.mp4` à toa, e entrega imediatamente o caminho e o link clicável (`file:///...`) da pasta **`freecut_workspace`**.
   - Abra o **FreeCut**, clique em **Open Workspace Folder**, selecione a pasta `freecut_workspace` e edite ou exporte o `.mp4` em 1 clique!

---

## Instalação Manual / Fora do OpenBot (Windows, macOS e Linux)

### Windows (PowerShell)
```powershell
git clone https://github.com/aldocaesar/freecut-studio-kit.git
cd freecut-studio-kit
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
*(Adicione `-InstallFreeCutApp` se também quiser baixar e configurar o editor web do FreeCut localmente com atalho `.\start-freecut.ps1`.)*

### macOS / Linux (Terminal)
```bash
git clone https://github.com/aldocaesar/freecut-studio-kit.git
cd freecut-studio-kit
chmod +x install.sh
./install.sh --with-freecut-app
```

---

## O Que Está Incluso no Kit (v6.3)

| Módulo / Skill | O que faz automaticamente | Custo / Chave |
|---|---|---|
| **`freecut-unified-engine`** | Transcrição word-by-word (`faster-whisper` GPU/CPU), narração neural (`edge-tts`), corte de silêncio A-roll (`cut_aroll.py`), caça de mídia exata com filtro OCR + recorte PNG transparente (`rembg` em `fetch_media.py`), montagem nativa v15 (`assemble_freecut.py`) e validador anti-vício (`validate_freecut.py`) | **100% Grátis** |
| **`doc-art-director`** | Decupagem sincronizada na palavra falada (`anchor_word`), zonas seguras (`16:9`, `9:16`, `4:5`, `1:1`), tipografia editorial multi-fonte (`textSpans` em 7 fontes), animações nativas (`textMotion` + `motionModifiers`) e 3 arquétipos de recorte sem repetição | **100% Grátis** |
| **`doc-motion-scenes`** | Cenas de Motion Graphics em 30fps com cartografia geodésica real de **242 países** (`world-atlas.js` Natural Earth offline + MapLibre GL), gráficos monotônicos sem colisão de texto e recortes reais integrados | **100% Grátis** |
| **`doc-lottie-overlays`** | Overlays vetoriais Bodymovin/Lottie (`<15 KB`: grifo marca-texto, setas, lower-thirds, cantoneiras de foco) sincronizados na fala + kit completo de SFX foley | **100% Grátis** |

Consulte também o guia detalhado em [`COMO-USAR-E-COMPARTILHAR.md`](./COMO-USAR-E-COMPARTILHAR.md).
