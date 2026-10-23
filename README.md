# VibeShift AI

## Instant Persona, Communication & Image Understanding Transformer

**One message. Any audience. Any vibe. Any image. ✨**

VibeShift AI is an AI-powered communication transformation platform that rewrites rough messages for different audiences and communication styles while preserving the user's original meaning.

It also supports **image understanding**, allowing users to upload an image and let the AI analyze and describe its visible content. The extracted information can then be used as context for generating or transforming communication.

Instead of manually rewriting the same message for different situations, users can select a persona and instantly transform their communication — whether the input starts as text or an image.

---

## 🎯 Problem Statement

People often need to communicate the same information in completely different ways depending on their audience.

For example, the same message may need to sound:

* 👔 Professional for an executive
* 🤝 Friendly for a teammate
* ⚖️ Precise for compliance communication
* 🔥 Casual and energetic for Gen Z

At the same time, important information is not always available as plain text. It may exist inside:

* Screenshots
* Posters
* Notices
* Documents
* Social media posts
* Event images
* Infographics
* Photos containing text or visual information

VibeShift AI solves both problems by allowing AI to **understand visual information and transform communication style while preserving the original intent and important details.**

---

# 🚀 Key Features

## 🎭 Four AI Personas

| Persona                | Communication Style                         |
| ---------------------- | ------------------------------------------- |
| 👔 Executive / C-Level | Concise, professional and decision-oriented |
| 🤝 Supportive Peer     | Friendly, constructive and encouraging      |
| ⚖️ Legal / Compliance  | Precise, neutral and formal                 |
| 🔥 Gen Z Hype          | Casual, energetic, expressive and modern    |

---

## 📝 Text Transformation

Users can enter a rough message and instantly transform it according to the selected persona.

### Supported inputs

* Original message
* Optional audience
* Optional context
* Selected communication persona

The AI preserves the core meaning while adapting the tone, vocabulary and presentation.

---

# 🖼️ AI Image Understanding

VibeShift AI can also work with **images**, not just text.

Users can upload an image and the AI can analyze the visible information and generate a meaningful description of what the image contains.

### Example

**Input Image:**

A screenshot of a college event announcement containing:

> Hackathon 2026
> Registration closes on Friday
> Venue: Main Auditorium

### AI Understanding:

The AI can identify that the image contains information about a college hackathon, including the registration deadline and venue.

### The information can then be transformed into:

**👔 Executive**

> The college hackathon registration closes on Friday. The event will be held in the Main Auditorium.

**🤝 Supportive Peer**

> Hey! Just a reminder that the hackathon registration closes this Friday. The event is happening in the Main Auditorium!

**🔥 Gen Z Hype**

> 🚨 Hackathon alert! Registration closes this Friday, so make sure you sign up ASAP! 🔥 The event is happening in the Main Auditorium!

---

## 🧠 Image-to-Description Flow

```text
        USER
          │
          ▼
    Upload Image
          │
          ▼
 ┌───────────────────┐
 │   Image Analysis  │
 │    AI Vision      │
 └─────────┬─────────┘
           │
           ▼
   Understand Image
           │
           ▼
   Generate Description
           │
           ▼
   Optional Context
           │
           ▼
   Select AI Persona
           │
           ▼
 Communication Transformation
           │
           ▼
      Final Output
```

---

# ✨ Core Features

### Communication

* 🤖 AI-powered message transformation
* 🎭 Four communication personas
* 📝 Original message input
* 👥 Optional audience field
* 💡 Optional context field
* 🔄 Regenerate transformation
* 📋 Copy transformed message
* 🔍 Original vs rewritten comparison
* 🟢 Added text highlighting
* 🔴 Removed text highlighting
* 📊 Word count statistics
* 📈 Percentage length change

### Image Intelligence

* 🖼️ Image upload
* 👁️ AI-powered image understanding
* 📝 Image-to-description generation
* 🔎 Identification of visible information
* 📄 Text/context extraction from images
* 🔄 Use image understanding as transformation context
* 🎭 Transform image-derived information into different communication styles

### User Experience

* 🌙 Dark / Light mode
* 📱 Responsive design
* ⚡ Loading states
* ❌ Error handling
* 🧹 Clear / reset functionality
* 💬 Example messages
* 🔢 Character and word counters

---

# 🧠 How It Works

## Text Input

```text
USER
  │
  ▼
Enter Message
  │
  ▼
Select Persona
  │
  ▼
React Frontend
  │
  │ POST /api/transform
  ▼
Flask Backend
  │
  ▼
AI Model
  │
  ▼
Rewritten Text
  │
  ▼
Text Diff
  │
  ▼
Original vs Rewritten
```

## Image Input

```text
USER
  │
  ▼
Upload Image
  │
  ▼
React Frontend
  │
  │ POST /api/image-analyze
  ▼
Flask Backend
  │
  ▼
Vision / AI Model
  │
  ▼
Image Description
  │
  ▼
Optional Context
  │
  ▼
Persona Selection
  │
  ▼
Communication Transformation
  │
  ▼
Final AI Response
```

---

# 🛠️ Tech Stack

## Frontend

* React
* Vite
* Tailwind CSS
* Lucide React
* JavaScript

## Backend

* Python
* Flask
* Flask-CORS
* REST API

## AI

* Hugging Face
* Instruction-tuned language model
* Vision-capable AI model for image understanding
* Local inference when hardware allows
* Optional hosted inference

## Other

* Text-diff library
* Browser Clipboard API
* Environment variables
* Responsive CSS

---

# 📂 Project Structure

```text
vibeshift-ai/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   ├── vite.config.js
│   └── ...
│
├── backend/
│   ├── routes/
│   │   ├── transform.py
│   │   └── image.py
│   │
│   ├── services/
│   │   ├── model_service.py
│   │   └── vision_service.py
│   │
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
├── README.md
└── LICENSE
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/vibeshift-ai.git
cd vibeshift-ai
```

---

# 🎨 Frontend Setup

Open a terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally run at:

```text
http://localhost:5173
```

---

# 🐍 Backend Setup

Open another terminal:

```bash
cd backend
```

Create a Python virtual environment.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create:

```text
backend/.env
```

Example:

```env
MODEL_NAME=your-model-name
VISION_MODEL_NAME=your-vision-model-name
HF_TOKEN=your_huggingface_token
PORT=5000
```

Never commit `.env` to GitHub.

Add it to `.gitignore`:

```text
.env
venv/
__pycache__/
node_modules/
dist/
```

---

# ▶️ Run the Backend

From the backend directory:

```bash
python app.py
```

The backend will normally run at:

```text
http://localhost:5000
```

---

# 🔌 API

## POST `/api/transform`

Transforms a message according to the selected persona.

### Request

```json
{
  "text": "Please send me the project report when you have time.",
  "persona": "executive",
  "context": "This is for our college project.",
  "audience": "Project team"
}
```

### Response

```json
{
  "original": "Please send me the project report when you have time.",
  "rewritten": "Please share the project report at your earliest convenience.",
  "persona": "executive",
  "original_word_count": 10,
  "rewritten_word_count": 9
}
```

---

# 🖼️ Image Analysis API

## POST `/api/image-analyze`

Analyzes an uploaded image and generates a description based on the visible information.

### Example Request

```text
POST /api/image-analyze
Content-Type: multipart/form-data

image: uploaded_image.png
```

### Example Response

```json
{
  "description": "The image contains a college hackathon announcement with information about the registration deadline and venue.",
  "detected_text": "Hackathon 2026. Registration closes on Friday.",
  "status": "success"
}
```

The generated description can then be passed as context to the communication transformation system.

---

# ❤️ Health Check

The backend provides:

```text
GET /api/health
```

Example response:

```json
{
  "status": "ok"
}
```

---

# ✍️ Example Transformation

## Original

> Hey, can you please send me the presentation? I need it because I have to finish my section.

### 👔 Executive / C-Level

> Please share the presentation so I can complete my assigned section.

### 🤝 Supportive Peer

> Hey! Could you send over the presentation when you get a chance? It'll help me finish my section. Thanks!

### ⚖️ Legal / Compliance

> Please provide the presentation materials so that I may complete the assigned section.

### 🔥 Gen Z Hype

> Heyyy! Can you send the presentation my way? I need it to finish my part ASAP 🙌

---

# 🖼️ Example Image Transformation

### Input

The user uploads an image containing a college announcement.

### AI Image Understanding

> The image is a college event announcement. It provides information about an upcoming hackathon, including its registration deadline and venue.

### 👔 Executive

> The college hackathon is scheduled for the upcoming event period. Registration closes on Friday, and the venue is the Main Auditorium.

### 🤝 Supportive Peer

> Hey! Just a reminder about the upcoming college hackathon. Registration closes on Friday, and it's happening in the Main Auditorium!

### 🔥 Gen Z Hype

> 🚨 Hackathon incoming! Registration closes Friday, so don't miss out! 🔥 Catch you at the Main Auditorium!

---

# 🔍 Text Comparison

VibeShift AI performs a real textual comparison between the original and generated message.

The comparison identifies:

* 🟢 Added words
* 🔴 Removed words
* ⚪ Unchanged text
* 📊 Original word count
* 📊 Rewritten word count
* 📈 Percentage length change

### Example

**Original:**

> Please send the report when you have time.

**Rewritten:**

> Please send the report at your earliest convenience.

The application visually highlights the differences.

> **Note:** The comparison represents textual differences. It is not a guaranteed semantic-equivalence score.

---

# 🔒 Privacy & Security

VibeShift AI follows a privacy-first approach.

* User messages are not logged by default.
* Messages are not permanently stored on the backend.
* API keys remain on the server.
* Secrets are stored using environment variables.
* No API keys are exposed in frontend code.
* Request sizes are validated and limited.
* AI output is rendered safely as text.
* Backend input validation is implemented.
* CORS is configured for the application.

For image processing, uploaded images should only be processed for the requested AI analysis and should not be permanently stored unless explicitly required by the application.

---

# ⚖️ Legal / Compliance Disclaimer

The Legal / Compliance persona only changes communication style.

It does **not**:

* Provide legal advice
* Guarantee legal compliance
* Replace a lawyer
* Guarantee that generated content satisfies any regulation

Generated content should be reviewed by an appropriate professional when necessary.

---

# 🎨 UI/UX

VibeShift AI follows a modern AI SaaS design system.

## Design Principles

* ✨ Premium visual appearance
* 🌈 Subtle gradients
* 🧊 Rounded cards
* 📐 Consistent spacing
* 🌓 Dark / Light mode
* 📱 Responsive layout
* ⚡ Smooth interactions
* ♿ Accessible controls
* 🎯 Clear visual hierarchy
* 🖼️ Intuitive image upload experience

---

# 🏆 Hackathon MVP

VibeShift AI is designed specifically for a short-duration hackathon.

The project prioritizes:

```text
Working AI
     ↓
Image + Text Understanding
     ↓
Reliable API
     ↓
Real Text Comparison
     ↓
Good User Experience
     ↓
Polished UI
```

Instead of spending time on unnecessary features such as authentication, payments, or complex databases, the project focuses on delivering a strong end-to-end AI experience.

---

# 🔮 Future Improvements

Potential future features include:

* 🔀 Compare multiple personas simultaneously
* 💾 Transformation history
* 🧠 Custom personas
* 🌐 Multilingual transformations
* 🎙️ Voice-to-message transformation
* 📧 Email integration
* 💬 Slack / Teams integration
* 🌍 Browser extension
* 📱 Mobile application
* 🏢 Organization-specific communication styles
* 📊 Advanced semantic similarity analysis
* 🖼️ Advanced document and image understanding
* 📄 PDF/image document summarization
* 🔍 OCR-powered text extraction
* 🎨 Image-based content generation
* 🧠 Multi-modal conversations

---

# ⚠️ Limitations

* AI output depends on the selected model.
* Image understanding accuracy depends on image quality and the capabilities of the vision model.
* Small, blurry, rotated or low-quality text may not be interpreted correctly.
* Local inference performance depends on available hardware.
* Hosted inference requires API configuration.
* AI-generated text may occasionally require human review.
* Legal / Compliance mode does not provide legal advice.
* Semantic equivalence cannot be guaranteed solely through textual diffing.
* Image analysis should not be treated as a substitute for professional visual, medical, legal or technical judgment.

---

# 🧪 Testing Checklist

Before demonstrating the project, verify:

```text
[ ] Frontend starts successfully
[ ] Backend starts successfully
[ ] Health endpoint works
[ ] User can enter text
[ ] User can upload an image
[ ] Image analysis works
[ ] AI generates an image description
[ ] All four personas work
[ ] AI generates real output
[ ] Image-derived context can be transformed
[ ] Loading state appears
[ ] Error state works
[ ] Copy button works
[ ] Regenerate works
[ ] Text comparison works
[ ] Word counts are correct
[ ] Length percentage is correct
[ ] Dark/light mode works
[ ] Mobile layout works
[ ] API keys are not exposed
```

---

# 👩‍💻 Development Architecture

The application uses a modular architecture so the AI model can be replaced without redesigning the entire application.

```text
                 ┌──────────────┐
                 │    React     │
                 │   Frontend   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   REST API   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │    Flask     │
                 │   Backend    │
                 └──────┬───────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      ┌──────────────┐      ┌──────────────┐
      │ Text Model   │      │ Vision Model │
      └──────┬───────┘      └──────┬───────┘
             │                     │
             └──────────┬──────────┘
                        ▼
                  AI Response
```

This separation keeps the frontend, backend, text AI and image AI integration maintainable and easy to modify.

---

# 💡 Why VibeShift AI?

Communication isn't one-size-fits-all.

The same idea can require completely different wording depending on who you're talking to.

And sometimes, that idea isn't even available as text — it may be inside an image, screenshot, poster or announcement.

VibeShift AI brings these capabilities together:

**See → Understand → Transform → Communicate**

A user can provide text or an image, let AI understand the information, choose the desired communication persona, and receive a polished response.

---

# 🌟 Project Vision

VibeShift AI aims to make communication more intelligent, adaptive and accessible.

Whether the user starts with:

* 📝 A rough message
* 🖼️ An image
* 📸 A screenshot
* 📄 Visual information
* 💡 A simple idea

VibeShift AI helps turn it into communication that fits the audience.

## One input.

## Any audience.

## Any vibe.

## ✨ VibeShift AI.

---

# 📜 License

This project was created for educational and hackathon purposes.

If this project is released publicly, add an appropriate open-source license.
