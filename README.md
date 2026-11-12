# FreeCut Universal Studio Kit (v7.2 Final)

Transforma **qualquer IA multimodal (OpenBot, Claude Code, Gemini / Antigravity ou Codex / Cursor)** em um **Editor de Vídeo Sênior e Diretor de Arte autônomo** para o [FreeCut (`walterlow/freecut` v15 / Workspace v2)](https://github.com/walterlow/freecut), cobrindo `16:9`, `9:16`, `4:5` e `1:1` e vídeos curtos ou longos (**10 a 20+ minutos sem estourar janela de contexto**), **100% gratuito e capaz de criar vídeos completos recebendo apenas o áudio**.

---

## Destaques da Versão `v7.2 Final`
- **API Gratuita do Pixabay em 1º Plano (`PIXABAY_API_KEY`) + Modo 100% Sem Chaves:** Como o Pexels pausou novas chaves de API, o `fetch_media.py` traz suporte nativo primário à API gratuita do **Pixabay** (`https://pixabay.com/api/docs/` — liberada na hora para **vídeos 1080p MP4 e fotos Full HD**), com limite automático `<= 95` caracteres, destilação inteligente de 2–3 tags principais (evitando `0 hits` em prompts longos), filtro de duração/orientação e download de ângulos secundários (`_b2.mp4` / `_b3.mp4`). Se preferir não criar nenhuma chave, continua rodando **100% grátis** via scraping multi-motor + `faster-whisper` local (`PEXELS_API_KEY` antiga também segue aceita como opcional).
- **Detecção de 1º Uso + Memória Contínua de Contexto (`creator_memory.py`):**
  - No **1º uso** (`.freecut-setup-done.json` ausente), instala dependências automaticamente e pergunta **uma única vez** se você deseja adicionar sua `PIXABAY_API_KEY` gratuita (ou outras opcionais) ou rodar 100% sem chaves.
  - A cada vídeo ou feedback, grava e consulta `<WORKSPACE>/.freecut-creator-memory.json` (formato padrão `16:9`/`9:16`, nicho, regras de estilo pedidas pelo usuário, entidades recorrentes e paletas/abertura dos últimos vídeos para manter identidade sem repetir abertura!).
- **Vídeo Completo Só com o Áudio (`.mp3` / `.wav` / `.m4a`):** Basta soltar o arquivo de áudio sem roteiro nem briefing — o agente transcreve palavra por palavra (`words_compact.txt`), lê a memória do canal, separa pessoas/marcas reais (`specific: true`, bloqueando stock genérico) de cenas atmosféricas (`specific: false`, via Pixabay HD / scraping), revisa folhas de contato em subagente isolado e entrega o projeto validado.
- **Abertura Instantânea (~1–2s) no Google Chrome (Workspace v2 Pre-Cache):** `assemble_freecut.py` já entrega `thumbnail.jpg` (`320x180` + capa `640x360`), `cache/filmstrip/` (`1fps` completo) e `cache/waveform/multi-res.bin` (`WFORM` v1 em 4 níveis), com `didNormalizationChange === false` no FreeCut atual.
- **10 Motores `MotionKit v7` + 8 Paletas Editoriais + Zero Vício (`validate_freecut.py` Hard Gates):** Zero clipe congelado (`durationInFrames <= sourceDuration`), palavras monumentais completas com auto-fit óptico, 5 tratamentos rotativos de imprensa, 35% de respiro visual limpo, 6 zonas tipográficas e 242 países offline (`world-atlas.js`).

---

## Como Usar (No OpenBot ou via GitHub)

### 1. Pelo Link Compartilhável do OpenBot
1. Instale o **`Editor-FreeCut`** pelo link do OpenBot (`doc-art-director`, `freecut-unified-engine`, `doc-motion-scenes`, `doc-lottie-overlays` já vêm instaladas com zero chaves expostas).
2. Solte apenas o seu áudio (`.mp3`/`.wav`/`.m4a`), pasta, vídeo de câmera ou roteiro. Na 1ª execução em PC virgem, ele baixa este kit automaticamente, instala dependências gratuitas e pergunta uma única vez sobre chaves opcionais (`PIXABAY_API_KEY`).
3. No FreeCut (Chrome), clique no seletor de **Workspace → Change / Select Workspace Folder** e aponte direto para a pasta **`freecut_workspace`** gerada (abre em ~1–2s sem reimportar ZIP!).

### 2. Instalação Manual / Claude Code / Antigravity / Cursor (Windows, macOS e Linux)

#### Windows (PowerShell)
```powershell
git clone https://github.com/aldocaesar/freecut-studio-kit.git
cd freecut-studio-kit
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

#### macOS / Linux (Terminal)
```bash
git clone https://github.com/aldocaesar/freecut-studio-kit.git
cd freecut-studio-kit
chmod +x install.sh
./install.sh --with-freecut-app
```

---

## Arquitetura dos 4 Módulos (`v7.2 Final`)

| Módulo / Skill | Responsabilidade | Custo / Chave |
|---|---|---|
| **`freecut-unified-engine`** | Detecção de 1º uso, memória contínua (`creator_memory.py`), `words_compact.txt`, caça paralela Pixabay HD + multi-motor (`_b2.mp4`), pré-cache Workspace v2 p/ Chrome e `validate_freecut.py` | **100% Grátis** (`PIXABAY_API_KEY` grátis recomendada) |
| **`doc-art-director`** | Direção criativa autônoma só com áudio consultando a memória do canal, ~35% de respiro visual, 5 estilos de imprensa e 6 zonas tipográficas | **100% Grátis** |
| **`doc-motion-scenes`** | 10 motores `MotionKit v7` + 8 paletas editoriais + cartografia Natural Earth offline de **242 países** + render paralelo 30fps com `motion_contact_sheet.jpg` (`20%/50%/78%/94%`) | **100% Grátis** |
| **`doc-lottie-overlays`** | Geração em lote (`< 0.2s`) de overlays vetoriais Bodymovin/Lottie (`<15 KB`, `application/lottie+json`) + SFX foley | **100% Grátis** |
