# FreeCut Universal Studio Bot (v6.3) — Instalação & Compartilhamento por Link

Este pacote transforma **qualquer IA Frontier** (**OpenBot**, **Claude Code**, **Gemini / Antigravity** ou **Codex / Cursor**) em um **Editor de Vídeo Sênior autônomo** para o [FreeCut (`walterlow/freecut`)](https://github.com/walterlow/freecut), **100% autônomo**, **zero DarkPlanner** e com **ZERO API paga obrigatória**.

---

## 0. Como Compartilhar SÓ por Link no OpenBot (Sem Enviar `.zip`)

1. O kit público já está hospedado e ativo em **`https://github.com/aldocaesar/freecut-studio-kit`** e referenciado em `AGENTS.md`, `CLAUDE.md` e `freecut-unified-engine/SKILL.md`.
2. No OpenBot, abra o agente individual **`Editor-FreeCut`** (ou um clone chamado **`Automation-Vid`**, pois links compartilháveis do OpenBot são gerados por **agente**, não por canal) → **Configurações → Compartilhar**.
3. Envie apenas o link `https://openbot.run/agents/...` para qualquer pessoa:
   - O link instala automaticamente no OpenBot dela o perfil, `AGENTS.md` e os 4 `SKILL.md`.
   - No **1º áudio/vídeo** enviado pela pessoa, o próprio bot detecta que `scripts/doctor.py` ainda não existe, baixa o kit do GitHub automaticamente e roda `bootstrap_env.py` (instalando Python, FFmpeg, `faster-whisper`, `rembg`, `world-atlas.js` de 242 países e Chromium sem pedir nenhum `.zip`).

---

## 1. Instalação Manual / Fora do OpenBot (Windows, Mac ou Linux)

### No Windows (PowerShell)
Abra o PowerShell na pasta extraída e rode:
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
*(Se quiser que o instalador também baixe e configure o aplicativo web do FreeCut localmente com atalho `.\start-freecut.ps1`, adicione `-InstallFreeCutApp`:)*
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -InstallFreeCutApp
```

### No macOS ou Linux (Terminal)
```bash
chmod +x install.sh
./install.sh --with-freecut-app
```

**O que o instalador configura sozinho:**
1. Verifica/instala **Python 3**, **FFmpeg**, **Node.js LTS** e **Git** (`winget` no Windows / `brew` ou `apt` no Mac/Linux).
2. Instala toda a stack Python gratuita:
   - `faster-whisper` (transcrição word-by-word 100% grátis e offline na GPU ou CPU)
   - `edge-tts` (narração neural gratuita com timestamps por palavra caso você mande só o texto)
   - `rembg[cpu]` (recorte automático de fundo transparente RGBA para produtos, garrafas e pessoas)
   - `playwright` + navegador `chromium` (renderização de Motion Graphics em 30fps e captura de matérias/jornais reais)
   - `rapidocr-onnxruntime` + `opencv-python-headless` + `yt-dlp` (caça de mídia real sem marca d'água)
3. Sincroniza as 4 skills tanto em `.agents/skills/` (OpenBot / Antigravity / Codex) quanto em `.claude/skills/` (Claude Code).
4. Inclui o atlas cartográfico vetorial **Natural Earth de 242 países (`world-atlas.js`)** 100% offline.
5. Roda `python doctor.py` no final para confirmar `[READY]`.

---

## 2. Como o Usuário Faz o Vídeo Dele? (Fluxo de Áudio & Transcrição)

Você **não precisa de serviços privados nem de chaves pagas** — basta mandar o áudio e o bot resolve tudo:

| O que você entrega para o Bot | O que o Bot faz automaticamente | Custo / Chave necessária |
|---|---|---|
| **1. Só o Áudio pronto** (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.opus` de WhatsApp/celular) | Normaliza formatos de voz automaticamente para WAV 44.1 kHz se necessário, roda `faster-whisper` local palavra por palavra (`words.json` + `subtitles.srt`) e edita o vídeo inteiro sincronizado na fala | **R$ 0 (100% Grátis / Offline)** |
| **2. Áudio + Legenda `.srt` pronta** | Lê os tempos direto do `.srt` (`--from-srt`) em `< 1s` e monta o vídeo | **R$ 0 (Instantâneo)** |
| **3. Vídeo gravado na câmera / celular** (`.mp4`, `.mov` — estilo Talking-Head / Reels) | Extrai o áudio via FFmpeg, transcreve com `faster-whisper`, corta os silêncios mortos (`cut_aroll.py`) com punch-in `1.00x/1.07x`, adiciona recortes/legendas na zona segura | **R$ 0 (100% Grátis)** |
| **4. Apenas o Roteiro escrito** (`.txt` ou no chat) | Gera narração neural + tempos exatos por palavra via `edge-tts` (`generate_voiceover.py`) — ou usa sua `ELEVENLABS_API_KEY` se você colocar no `.env` | **R$ 0 por padrão** |

> **Quer transcrição em nuvem ainda mais rápida em PCs fracos?** Basta preencher opcionalmente `GROQ_API_KEY` (tem plano gratuito) ou `ASSEMBLYAI_API_KEY` no arquivo `.env`. Se estiverem em branco, o bot usa o `faster-whisper` local automaticamente.

---

## 3. Exemplos de Pedidos Prontos (Qualquer Estilo ou Formato)

Abra esta pasta no seu agente (OpenBot, Claude Code, Antigravity/Gemini ou Cursor) e peça:

- **Documentário / YouTube Horizontal (`16:9`)**:
  > *"Edite este áudio `meu_audio.mp3` em 16:9 estilo documentário investigativo para o FreeCut, com mapas geodésicos reais, recortes sem fundo e 20% de motion graphics."*
- **Reels / TikTok / Shorts Vertical (`9:16`)**:
  > *"Edite este áudio `short.mp3` em formato vertical 9:16 com legendas dinâmicas na zona segura, cortes rápidos na palavra e recortes em parallax."*
- **Talking-Head / Câmera ("Yap" `9:16` ou `16:9`)**:
  > *"Edite minha gravação `camera.mp4`: corte as pausas de silêncio, alterne zoom sutil nos cortes e coloque prints/recortes reais quando eu citar cada empresa."*

---

## 4. Entrega Padrão no FreeCut (Sem Renderizar MP4 no PC) & APIs Opcionais
1. **Padrão Automático (Montar no FreeCut + Enviar URL da Pasta):**
   Por padrão, o bot **NÃO renderiza `.mp4` direto no seu PC**. Assim que termina a montagem e valida com `validate_freecut.py` (`PASS`), ele envia na hora o caminho e o link clicável (`file:///...`) da pasta **`freecut_workspace`** (mais o `.freecut.zip`). Basta abrir o FreeCut (`.\start-freecut.ps1` / `./start-freecut.sh` ou no navegador), clicar em **Open Workspace Folder**, selecionar `freecut_workspace` (todas as faixas `Subtitles`, `Text`, `Lottie`, `Foreground Cutouts`, `GPU Grade`, `Main Visuals`, `Backdrop`, `SFX`, `Narration`, `BGM` vêm 100% editáveis) e clicar em **Export MP4** lá dentro!
2. **Exportação Direta `.mp4` pelo Bot (Apenas Sob Pedido):**
   Se algum dia você quiser que o bot gere um `.mp4` direto no PC sem abrir o navegador, basta pedir explicitamente *"renderize também um MP4 de preview"* (`render_preview.py`).
3. **Chaves de API Opcionais (Na Hora de Instalar ou Depois):**
   - **0 chaves são obrigatórias:** se a pessoa não tiver nenhuma API na hora de instalar, basta pular (100% grátis com `faster-whisper` local + `edge-tts` + busca web real).
   - **Se quiser colocar APIs depois, precisa instalar tudo de novo? Não!** No OpenBot, basta pedir no chat *"quero cadastrar minha chave da Groq/Pexels/ElevenLabs"* (abre o cofre seguro na hora). No terminal, basta rodar `python .agents/skills/freecut-unified-engine/scripts/bootstrap_env.py --setup-keys` (ou editar o `.env`).
