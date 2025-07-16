# Background Video Agent

## Overview

The Background Video Agent is a simplified video generation system designed specifically for creating short, looping background videos for Instagram Reels and similar social media content. It generates 5-10 second videos using KlingAI with piapi integration.

## Features

- **Short Duration**: Optimized for 5 or 10 second videos
- **Seamless Loops**: Designed to loop perfectly for continuous playback
- **Period-Specific Themes**: Pre-configured themes for each 7 Cycles period
- **Vertical Format**: 9:16 aspect ratio for Instagram Reels
- **Simple Prompts**: Focused on abstract, background-only content

## API Endpoints

### Generate Background Video
```
POST /api/generate-background-video
```

Request body:
```json
{
  "period": "Energie",
  "duration": 5,  // 5 or 10 seconds
  "custom_prompt": "Optional custom prompt"
}
```

Response:
```json
{
  "success": true,
  "video": {
    "id": "abc123",
    "period": "Energie",
    "duration": 5,
    "file_url": "/static/background_videos/energie_background_5s_abc123.mp4",
    "external_url": "https://klingai-output-url.mp4",
    "created_at": "2024-01-16T12:00:00Z"
  },
  "message": "5s background video generated successfully"
}
```

### Get Background Videos
```
GET /api/background-videos?period=Energie
```

### Delete Background Video
```
DELETE /api/background-videos/{video_id}
```

### Get Video Themes
```
GET /api/background-video-themes
```

## Period Themes

Each period has optimized keywords and moods for background video generation:

### Image
- **Keywords**: golden light, sunburst, radiant glow
- **Mood**: inspiring
- **Description**: Goldenes Licht und strahlende Energie

### Veränderung
- **Keywords**: flowing water, transformation, blue waves
- **Mood**: dynamic
- **Description**: Fließende Transformation und Wandel

### Energie
- **Keywords**: fire, lightning, red energy burst
- **Mood**: powerful
- **Description**: Kraftvolle Energie und Dynamik

### Kreativität
- **Keywords**: paint splash, colorful abstract, yellow burst
- **Mood**: creative
- **Description**: Kreative Explosion und Farbenspiel

### Erfolg
- **Keywords**: sparkling lights, celebration, magenta glow
- **Mood**: triumphant
- **Description**: Erfolg und festlicher Glanz

### Entspannung
- **Keywords**: calm water, green nature, peaceful clouds
- **Mood**: relaxing
- **Description**: Ruhe und natürliche Harmonie

### Umsicht
- **Keywords**: purple mist, cosmic space, gentle stars
- **Mood**: contemplative
- **Description**: Weisheit und kosmische Verbindung

## Usage Examples

### Basic Usage
```python
# Generate a 5-second background video for Energie period
result = await generate_background_video({
    "period": "Energie",
    "duration": 5
})
```

### Custom Prompt
```python
# Generate with custom prompt
result = await generate_background_video({
    "period": "Kreativität",
    "duration": 10,
    "custom_prompt": "Abstract paint explosions in yellow and orange"
})
```

## Configuration

Set the following environment variables:
```bash
KLINGAI_API_KEY=your_api_key_here
KLINGAI_PROVIDER=piapi  # Currently only piapi is supported
```

## Prompt Guidelines

The agent automatically formats prompts for optimal results:
- Always includes duration (5 or 10 seconds)
- Enforces seamless loop requirement
- Excludes text and people
- Specifies vertical format
- Uses abstract, background-focused descriptions

Example generated prompt:
```
"Abstract background video: fire, lightning, red energy burst. powerful mood. 5 seconds, seamless loop, no text, no people, vertical format"
```

## Error Handling

Common errors and solutions:

1. **"KlingAI client not initialized"**
   - Ensure KLINGAI_API_KEY is set in environment

2. **"Failed to generate video"**
   - Check KlingAI API status
   - Verify API key is valid
   - Check prompt formatting

3. **Invalid duration**
   - Only 5 or 10 seconds are supported
   - Defaults to 5 seconds if invalid

## Storage

Videos are stored in:
- **Local**: `/static/background_videos/`
- **Metadata**: `/static/background_videos_storage.json`

## Differences from Instagram Reel Agent

This agent is a simplified version focusing only on background videos:
- ✅ Single provider (KlingAI with piapi)
- ✅ Short durations (5-10 seconds)
- ✅ Simple, focused prompts
- ✅ No complex video composition
- ✅ No multiple provider selection
- ✅ Optimized for looping backgrounds

## Future Enhancements

- Download and store videos locally
- Preview generation
- Batch generation for all periods
- Template-based prompts
- Integration with video composition tools