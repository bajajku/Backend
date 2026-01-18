# 🧠 Spatial Summarizer

> **Transform documents into interactive, accessible 3D learning experiences**

An AI-powered platform that converts educational documents (PDF, PPTX, TXT) into self-contained, interactive 3D HTML visualizations with AI-generated narration. Designed with **cognitive and neuro-accessibility** at its core.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r160+-orange.svg)](https://threejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Project Vision

**Spatial Summarizer** bridges the gap between traditional text-heavy documents and multi-sensory learning experiences. By leveraging AI and 3D visualization, we make educational content more accessible to individuals with:

- 🎨 **ADHD** - Interactive, engaging, self-paced exploration
- 📖 **Dyslexia** - Visual-first approach with audio narration
- 🧩 **Autism** - Predictable structure, clear relationships
- 👁️ **Visual Learning Preferences** - Spatial relationships, color coding

### Core Philosophy

The theme emphasized in `CLAUDE.md` centers on **accessibility through multi-sensory transformation**:

1. **Single HTML Output** - No complex deployments, just download and share
2. **LLM-Driven Design** - AI understands content and creates meaningful 3D representations
3. **Primitive-Based Scenes** - No dependency on external 3D models; scenes are generated from Three.js primitives
4. **Audio Narration** - Every concept has a voice, reducing cognitive load
5. **Interactive Exploration** - Learn by doing, not just reading

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DOCUMENT UPLOAD                          │
│                    (PDF / PPTX / TXT)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: EXTRACT                                                │
│  ├─ PyMuPDF (PDF)                                              │
│  ├─ python-pptx (PowerPoint)                                   │
│  └─ Plain text parser                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: DEEP ANALYSIS (LLM)                                   │
│  ├─ Extract key concepts & relationships                       │
│  ├─ Identify hierarchies & categories                          │
│  ├─ Determine subject area & difficulty                        │
│  ├─ Generate model keywords                                    │
│  └─ Design visual theme                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: SCENE DESIGN                                          │
│  ├─ V1: Match GLTF models from GCS (legacy)                   │
│  ├─ V2: Anatomical generator (specialized)                     │
│  └─ V3: LLM-generated primitives (recommended)                 │
│      ├─ Position concepts in 3D space                          │
│      ├─ Choose shapes (sphere, box, cone, etc.)               │
│      ├─ Define colors by category                             │
│      └─ Create connections (lines, arrows)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: NARRATION GENERATION (LLM)                            │
│  └─ Context-aware explanations for each concept                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: TEXT-TO-SPEECH (ElevenLabs)                          │
│  └─ Convert narrations to high-quality audio                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: HTML GENERATION (LLM)                                 │
│  ├─ Complete Three.js scene embedded                           │
│  ├─ All interactions & animations                              │
│  ├─ Accessibility features (ARIA, keyboard nav)                │
│  └─ Responsive design                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              SINGLE HTML FILE OUTPUT                            │
│         (Downloadable, Shareable, Offline-Capable)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🎨 Three Generation Modes

1. **V1: Model Matching** (Legacy)
   - Matches pre-made GLTF models from Google Cloud Storage
   - Keyword-based semantic matching
   - Good for general topics with available models

2. **V2: Anatomical Generator** (Specialized)
   - Custom generator for anatomical/biological content
   - Specialized particle systems and animations
   - Content-aware visualizations (e.g., brain shapes for neuroscience)

3. **V3: LLM-Generated Primitives** (Recommended) ⭐
   - **No external model dependencies**
   - LLM designs entire scene using Three.js primitives
   - Creates meaningful spatial relationships
   - Truly content-aware and educational
   - See `docs/LLM_GENERATED_3D_DESIGN.md` for details

### 🎯 Accessibility First

- **Keyboard Navigation** - Full keyboard support for all interactions
- **ARIA Labels** - Screen reader compatible
- **Focus Indicators** - Clear visual focus states
- **Audio Narration** - Every concept explained verbally
- **Self-Paced** - Users control the learning speed
- **Visual Clarity** - High contrast, clear typography

### 🚀 Performance

- **Single File Output** - No server dependencies after generation
- **CDN Resources** - Fast loading from global CDNs
- **Optimized Assets** - Compressed audio, efficient 3D rendering
- **Progressive Loading** - Loading indicators for better UX

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Document Processing**: PyMuPDF, python-pptx
- **LLM**: LangChain with Google Gemini (primary) / OpenAI / OpenRouter / Ollama
- **Storage**: Google Cloud Storage (for V1 models)
- **TTS**: ElevenLabs API
- **Async**: asyncio, httpx

### Frontend
- **3D Engine**: Three.js (r160+)
- **Styling**: Vanilla CSS with glassmorphism
- **Fonts**: Google Fonts (Inter)
- **Design**: Premium gradients, micro-animations, responsive

---

## 📁 Project Structure

```
doc-to-3d-explorer/
├── Backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app, CORS config
│   │   ├── config.py                   # Settings via pydantic-settings
│   │   ├── routers/
│   │   │   └── generate.py             # POST /api/v1/generate endpoint
│   │   ├── services/
│   │   │   ├── extraction.py           # Document text extraction
│   │   │   ├── analysis.py             # LLM content analysis
│   │   │   ├── matching.py             # Model selection (V1)
│   │   │   ├── anatomical_generator.py # Specialized generator (V2)
│   │   │   ├── narration.py            # Text generation + TTS
│   │   │   └── html_generator.py       # LLM generates final HTML
│   │   ├── models/
│   │   │   ├── schemas.py              # Pydantic request/response models
│   │   │   └── analysis.py             # Content analysis models
│   │   └── utils/
│   │       ├── gcs.py                  # GCS client wrapper
│   │       └── llm.py                  # LangChain-based LLM abstraction
│   ├── docs/
│   │   └── LLM_GENERATED_3D_DESIGN.md  # V3 design documentation
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── CLAUDE.md                       # Detailed backend documentation
│
└── Frontend/
    └── index.html                      # Upload interface with premium design
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key (or other LLM provider)
- ElevenLabs API key
- Google Cloud Storage account (for V1 only)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd doc-to-3d-explorer
   ```

2. **Set up Backend**
   ```bash
   cd Backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

   Required variables:
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   
   # Optional (for V1 model matching)
   GCS_BUCKET_NAME=doc-to-3d-models
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

4. **Run Backend Server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Run Frontend** (in a new terminal)
   ```bash
   cd Frontend
   python3 -m http.server 3000
   ```

6. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## 📡 API Endpoints

### `POST /api/v1/generate`
Generate interactive 3D HTML from uploaded document.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -F "file=@document.pdf" \
  -F "version=v3" \
  --output scene.html
```

**Parameters:**
- `file`: Document file (PDF, PPTX, or TXT)
- `version`: Generation mode (`v1`, `v2`, or `v3`)

**Response:**
- Content-Type: `text/html`
- Content-Disposition: `attachment; filename="<title>_3D.html"`

### `GET /api/v1/models`
List available 3D models from GCS manifest (V1 only).

### `GET /api/v1/health`
Service health status.

---

## 🎨 Generation Modes Explained

### V1: Model Matching (Legacy)

**How it works:**
1. Analyzes document content
2. Extracts keywords and subject area
3. Matches against pre-made GLTF models in GCS
4. Selects 2-5 best matching models
5. Generates scene with matched models

**Pros:**
- High-quality 3D models
- Fast generation

**Cons:**
- Limited by available models
- May show irrelevant models
- Requires GCS setup

**Best for:** General topics with good model coverage

---

### V2: Anatomical Generator (Specialized)

**How it works:**
1. Detects anatomical/biological content
2. Generates custom particle systems
3. Creates content-aware shapes (e.g., brain outline)
4. Adds specialized animations

**Pros:**
- Content-aware visualizations
- No external models needed
- Beautiful particle effects

**Cons:**
- Limited to anatomical/biological topics
- Experimental

**Best for:** Biology, anatomy, neuroscience documents

---

### V3: LLM-Generated Primitives (Recommended) ⭐

**How it works:**
1. Deep analysis extracts concepts, relationships, hierarchies
2. LLM designs 3D scene layout
3. Chooses appropriate primitives (spheres, boxes, cones, etc.)
4. Positions concepts spatially based on relationships
5. Creates connections (lines, arrows)
6. Generates complete Three.js code

**Pros:**
- **Truly educational** - spatial relationships match content
- **No external dependencies** - uses only Three.js primitives
- **Infinitely flexible** - works for any topic
- **Meaningful interactions** - click to explore relationships

**Cons:**
- Slightly longer generation time
- Requires capable LLM

**Best for:** All educational content (recommended default)

**Scene Layout Strategies:**
- **Concept Map**: Central concept with related concepts orbiting
- **Hierarchical**: Tree structure for structured content
- **Timeline**: Linear progression for sequential content
- **Clustered**: Grouped by categories

See `docs/LLM_GENERATED_3D_DESIGN.md` for detailed design documentation.

---

## 🎯 Use Cases

### Education
- **Students**: Transform textbook chapters into interactive 3D experiences
- **Teachers**: Create engaging visual aids from lesson plans
- **Researchers**: Visualize complex papers and findings

### Accessibility
- **ADHD**: Interactive, engaging alternative to static text
- **Dyslexia**: Visual-first learning with audio support
- **Autism**: Predictable, structured exploration
- **Visual Learners**: Spatial relationships and color coding

### Professional
- **Presentations**: Convert slides into memorable 3D experiences
- **Documentation**: Make technical docs more accessible
- **Training**: Create interactive training materials

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Optional - GCS (for V1 only)
GCS_BUCKET_NAME=doc-to-3d-models
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Optional - Server
MAX_FILE_SIZE_MB=50
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
LOG_LEVEL=INFO
PORT=8000
```

### LLM Provider Configuration

The system uses LangChain for LLM abstraction. Default is Google Gemini, but you can switch:

**Google Gemini (Default):**
```bash
GOOGLE_API_KEY=your_key
```

**OpenAI:**
```bash
OPENAI_API_KEY=your_key
```

**OpenRouter:**
```bash
OPENROUTER_API_KEY=your_key
```

**Ollama (Local):**
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🎨 Frontend Design

The frontend (`Frontend/index.html`) showcases **premium web design principles**:

### Design Features
- **Glassmorphism** - Frosted glass cards with backdrop blur
- **Dynamic Gradients** - Animated multi-color backgrounds
- **Floating Orbs** - Ambient background animations
- **Micro-Animations** - Smooth hover effects and transitions
- **Premium Typography** - Google Fonts (Inter)
- **Responsive Design** - Works on desktop and mobile
- **Accessibility** - ARIA labels, keyboard navigation, skip links

### Color Palette
- Primary: `#007aff` (Blue)
- Secondary: `#af52de` (Purple)
- Accent: `#ff2d55` (Pink)
- Success: `#30d158` (Green)
- Warning: `#ff9500` (Orange)

---

## 🧪 Testing

### Manual Testing
```bash
# Test with sample PDF
curl -X POST http://localhost:8000/api/v1/generate \
  -F "file=@sample.pdf" \
  -F "version=v3" \
  --output test_scene.html

# Open in browser
open test_scene.html
```

### Unit Tests
```bash
cd Backend
pytest tests/
```

---

## 🐳 Docker Deployment

### Build Image
```bash
cd Backend
docker build -t doc-to-3d-backend .
```

### Run Container
```bash
docker run -p 8000:8000 --env-file .env doc-to-3d-backend
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./Backend
    ports:
      - "8000:8000"
    env_file:
      - ./Backend/.env
    volumes:
      - ./Backend/app:/app/app
```

---

## 📊 Error Handling

| Code | Scenario | Solution |
|------|----------|----------|
| 400 | Invalid file type | Upload PDF, PPTX, or TXT |
| 413 | File too large | Reduce file size or increase `MAX_FILE_SIZE_MB` |
| 422 | No matching models (V1) | Try V3 mode or add more models to GCS |
| 500 | LLM/TTS service error | Check API keys and service status |
| 503 | GCS unavailable | Check GCS credentials and bucket access |

**Error Response Format:**
```json
{
  "detail": "error message",
  "error_code": "NO_MATCHING_MODELS"
}
```

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

1. **More Scene Layouts** - Add new layout strategies for V3
2. **Additional LLM Providers** - Support more LLM backends
3. **Enhanced Accessibility** - Improve screen reader support
4. **Performance** - Optimize 3D rendering and loading
5. **Testing** - Expand test coverage

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Three.js** - Powerful 3D rendering engine
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM abstraction layer
- **ElevenLabs** - High-quality text-to-speech
- **Google Gemini** - Advanced language model

---

## 📚 Additional Documentation

- **Backend Details**: See `CLAUDE.md` for comprehensive backend documentation
- **V3 Design**: See `docs/LLM_GENERATED_3D_DESIGN.md` for primitive-based scene design
- **API Reference**: Visit `/docs` endpoint when server is running

---

## 🎯 Roadmap

- [ ] Support for more document formats (DOCX, Markdown)
- [ ] Real-time collaboration features
- [ ] Custom voice selection for TTS
- [ ] Export to VR formats
- [ ] Mobile app versions
- [ ] Cloud deployment templates
- [ ] Model library expansion (V1)
- [ ] Advanced animation presets (V3)

---

## 💬 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing documentation in `CLAUDE.md` and `docs/`
- Review API documentation at `/docs` endpoint

---

**Made with ❤️ for accessible, engaging education**
