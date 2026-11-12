# FreeCut Universal Studio Kit (v7.0 Final)

Transforma **qualquer IA multimodal (OpenBot, Claude Code, Gemini / Antigravity ou Codex / Cursor)** em um **Editor de Vídeo Sênior e Diretor de Arte autônomo** para o [FreeCut (`walterlow/freecut` v15)](https://github.com/walterlow/freecut), atendendo qualquer formato (`16:9`, `9:16`, `4:5`, `1:1`) e vídeos curtos ou longos (**10 a 20+ minutos sem estourar janela de contexto**), **100% gratuito e sem chaves pagas obrigatórias**.

---

## Novidades da Versão Definitiva (`v7.0 Final`)
- **Zero Vídeo Congelado + Sub-Beats Compostos (`<= 5.8s–6.2s` por corte):** `fetch_media.py` prioriza clipes longos e baixa automaticamente ângulos secundários (`_b2.mp4` / `_b3.mp4`); `assemble_freecut.py` **jamais** emite `durationInFrames > sourceDuration` e subdivide cenas longas em 2–3 sub-planos dinâmicos.
- **10 Motores Declarativos `MotionKit v7.0` + 8 Paletas Editoriais + Detector de Cauda Viva (`94%`):** Atlas geodésico 2D, Globo 3D ortográfico, Jornada Espacial 2.5D (estilo Vox), Curva com câmera `followTip`, Odômetro Mecânico com barra de contraste, Feed 3D de Stories/UI ao vivo, Mesa Investigativa de Dossiê com carimbo, Grafo de Fluxo Financeiro com pacotes em trânsito, Split Diagonal *Versus* e Matriz Proporcional de 100 blocos — alternando paletas claras, quentes e escuras com animação viva até o último frame.
- **Design Editorial Desviciado:** Auto-ajuste óptico de palavras monumentais completas (zero palavras cortadas como `"VIRGÍNI"`), recortes PNG alternando esquerda/centro/direita, **5 tratamentos rotativos de imprensa** (máximo de 2 marca-textos amarelos ancorados via RapidOCR a cada 10 min), **35% de respiro visual limpo**, roteamento de texto em **6 zonas negativas** fugindo do rosto/sujeito e mix de cortes secos (`~38%`) com 5 transições cinematográficas.
- **Blindagem Bytecode-Clean (`-B` / `dont_write_bytecode`):** Mantém `.agents/skills` 100% limpo para compartilhamento em 1 clique no botão **Publicar agente** do OpenBot.

---

## Como Funciona no OpenBot ou Fora Dele

### 1. Pelo Link Compartilhável do OpenBot
1. Instale o **`Editor-FreeCut`** pelo link do OpenBot (`doc-art-director`, `freecut-unified-engine`, `doc-motion-scenes`, `doc-lottie-overlays` já vêm instaladas com zero chaves expostas).
2. Envie apenas o áudio, pasta (com áudio e eventual `.srt`), vídeo de câmera ou roteiro. Na 1ª execução em PC virgem, ele baixa este kit automaticamente, configura as dependências gratuitas e pergunta uma única vez se deseja rodar 100% grátis ou conectar chaves opcionais.
3. Abra a pasta **`freecut_workspace`** gerada diretamente em **Open Workspace Folder** no FreeCut!

### 2. Instalação Manual (Windows, macOS e Linux)

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

## Arquitetura dos 4 Módulos (`v7.0 Final`)

| Módulo / Skill | Responsabilidade | Custo / Chave |
|---|---|---|
| **`freecut-unified-engine`** | Auto-setup em PC virgem, `words_compact.txt`, narração neural (`edge-tts`), corte A-roll, caça paralela multi-ângulo (`_b2.mp4`), montagem multi-plano zero-freeze, 5 tratamentos de imprensa, 6 zonas tipográficas e `validate_freecut.py` v7.0 | **100% Grátis** |
| **`doc-art-director`** | Direção criativa autônoma a partir só do áudio ou pasta, ritmo com ~35% de respiro visual, rotação de arquétipos sem repetição e schema enxuto | **100% Grátis** |
| **`doc-motion-scenes`** | 10 motores `MotionKit v7.0` + 8 paletas editoriais + cartografia Natural Earth offline de **242 países** + render paralelo 30fps com `motion_contact_sheet.jpg` de 4 colunas (`20%/50%/78%/94%`) | **100% Grátis** |
| **`doc-lottie-overlays`** | Geração em lote (`< 0.2s`) de overlays vetoriais Bodymovin/Lottie (`<15 KB`: cantoneiras de foco, sublinhado a tinta, setas, círculos e grifo OCR controlado) + SFX foley | **100% Grátis** |
