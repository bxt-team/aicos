# Video Template System for Post Composition

## Overview

The Post Composition Agent now includes a powerful video template system that allows you to create dynamic videos with replaceable text, colors, and video elements - without requiring a Canva API subscription. This system uses MoviePy for video manipulation and supports Instagram Reels, Stories, and Posts.

## Features

### Video Templates

The system includes three pre-built video templates:

1. **Energy Burst** (`energy_burst`)
   - Duration: 15 seconds
   - Dynamic energy-themed video with color transitions
   - Replaceable elements:
     - Main text (appears center, fades in)
     - Subtitle (slides up from bottom)
     - Background video
     - Primary color overlay

2. **Quote Carousel** (`quote_carousel`)
   - Duration: 20 seconds
   - Animated quote presentation with 3 sequential quotes
   - Replaceable elements:
     - Three quote texts (fade in/out sequentially)
     - Background video (loops)

3. **Period Showcase** (`period_showcase`)
   - Duration: 10 seconds
   - 7 Cycles period presentation with dynamic colors
   - Replaceable elements:
     - Period name (zooms in)
     - Period description
     - Period color overlay with gradient

## API Endpoints

### Get Available Video Templates
```
GET /api/video-templates
```

Returns all available video templates with their replaceable elements.

### Get Template Fields
```
GET /api/video-template-fields/{template_id}
```

Returns the specific replaceable fields for a template.

### Create Video Reel
```
POST /api/create-video-reel
```

Body:
```json
{
  "template_id": "energy_burst",
  "content_data": {
    "text_replacements": {
      "main_text": "Harness Your Energy",
      "subtitle": "7 Cycles - Energie Period"
    },
    "video_replacements": {
      "background_video": "/path/to/background.mp4"
    },
    "color_replacements": {
      "primary_overlay": "#F44336"
    },
    "period": "Energie"
  }
}
```

### Compose Video Post
```
POST /api/compose-video-post
```

Body:
```json
{
  "background_path": "/path/to/background.jpg",
  "text": "Your main content",
  "period": "Energie",
  "template_name": "video:energy_burst",
  "post_format": "reel",
  "custom_options": {
    "text_replacements": {
      "main_text": "Custom main text",
      "subtitle": "Custom subtitle"
    },
    "video_replacements": {
      "background_video": "/path/to/video.mp4"
    },
    "color_replacements": {
      "primary_overlay": "#FF0000"
    }
  }
}
```

## Usage Examples

### 1. Creating an Energy Burst Video

```python
# Create an energetic video for the Energie period
result = await create_video_reel({
    "template_id": "energy_burst",
    "content_data": {
        "text_replacements": {
            "main_text": "Unleash Your Creative Power",
            "subtitle": "Transform Ideas into Reality"
        },
        "video_replacements": {
            "background_video": "/static/videos/energy_background.mp4"
        },
        "color_replacements": {
            "primary_overlay": "#F44336"  # Red for Energie
        },
        "period": "Energie"
    }
})
```

### 2. Creating a Quote Carousel

```python
# Create a quote carousel video
result = await create_video_reel({
    "template_id": "quote_carousel",
    "content_data": {
        "text_replacements": {
            "quote_1": "Energy flows where attention goes",
            "quote_2": "Every moment is a fresh beginning",
            "quote_3": "Create your own sunshine"
        },
        "video_replacements": {
            "background_loop": "/static/videos/calm_background.mp4"
        }
    }
})
```

### 3. Creating a Period Showcase

```python
# Showcase a specific 7 Cycles period
result = await create_video_reel({
    "template_id": "period_showcase",
    "content_data": {
        "text_replacements": {
            "period_name": "ENTSPANNUNG",
            "period_description": "Zeit für Ruhe und Regeneration"
        },
        "color_replacements": {
            "period_color": "#4CAF50"  # Green for Entspannung
        },
        "period": "Entspannung"
    }
})
```

## Template Customization

### Text Zones
Each text zone supports:
- **Position**: Center, specific coordinates, or relative positions
- **Size**: Font size in pixels
- **Color**: Text color (hex or named colors)
- **Font**: Font family (defaults to Arial)
- **Animation**: fade_in, fade_out, slide_up, zoom_in
- **Timing**: start_time and duration in seconds

### Video Zones
Video zones support:
- **Position**: Placement on the canvas
- **Size**: "full" or custom dimensions
- **Timing**: start_time and duration
- **Loop**: Auto-loop if video is shorter than duration
- **Blend Mode**: How the video blends with background

### Color Overlays
Color overlays support:
- **Color**: Hex color code
- **Opacity**: 0.0 to 1.0
- **Gradient**: Optional gradient effect
- **Animation**: Optional pulsing or other effects

## Period Color Mapping

The system automatically maps 7 Cycles periods to colors:
- **Image**: Gold (#DAA520)
- **Veränderung**: Blue (#2196F3)
- **Energie**: Red (#F44336)
- **Kreativität**: Yellow (#FFD700)
- **Erfolg**: Magenta (#CC0066)
- **Entspannung**: Green (#4CAF50)
- **Umsicht**: Purple (#9C27B0)

## Technical Requirements

### Dependencies
- MoviePy for video processing
- PIL/Pillow for image manipulation
- NumPy for array operations
- FFmpeg (must be installed on system)

### Supported Formats
- **Input Videos**: MP4, MOV, AVI
- **Output**: MP4 (H.264 codec, AAC audio)
- **Resolution**: 1080x1920 (Reels/Stories), 1080x1080 (Posts)

## Advantages Over Canva API

1. **No API Key Required**: Works without any external API subscription
2. **Full Control**: Complete control over video generation process
3. **Cost-Effective**: No per-use charges or monthly fees
4. **Customizable**: Easy to add new templates and effects
5. **Privacy**: All processing happens locally
6. **No Rate Limits**: Generate unlimited videos

## Creating Custom Templates

To add new templates, edit the `_load_templates()` method in `video_template_tools.py`:

```python
"custom_template": VideoTemplate(
    name="Custom Template",
    description="Your custom template description",
    duration=12.0,
    text_zones=[
        {
            "id": "title",
            "position": ("center", 500),
            "size": 70,
            "color": "white",
            "start_time": 1,
            "duration": 10,
            "animation": "fade_in"
        }
    ],
    video_zones=[
        {
            "id": "background",
            "position": (0, 0),
            "size": "full",
            "start_time": 0,
            "duration": 12
        }
    ]
)
```

## Troubleshooting

### Common Issues

1. **FFmpeg Not Found**
   - Install FFmpeg: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)

2. **Video Format Not Supported**
   - Convert videos to MP4 format before using

3. **Memory Issues with Large Videos**
   - Reduce video resolution or duration
   - Process videos in smaller segments

4. **Text Not Displaying**
   - Ensure fonts are installed on system
   - Use standard fonts like Arial or Helvetica