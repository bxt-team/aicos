# Voice Over & Caption Features

This document describes the new voice over and caption functionality for Instagram Reels.

## Features

### 1. Voice Over Generation
- Generate professional voice overs using ElevenLabs API
- Multiple voice options with different styles and genders
- Support for multiple languages (English, German, Spanish, French, etc.)
- Voice script generation optimized for video content

### 2. Caption/Subtitle Generation
- Automatic transcription using OpenAI Whisper
- Multiple subtitle formats: SRT, WebVTT, ASS
- Customizable caption styles (minimal, bold, colorful, elegant)
- Option to burn captions into video or keep as separate tracks

### 3. Complete Video Processing Pipeline
- Add voice over to existing videos
- Generate and add captions automatically
- Process videos with both voice and captions in one step

## Setup

### Prerequisites
1. Install required Python packages:
   ```bash
   pip install webvtt-py srt
   ```

2. Set up environment variables in `.env`:
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

3. Ensure FFmpeg is installed on your system for video processing

## Usage

### In the Instagram Reel Interface

1. **Adding Voice Over to a Reel:**
   - Navigate to the Instagram Reel interface
   - Find the reel you want to add voice over to
   - Click the "🎤 Voice Over" button
   - In the modal, you can:
     - Generate a voice script based on video content
     - Select voice and language
     - Choose caption style
     - Process the video with voice and captions

2. **Voice Script Generation:**
   - Describe your video content
   - Set target duration
   - Choose speaking style (conversational, professional, energetic, etc.)
   - Optionally specify the 7 Cycles period for optimized content

3. **Caption Customization:**
   - Choose from predefined styles (minimal, bold, colorful, elegant)
   - Set whether to burn captions into video
   - Adjust caption timing and appearance

## API Endpoints

### Voice Over Endpoints

- `POST /api/generate-voice-script` - Generate optimized voice script
- `POST /api/generate-voice-over` - Create voice over audio
- `POST /api/generate-captions` - Generate captions from audio
- `POST /api/add-voice-to-video` - Add voice over to video
- `POST /api/add-captions-to-video` - Add captions to video
- `POST /api/process-video-with-voice-and-captions` - Complete pipeline
- `GET /api/available-voices` - Get list of available voices
- `GET /api/caption-styles` - Get available caption styles
- `GET /api/voice-overs` - Get generated voice over history

## Available Voices

The system includes 12 different voices from ElevenLabs:
- **Female voices:** Rachel (calm), Domi (young), Bella (soft), Elli (emotional)
- **Male voices:** Clyde (conversational), Dave (conversational), Antoni (well-rounded), Josh (deep), Arnold (crisp), Adam (deep), Sam (raspy)

## Technical Details

### Voice Over Agent Architecture
- Located in `src/agents/voice_over_agent.py`
- Integrates with ElevenLabs API for voice synthesis
- Uses OpenAI Whisper for transcription
- Leverages FFmpeg for video/audio processing

### Frontend Components
- `VoiceOverInterface.tsx` - Main UI component for voice over features
- Integrated into `InstagramReelInterface.tsx` via modal dialog

### Storage
- Voice overs are stored in `static/voice_overs/`
- Processed videos in `static/videos_with_voice/`
- Subtitles in `static/subtitles/`
- Metadata stored in JSON files for quick retrieval

## Limitations

- ElevenLabs API key required for voice generation
- FFmpeg must be installed for video processing
- Voice generation is limited by ElevenLabs API quotas
- Transcription accuracy depends on audio quality

## Future Enhancements

- Background music mixing
- Multiple voice tracks
- Advanced caption animations
- Real-time preview
- Voice cloning capabilities
- Automatic translation