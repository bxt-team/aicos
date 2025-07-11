# KlingAI Integration Documentation

## Overview

The Instagram Reel Generator now supports KlingAI for high-quality video generation. KlingAI provides cinematic quality video generation with support for text-to-video, image-to-video, and advanced camera controls.

## Features

- **Text-to-Video**: Generate videos from text prompts
- **Image-to-Video**: Animate static images into videos
- **Camera Control**: Professional camera movements (zoom, pan, dolly, etc.)
- **Multiple Models**: Support for Kling 2.1, 2.0, 1.6, 1.5, and 1.0
- **High Quality**: 1080p resolution at 30fps
- **Instagram Optimized**: Automatic 9:16 aspect ratio for Reels
- **Duration**: Up to 10 seconds per video

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# KlingAI Configuration
KLINGAI_API_KEY=your_klingai_api_key_here
KLINGAI_PROVIDER=piapi  # Options: piapi, appypie, segmind
```

### API Providers

1. **PiAPI** (Recommended)
   - URL: https://piapi.ai/kling-api
   - Features: All models, text-to-video, image-to-video, extend video
   - Max duration: 10 seconds

2. **Appy Pie**
   - URL: https://www.appypiedesign.ai/api/
   - Features: Text-to-video, image-to-video
   - Max duration: 10 seconds

3. **Segmind**
   - URL: https://www.segmind.com/
   - Features: Image-to-video only
   - Max duration: 5 seconds

## API Usage

### Generate Instagram Reel with KlingAI

```bash
POST /api/generate-instagram-reel
```

Request body:
```json
{
  "instagram_text": "Your Instagram caption text",
  "period": "Energie",  // One of the 7 Cycles periods
  "provider": "klingai",
  "klingai_model": "kling-2.1",  // Optional, defaults to kling-2.1
  "additional_input": "Additional context",  // Optional
  "image_paths": ["/path/to/image.jpg"],  // Optional, for image-to-video
  "force_new": false  // Force regeneration even if cached
}
```

### Available Models

```bash
GET /api/klingai-models
```

Returns available KlingAI models with their features and recommendations.

### Video Providers Info

```bash
GET /api/video-providers
```

Returns information about all available video generation providers including KlingAI.

## Period-Specific Styling

Each of the 7 Cycles periods has optimized camera movements:

- **Image**: Slow zoom in - creates intimacy and focus
- **Veränderung**: Smooth horizontal pan - suggests change and transition
- **Energie**: Dynamic orbit - energetic circular movement
- **Kreativität**: Creative dolly forward - exploration and discovery
- **Erfolg**: Elegant crane up - ascending success movement
- **Entspannung**: Static peaceful shot - calm and stability
- **Umsicht**: Contemplative pull back - gaining perspective

## Implementation Details

### KlingAI Client (`backend/app/services/klingai_client.py`)

The KlingAI client handles:
- API authentication for different providers
- Text-to-video and image-to-video generation
- Task status polling
- Video download and storage

### Instagram Reel Agent Updates

The `InstagramReelAgent` now includes:
- `generate_reel_with_klingai()` method
- `generate_klingai_prompt()` for optimized prompts
- Period-specific camera controls
- Model selection support

### API Flow

1. User requests video generation with KlingAI
2. Agent generates optimized prompt based on period and content
3. KlingAI API creates generation task
4. System polls for completion (typically 1-3 minutes)
5. Video is downloaded and stored
6. URL returned to user

## Best Practices

1. **Model Selection**
   - Use Kling 2.1 for best quality and motion
   - Use Kling 1.6 for faster generation
   - Use Kling 2.0 for stable, reliable results

2. **Prompts**
   - Be specific about visual style and mood
   - Include camera movement descriptions
   - Specify Instagram Reels format (9:16, vertical)

3. **Image-to-Video**
   - Use high-quality source images (at least 1080x1920)
   - Provide context in the prompt for better animation
   - Consider the period theme when selecting images

4. **Performance**
   - Videos are cached to avoid regeneration
   - Use `force_new=true` to regenerate
   - Generation typically takes 1-3 minutes

## Error Handling

The system handles:
- API authentication failures
- Generation timeouts (5-minute max)
- Network errors with retry logic
- Invalid model or provider selection

## Future Enhancements

- Support for video extension (adding to existing videos)
- Batch generation for multiple periods
- Custom camera control parameters
- Integration with other KlingAI features