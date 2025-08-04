# AI Interview Assistant

A comprehensive AI-powered interview practice platform built with Next.js, LiveKit, and OpenAI Azure API.

## Features

### 🔐 Authentication
- User registration and login system
- Secure session management
- User profile management

### 📄 Resume Upload & Analysis
- Drag-and-drop resume upload
- Support for PDF, DOC, and DOCX formats
- AI-powered resume parsing
- Skills and experience extraction

### 🎯 Job Recommendations
- Personalized job matching based on resume
- Match percentage scoring
- Detailed job descriptions
- Company and location information

### 🎤 AI Interview Practice
- Voice-to-voice AI interviews
- Real-time conversation with AI
- Job-specific interview questions
- Live transcription and feedback

### 📊 Interview Preparation
- Equipment setup and testing
- Microphone and camera permissions
- Interview tips and guidelines
- Progress tracking

## Technology Stack

- **Frontend**: Next.js 15, React 19, TypeScript
- **UI Components**: Radix UI, Tailwind CSS
- **Animations**: Motion (Framer Motion)
- **Voice Communication**: LiveKit
- **AI Integration**: OpenAI Azure API
- **Icons**: Phosphor Icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- pnpm (recommended) or npm
- LiveKit account and credentials
- OpenAI Azure API access

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   cd voice-assistant/frontend
   pnpm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env.local
   ```
   
   Add your LiveKit and OpenAI credentials to `.env.local`

4. Start the development server:
   ```bash
   pnpm dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage Flow

1. **Authentication**: Sign up or log in to your account
2. **Resume Upload**: Upload your resume to get personalized job recommendations
3. **Job Selection**: Choose from AI-recommended jobs based on your profile
4. **Interview Setup**: Configure your microphone and camera
5. **AI Interview**: Practice with the AI interviewer using voice conversation

## Component Structure

```
components/
├── auth/
│   ├── login-form.tsx
│   └── signup-form.tsx
├── resume/
│   └── resume-upload.tsx
├── jobs/
│   └── job-recommendations.tsx
├── interview/
│   └── interview-preparation.tsx
├── ui/
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   └── label.tsx
└── interview-assistant.tsx (main orchestrator)
```

## Key Components

### InterviewAssistant
The main component that orchestrates the entire interview flow, managing state and view transitions.

### ResumeUpload
Handles file upload with drag-and-drop support, file validation, and AI-powered resume analysis.

### JobRecommendations
Displays personalized job matches with match percentages and detailed information.

### InterviewPreparation
Manages equipment setup, permissions, and provides interview tips before starting.

## Customization

### Styling
The app uses Tailwind CSS with a custom design system. Colors and themes can be modified in `app/globals.css`.

### AI Integration
The interview AI is powered by OpenAI Azure API through LiveKit. Customize the AI behavior by modifying the backend API.

### Job Matching
Job recommendations are currently mocked. Integrate with real job APIs (Indeed, LinkedIn, etc.) for production use.

## Development

### Adding New Features
1. Create new components in the appropriate directory
2. Update the `InterviewAssistant` component to handle new views
3. Add necessary types to `lib/types.ts`
4. Update the progress bar if adding new steps

### Testing
```bash
# Run linting
pnpm lint

# Run type checking
pnpm type-check

# Format code
pnpm format
```

## Deployment

The app can be deployed to Vercel, Netlify, or any other Next.js-compatible platform.

```bash
# Build for production
pnpm build

# Start production server
pnpm start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 