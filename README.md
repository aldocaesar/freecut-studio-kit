# FreeCut Universal Studio Kit (v8.0 — Camaleão & Motion 100% Criativo via LLM)

Transforma **qualquer IA multimodal (OpenBot, Claude Code, Gemini / Antigravity ou Codex / Cursor)** em um **Editor de Vídeo Sênior e Diretor de Arte Camaleão autônomo** para o [FreeCut (`walterlow/freecut` v15 / Workspace v2)](https://github.com/walterlow/freecut), cobrindo `16:9`, `9:16`, `4:5` e `1:1` e vídeos curtos ou longos (**10 a 20+ minutos sem estourar janela de contexto**), **100% gratuito e capaz de criar vídeos completos recebendo apenas o áudio**.

---

## Destaques da Versão `v8.0`
- **Motion Graphics 100% Criativos e Inéditos por Cena (`doc-motion-scenes` v8.0):** Zero templates prontos e zero paletas engessadas! Removemos todos os slides pré-fabricados do `motion-kit.js` — agora ele fornece apenas primitivas determinísticas de física/mola, easing, curvas SVG (`strokeProgress`, `pointOnPath`), câmera rostrum e cartografia Natural Earth offline de **242 países** (`world-atlas.js`), enquanto o LLM inventa do zero cada `motion/SXX.html` (SVG ilustrado, Canvas2D procedural, UI 3D sob medida, tipografia cinética ou mapa geodésico) a partir da metáfora exata narrada. O `validate_freecut.py` bloqueia widgets antigos e reprova clones estruturais entre cenas.
- **Direção de Arte Camaleão por Vídeo (`style_dna`) + Memória Anti-Clone (`creator_memory.py`):** Cada projeto nasce com paleta (`accent`, `accent_secondary`, `paper_bg`, `studio_bg`), combinação de Google Fonts (`font_display`, `font_serif`, `font_body`, `font_mono`), fundos de recorte e overlays vetoriais desenhados especificamente para o humor do áudio (Comédia/Pop, Documentário Investigativo, Tech/Finanças, História, Lifestyle), sem travar cor repetida entre vídeos e respeitando ~35%–45% de cenas limpas (`silent_visual: true`).
- **API Gratuita do Pixabay em 1º Plano (`PIXABAY_API_KEY`) + Modo 100% Sem Chaves:** Como o Pexels pausou novas chaves de API, o `fetch_media.py` usa nativamente a API gratuita do **Pixabay** (`https://pixabay.com/api/docs/` — liberada na hora para **vídeos 1080p MP4 e fotos Full HD**), com destilação automática de 2–3 tags principais e download de múltiplos ângulos (`_b2.mp4` / `_b3.mp4`). Basta colar a chave no chat no 1º uso (salva direto no Cofre do OpenBot ou `.env` local) ou rodar **100% sem chaves** via scraping multi-motor + `faster-whisper` local.
- **Abertura Instantânea (~1–2s) no Google Chrome (Workspace v2 Pre-Cache):** `assemble_freecut.py` já entrega `thumbnail.jpg`, `cache/filmstrip/` (`1fps` completo) e `cache/waveform/multi-res.bin` (`WFORM` v1 em 4 níveis), com `didNormalizationChange === false` no FreeCut atual.

---

## Como Usar (No OpenBot ou via GitHub)

### 1. Pelo Link Compartilhável do OpenBot
1. Instale o **`Editor-FreeCut`** pelo link do OpenBot (`doc-art-director`, `freecut-unified-engine`, `doc-motion-scenes`, `doc-lottie-overlays` já vêm instaladas com zero chaves expostas).
2. Se quiser vídeos/fotos HD via Pixabay, cole sua `PIXABAY_API_KEY` gratuita na 1ª mensagem (ele guarda no Cofre do OpenBot na hora e nunca mais pergunta); ou solte direto seu áudio (`.mp3`/`.wav`/`.m4a`) para editar 100% sem chaves.
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

## Arquitetura dos 4 Módulos (`v8.0`)

| Módulo / Skill | Responsabilidade | Custo / Chave |
|---|---|---|
| **`freecut-unified-engine`** | Onboarding de 1º uso, memória anti-clone (`creator_memory.py`), `words_compact.txt`, caça paralela Pixabay HD + multi-motor (`_b2.mp4`), `style_dna` camaleão, pré-cache Workspace v2 e `validate_freecut.py` | **100% Grátis** (`PIXABAY_API_KEY` grátis recomendada) |
| **`doc-art-director`** | Direção criativa camaleão só com áudio adaptada ao gênero, ~35%–45% de respiro visual, recortes opcionais sem texto forçado e 6 zonas tipográficas | **100% Grátis** |
| **`doc-motion-scenes`** | Motions 30fps **100% autorais via LLM** em HTML/CSS/SVG/Canvas2D + física/mola determinística (`motion-kit.js`) + cartografia offline de **242 países** (`world-atlas.js`) + `motion_contact_sheet.jpg` (`20%/50%/78%/94%`) | **100% Grátis** |
| **`doc-lottie-overlays`** | Geração em lote (`< 0.2s`) de acentos vetoriais Bodymovin/Lottie (`spark_burst`, `handdrawn_underline`, `minimal_lower_third`, etc., `<15 KB`) sincronizados ao `style_dna` + SFX foley | **100% Grátis** |
