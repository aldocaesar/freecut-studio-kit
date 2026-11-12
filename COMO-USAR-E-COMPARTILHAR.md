# FreeCut Universal Studio Kit (v8.0) — Como Compartilhar, Pixabay Grátis & PC Virgem

Este pacote transforma **qualquer IA Frontier** (**OpenBot**, **Claude Code**, **Gemini / Antigravity** ou **Codex / Cursor**) em um **Editor de Vídeo Sênior e Diretor de Arte Camaleão autônomo** para o [FreeCut (`walterlow/freecut`)](https://github.com/walterlow/freecut), **100% autônomo**, com **motions criativos inéditos via LLM**, **memória anti-clone** e **ZERO API paga obrigatória**.

---

## 0. Segurança ao Compartilhar o Bot (Zero Chaves / Zero Dados Locais)
- Ao compartilhar o **`Editor-FreeCut`** pelo link do OpenBot, pelo [FreeCut-Doc-Bot-Shareable.zip](https://github.com/aldocaesar/freecut-studio-kit) ou pelo GitHub:
  - **Sua chave de API nunca vai junto:** chaves salvas no Cofre do OpenBot (`PIXABAY_API_KEY`, etc.) ficam criptografadas exclusivamente no servidor OpenBot da sua máquina; nenhum `.env`, projeto local (`projects/`) ou histórico pessoal vai no pacote.
  - No PC da outra pessoa, ela cadastra a própria `PIXABAY_API_KEY` gratuita (`https://pixabay.com/api/docs/`) ou usa o modo 100% sem chaves.

---

## 1. O Que Acontece no PC Novo Quando a Pessoa Manda a Chave da API (ou o 1º Áudio)
1. **Mandou a `PIXABAY_API_KEY` direto no chat (mesmo na 1ª mensagem):**
   - O bot salva a chave na hora no Cofre do OpenBot da pessoa (ou `.env` local fora do OpenBot), sem repetir o segredo no chat.
   - Na mesma hora, se o PC for virgem, ele baixa o kit completo do GitHub (se faltar), instala automaticamente Python 3, FFmpeg, pacotes Python (`faster-whisper`, `rembg`, `opencv`, `playwright`, `yt-dlp`) e o navegador headless Chromium, valida tudo com `doctor.py -> RESULT: [READY]` e grava `.freecut-setup-done.json` apenas após passar no teste.
   - *(No OpenBot da outra pessoa, basta deixar o acesso do agente em **Full access** / aprovar a instalação na primeira vez para que ele possa instalar os programas no PC dela.)*
2. **Memória Contínua Anti-Clone (`.freecut-creator-memory.json`):** A cada vídeo concluído e a cada ajuste pedido (*"sempre 9:16"*, *"sem legenda"*), `creator_memory.py` lembra as preferências do canal e evita repetir paletas, fontes e metáforas de motion do vídeo anterior.
3. **Vídeo Completo Só com o Áudio:** A partir do setup pronto, basta soltar apenas o `.mp3` / `.wav` / `.m4a` no chat — zero questionários!

---

## 2. Como Abrir em ~1–2s no Google Chrome (Sem Delay!)
Ao terminar, aponte o **Workspace → Change / Select Workspace Folder** do FreeCut (Chrome) diretamente para a pasta **`freecut_workspace`** gerada (já pré-cacheada com miniaturas, `filmstrip` 1fps e ondas `WFORM`).
