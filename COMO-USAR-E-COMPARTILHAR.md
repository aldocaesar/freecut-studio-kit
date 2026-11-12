# FreeCut Universal Studio Kit (v7.2 Final) — Instalação, Pixabay Grátis & Uso Só com Áudio

Este pacote transforma **qualquer IA Frontier** (**OpenBot**, **Claude Code**, **Gemini / Antigravity** ou **Codex / Cursor**) em um **Editor de Vídeo Sênior e Diretor de Arte autônomo** para o [FreeCut (`walterlow/freecut`)](https://github.com/walterlow/freecut), **100% autônomo**, com **memória contínua de contexto** e **ZERO API paga obrigatória**.

---

## 0. API Gratuita Recomendada para Vídeos & Fotos de Stock: Pixabay (`PIXABAY_API_KEY`)
Como o Pexels pausou a emissão de novas chaves de API, o motor `v7.2` usa o **Pixabay** como provedor gratuito principal de vídeos 1080p e fotos Full HD de stock:
1. Crie uma conta gratuita em 30 segundos e copie sua chave em `https://pixabay.com/api/docs/`.
2. Na **1ª execução**, o bot pergunta uma única vez se você quer informar sua `PIXABAY_API_KEY` (ou rodar 100% sem nenhuma chave usando scraping multi-motor).
3. Se você também já tiver uma `PEXELS_API_KEY` antiga, ela continua funcionando normalmente como complementar.

---

## 1. Como Funciona o 1º Uso + Memória de Contexto + Só Áudio
1. **1º Uso Inteligente (`.freecut-setup-done.json`):** No primeiro contato em um PC novo, o bot/skill verifica e instala automaticamente Python, FFmpeg, `faster-whisper`, `rembg`, Playwright Chromium e o atlas offline de 242 países, pergunta **uma única vez** sobre chaves opcionais (`PIXABAY_API_KEY`, `GROQ_API_KEY`, `ELEVENLABS_API_KEY`) e grava `.freecut-setup-done.json` para nunca mais interromper nos próximos vídeos.
2. **Memória Contínua do Canal (`.freecut-creator-memory.json` + Memória do OpenBot):** A cada vídeo concluído e a cada ajuste que você pedir (*"sempre 9:16"*, *"prefiro fundos claros"*, *"ritmo mais rápido"*), `creator_memory.py` salva essas regras localmente e registra as paletas/abertura usadas para que os próximos vídeos mantenham o DNA do seu canal sem repetir a mesma abertura.
3. **Vídeo Perfeito Só com o Áudio:** A partir do setup feito, basta soltar apenas o `.mp3` / `.wav` / `.m4a` no chat. Sem questionários: ele transcreve palavra por palavra, consulta a memória do canal, busca fotos reais para nomes/marcas citados (`specific: true`) e vídeos HD no Pixabay para cenas de atmosfera (`specific: false`), confere tudo visualmente em subagente isolado e entrega a `freecut_workspace` com `100%` dos caches prontos.

---

## 2. Como Abrir em ~1–2s no Google Chrome (Sem Delay!)
Ao terminar, o bot entrega o link clicável da pasta **`freecut_workspace`** já pré-cacheada (`thumbnail.jpg`, `filmstrip` 1fps e ondas `WFORM` binárias):
- No FreeCut aberto no Chrome, clique em **Workspace → Change / Select Workspace Folder** e selecione diretamente a pasta `freecut_workspace` (evite *Import Project `.freecut.zip`* localmente, pois o ZIP precisa descompactar centenas de MB na memória do navegador).
