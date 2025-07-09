import os
import json
import subprocess
import requests
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
from src.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
import webvtt
import srt
from datetime import timedelta

class VoiceOverAgent(BaseCrew):
    """Agent for creating voice overs and adding captions/subtitles to videos"""
    
    def __init__(self, openai_api_key: str, elevenlabs_api_key: str = None):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.elevenlabs_api_key = elevenlabs_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Storage for voice overs
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/voice_overs_storage.json")
        self.voice_storage = self._load_voice_storage()
        
        # Output directories
        self.audio_output_dir = os.path.join(os.path.dirname(__file__), "../../static/voice_overs")
        self.video_output_dir = os.path.join(os.path.dirname(__file__), "../../static/videos_with_voice")
        self.subtitle_output_dir = os.path.join(os.path.dirname(__file__), "../../static/subtitles")
        
        os.makedirs(self.audio_output_dir, exist_ok=True)
        os.makedirs(self.video_output_dir, exist_ok=True)
        os.makedirs(self.subtitle_output_dir, exist_ok=True)
        
        # Create agents
        self.voice_agent = self.create_agent("voice_over_agent", llm=self.llm)
        self.caption_agent = self.create_agent("caption_agent", llm=self.llm)
        
        # ElevenLabs settings
        self.elevenlabs_base_url = "https://api.elevenlabs.io/v1"
        self.elevenlabs_headers = {
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        } if elevenlabs_api_key else {}
        
        # Available ElevenLabs voices
        self.available_voices = {
            "rachel": {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female", "style": "calm"},
            "clyde": {"voice_id": "2EiwWnXFnvU5JabPnv8n", "name": "Clyde", "gender": "male", "style": "conversational"},
            "domi": {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "style": "young"},
            "dave": {"voice_id": "CYw3kZ02Hs0563khs1Fj", "name": "Dave", "gender": "male", "style": "conversational"},
            "fin": {"voice_id": "D38z5RcWu1voky8WS1ja", "name": "Fin", "gender": "male", "style": "sailor"},
            "bella": {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female", "style": "soft"},
            "antoni": {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male", "style": "well-rounded"},
            "elli": {"voice_id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female", "style": "emotional"},
            "josh": {"voice_id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male", "style": "deep"},
            "arnold": {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "style": "crisp"},
            "adam": {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male", "style": "deep"},
            "sam": {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male", "style": "raspy"}
        }
        
        # Voice settings
        self.voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
        # Caption styles
        self.caption_styles = {
            "minimal": {
                "font": "Arial",
                "font_size": 48,
                "color": "white",
                "outline_color": "black",
                "outline_width": 2,
                "position": "bottom",
                "margin": 50
            },
            "bold": {
                "font": "Arial Black",
                "font_size": 56,
                "color": "white",
                "outline_color": "black",
                "outline_width": 3,
                "position": "center",
                "margin": 0
            },
            "colorful": {
                "font": "Arial",
                "font_size": 52,
                "color": "yellow",
                "outline_color": "black",
                "outline_width": 3,
                "position": "bottom",
                "margin": 60
            },
            "elegant": {
                "font": "Georgia",
                "font_size": 44,
                "color": "white",
                "outline_color": "gray",
                "outline_width": 1,
                "position": "bottom",
                "margin": 40
            }
        }
        
        # Check if ffmpeg is available
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _load_voice_storage(self) -> Dict[str, Any]:
        """Load previously created voice overs"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading voice storage: {e}")
        return {"voice_overs": [], "by_hash": {}}
    
    def _save_voice_storage(self):
        """Save voice overs to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.voice_storage, f, indent=2)
        except Exception as e:
            print(f"Error saving voice storage: {e}")
    
    def _generate_voice_hash(self, text: str, voice: str, language: str = "en") -> str:
        """Generate a hash for the voice over parameters"""
        voice_key = f"{text}_{voice}_{language}"
        return hashlib.md5(voice_key.encode()).hexdigest()
    
    def generate_voice_script(self, video_content: str, target_duration: int = 30, 
                            style: str = "conversational", period: str = None) -> Dict[str, Any]:
        """Generate a voice over script for video content"""
        try:
            # Create script generation task
            script_task = Task(
                description=f"""
                Erstelle ein Voice-Over Script für ein Video mit folgendem Inhalt:
                
                Video Inhalt: {video_content}
                Zieldauer: {target_duration} Sekunden
                Stil: {style}
                7 Cycles Periode: {period or 'Allgemein'}
                
                Das Script soll:
                1. Natürlich und flüssig klingen
                2. Zur visuellen Handlung passen
                3. Die richtige Länge für {target_duration} Sekunden haben
                4. Pausen für wichtige visuelle Momente einplanen
                5. Eine klare Struktur haben (Einleitung, Hauptteil, Schluss)
                
                Erstelle das Script im JSON-Format:
                {{
                    "script": "Der vollständige Voice-Over Text",
                    "segments": [
                        {{
                            "start_time": 0,
                            "end_time": 5,
                            "text": "Text für dieses Segment",
                            "emphasis": "normal/strong/soft"
                        }}
                    ],
                    "total_duration": {target_duration},
                    "word_count": "Anzahl der Wörter",
                    "speaking_rate": "Wörter pro Minute"
                }}
                """,
                expected_output="Ein strukturiertes Voice-Over Script im JSON-Format",
                agent=self.voice_agent
            )
            
            # Execute script generation
            crew = Crew(
                agents=[self.voice_agent],
                tasks=[script_task],
                verbose=True
            )
            
            script_result = crew.kickoff()
            
            # Parse the generated script
            try:
                script_data = json.loads(script_result.raw)
            except json.JSONDecodeError:
                # Fallback script
                script_data = {
                    "script": video_content[:200] + "...",
                    "segments": [
                        {
                            "start_time": 0,
                            "end_time": target_duration,
                            "text": video_content[:200] + "...",
                            "emphasis": "normal"
                        }
                    ],
                    "total_duration": target_duration,
                    "word_count": len(video_content.split()),
                    "speaking_rate": "150"
                }
            
            return {
                "success": True,
                "script": script_data,
                "message": "Voice-Over Script erfolgreich erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Voice-Over Scripts"
            }
    
    def generate_voice_over(self, text: str, voice: str = "bella", 
                          language: str = "en", model: str = "eleven_multilingual_v2",
                          output_format: str = "mp3_44100_128") -> Dict[str, Any]:
        """Generate voice over using ElevenLabs API"""
        try:
            if not self.elevenlabs_api_key:
                return {
                    "success": False,
                    "error": "No ElevenLabs API key",
                    "message": "ElevenLabs API-Schlüssel nicht konfiguriert"
                }
            
            # Check if voice over already exists
            voice_hash = self._generate_voice_hash(text, voice, language)
            
            if voice_hash in self.voice_storage.get("by_hash", {}):
                existing_voice = self.voice_storage["by_hash"][voice_hash]
                if os.path.exists(existing_voice["file_path"]):
                    return {
                        "success": True,
                        "voice_over": existing_voice,
                        "source": "existing",
                        "message": "Bestehende Voice-Over abgerufen"
                    }
            
            # Get voice ID
            voice_info = self.available_voices.get(voice, self.available_voices["bella"])
            voice_id = voice_info["voice_id"]
            
            # Prepare API request
            url = f"{self.elevenlabs_base_url}/text-to-speech/{voice_id}"
            
            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": self.voice_settings
            }
            
            headers = self.elevenlabs_headers.copy()
            headers["Accept"] = f"audio/{output_format.split('_')[0]}"
            
            # Make API request
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Save audio file
                audio_filename = f"voice_over_{voice}_{voice_hash[:8]}.mp3"
                audio_path = os.path.join(self.audio_output_dir, audio_filename)
                
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                
                # Get audio duration
                duration = self._get_audio_duration(audio_path)
                
                # Store voice over information
                voice_info = {
                    "id": voice_hash,
                    "text": text,
                    "voice": voice,
                    "voice_name": voice_info["name"],
                    "language": language,
                    "model": model,
                    "file_path": audio_path,
                    "file_url": f"/static/voice_overs/{audio_filename}",
                    "duration": duration,
                    "created_at": datetime.now().isoformat()
                }
                
                # Save to storage
                self.voice_storage["voice_overs"].append(voice_info)
                self.voice_storage["by_hash"][voice_hash] = voice_info
                self._save_voice_storage()
                
                return {
                    "success": True,
                    "voice_over": voice_info,
                    "source": "generated",
                    "message": f"Voice-Over mit {voice_info['name']} erstellt"
                }
            else:
                return {
                    "success": False,
                    "error": f"ElevenLabs API error: {response.status_code}",
                    "message": f"Fehler bei der ElevenLabs API: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen der Voice-Over"
            }
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file using ffmpeg"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return 0.0
        except Exception:
            return 0.0
    
    def generate_captions(self, audio_path: str, language: str = "en", 
                         style: str = "minimal", max_chars_per_line: int = 40) -> Dict[str, Any]:
        """Generate captions/subtitles from audio using speech recognition"""
        try:
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": "Audio file not found",
                    "message": "Audio-Datei nicht gefunden"
                }
            
            # Use OpenAI Whisper for transcription
            transcription_result = self._transcribe_audio(audio_path, language)
            
            if not transcription_result["success"]:
                return transcription_result
            
            segments = transcription_result["segments"]
            
            # Generate subtitle files
            subtitle_filename = f"subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create SRT file
            srt_path = os.path.join(self.subtitle_output_dir, f"{subtitle_filename}.srt")
            srt_content = self._create_srt_content(segments, max_chars_per_line)
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            # Create WebVTT file
            vtt_path = os.path.join(self.subtitle_output_dir, f"{subtitle_filename}.vtt")
            vtt_content = self._create_vtt_content(segments, max_chars_per_line)
            with open(vtt_path, 'w', encoding='utf-8') as f:
                f.write(vtt_content)
            
            # Create styled ASS file for burned-in subtitles
            ass_path = os.path.join(self.subtitle_output_dir, f"{subtitle_filename}.ass")
            ass_content = self._create_ass_content(segments, style, max_chars_per_line)
            with open(ass_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            return {
                "success": True,
                "captions": {
                    "srt_path": srt_path,
                    "vtt_path": vtt_path,
                    "ass_path": ass_path,
                    "segments": segments,
                    "language": language,
                    "style": style
                },
                "message": "Untertitel erfolgreich erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen der Untertitel"
            }
    
    def _transcribe_audio(self, audio_path: str, language: str) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            # Use OpenAI Whisper for transcription
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'file': audio_file,
                    'model': (None, 'whisper-1'),
                    'language': (None, language),
                    'response_format': (None, 'verbose_json'),
                    'timestamp_granularities[]': (None, 'word')
                }
                
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                
                # Process segments
                segments = []
                if 'words' in result:
                    # Group words into segments
                    current_segment = {
                        "start": 0,
                        "end": 0,
                        "text": ""
                    }
                    
                    for word in result['words']:
                        if current_segment["text"] and (word['start'] - current_segment["end"] > 0.5):
                            # New segment
                            segments.append(current_segment)
                            current_segment = {
                                "start": word['start'],
                                "end": word['end'],
                                "text": word['word']
                            }
                        else:
                            # Add to current segment
                            if not current_segment["text"]:
                                current_segment["start"] = word['start']
                            current_segment["end"] = word['end']
                            current_segment["text"] += " " + word['word'] if current_segment["text"] else word['word']
                    
                    if current_segment["text"]:
                        segments.append(current_segment)
                else:
                    # Fallback to simple segmentation
                    text = result.get('text', '')
                    duration = self._get_audio_duration(audio_path)
                    words = text.split()
                    words_per_segment = max(5, len(words) // 10)
                    
                    for i in range(0, len(words), words_per_segment):
                        segment_words = words[i:i+words_per_segment]
                        start_time = (i / len(words)) * duration
                        end_time = ((i + len(segment_words)) / len(words)) * duration
                        
                        segments.append({
                            "start": start_time,
                            "end": end_time,
                            "text": " ".join(segment_words)
                        })
                
                return {
                    "success": True,
                    "segments": segments,
                    "full_text": result.get('text', '')
                }
            else:
                return {
                    "success": False,
                    "error": f"Whisper API error: {response.status_code}",
                    "message": "Fehler bei der Transkription"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler bei der Audio-Transkription"
            }
    
    def _create_srt_content(self, segments: List[Dict], max_chars: int) -> str:
        """Create SRT subtitle content"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = self._seconds_to_srt_time(segment['start'])
            end_time = self._seconds_to_srt_time(segment['end'])
            text = self._wrap_text(segment['text'], max_chars)
            
            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
        
        return srt_content
    
    def _create_vtt_content(self, segments: List[Dict], max_chars: int) -> str:
        """Create WebVTT subtitle content"""
        vtt_content = "WEBVTT\n\n"
        
        for segment in segments:
            start_time = self._seconds_to_vtt_time(segment['start'])
            end_time = self._seconds_to_vtt_time(segment['end'])
            text = self._wrap_text(segment['text'], max_chars)
            
            vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"
        
        return vtt_content
    
    def _create_ass_content(self, segments: List[Dict], style: str, max_chars: int) -> str:
        """Create ASS subtitle content with styling"""
        style_info = self.caption_styles.get(style, self.caption_styles["minimal"])
        
        ass_content = f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_info['font']},{style_info['font_size']},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{style_info['outline_width']},0,2,10,10,{style_info['margin']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        for segment in segments:
            start_time = self._seconds_to_ass_time(segment['start'])
            end_time = self._seconds_to_ass_time(segment['end'])
            text = self._wrap_text(segment['text'], max_chars).replace('\n', '\\N')
            
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
        
        return ass_content
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        milliseconds = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        milliseconds = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    def _wrap_text(self, text: str, max_chars: int) -> str:
        """Wrap text to maximum characters per line"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + (1 if current_line else 0)
            
            if current_length + word_length <= max_chars:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)
    
    def add_voice_over_to_video(self, video_path: str, audio_path: str, 
                               volume: float = 1.0, fade_in: float = 0.5, 
                               fade_out: float = 0.5) -> Dict[str, Any]:
        """Add voice over audio to video"""
        try:
            if not self.ffmpeg_available:
                return {
                    "success": False,
                    "error": "FFmpeg not available",
                    "message": "FFmpeg ist nicht verfügbar"
                }
            
            if not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": "Video file not found",
                    "message": "Video-Datei nicht gefunden"
                }
            
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": "Audio file not found",
                    "message": "Audio-Datei nicht gefunden"
                }
            
            # Generate output filename
            output_filename = f"video_with_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(self.video_output_dir, output_filename)
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-filter_complex', f'[1:a]volume={volume},afade=in:st=0:d={fade_in},afade=out:st=-{fade_out}:d={fade_out}[voice];[0:a][voice]amix=inputs=2:duration=first[out]',
                '-map', '0:v',
                '-map', '[out]',
                '-shortest',
                output_path
            ]
            
            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg error: {result.stderr}",
                    "message": "Fehler beim Hinzufügen der Voice-Over"
                }
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": f"/static/videos_with_voice/{output_filename}",
                "message": "Voice-Over erfolgreich hinzugefügt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Hinzufügen der Voice-Over zum Video"
            }
    
    def add_captions_to_video(self, video_path: str, subtitle_path: str, 
                             burn_in: bool = True, style: str = "minimal") -> Dict[str, Any]:
        """Add captions/subtitles to video"""
        try:
            if not self.ffmpeg_available:
                return {
                    "success": False,
                    "error": "FFmpeg not available",
                    "message": "FFmpeg ist nicht verfügbar"
                }
            
            if not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": "Video file not found",
                    "message": "Video-Datei nicht gefunden"
                }
            
            if not os.path.exists(subtitle_path):
                return {
                    "success": False,
                    "error": "Subtitle file not found",
                    "message": "Untertitel-Datei nicht gefunden"
                }
            
            # Generate output filename
            output_filename = f"video_with_captions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(self.video_output_dir, output_filename)
            
            if burn_in:
                # Burn subtitles into video
                if subtitle_path.endswith('.ass'):
                    # Use ASS file directly
                    cmd = [
                        'ffmpeg',
                        '-y',
                        '-i', video_path,
                        '-vf', f"ass='{subtitle_path}'",
                        '-c:a', 'copy',
                        output_path
                    ]
                else:
                    # Convert to ASS for styling
                    style_info = self.caption_styles.get(style, self.caption_styles["minimal"])
                    cmd = [
                        'ffmpeg',
                        '-y',
                        '-i', video_path,
                        '-vf', f"subtitles={subtitle_path}:force_style='FontName={style_info['font']},FontSize={style_info['font_size']},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline={style_info['outline_width']},MarginV={style_info['margin']}'",
                        '-c:a', 'copy',
                        output_path
                    ]
            else:
                # Add subtitles as a separate stream
                cmd = [
                    'ffmpeg',
                    '-y',
                    '-i', video_path,
                    '-i', subtitle_path,
                    '-c', 'copy',
                    '-c:s', 'mov_text' if output_path.endswith('.mp4') else 'srt',
                    '-metadata:s:s:0', 'language=eng',
                    output_path
                ]
            
            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg error: {result.stderr}",
                    "message": "Fehler beim Hinzufügen der Untertitel"
                }
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": f"/static/videos_with_voice/{output_filename}",
                "burn_in": burn_in,
                "message": "Untertitel erfolgreich hinzugefügt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Hinzufügen der Untertitel zum Video"
            }
    
    def process_video_with_voice_and_captions(self, video_path: str, script_text: str,
                                            voice: str = "bella", language: str = "en",
                                            caption_style: str = "minimal", 
                                            burn_in_captions: bool = True) -> Dict[str, Any]:
        """Complete pipeline: generate voice over, create captions, and add both to video"""
        try:
            # Step 1: Generate voice over
            voice_result = self.generate_voice_over(script_text, voice, language)
            
            if not voice_result["success"]:
                return voice_result
            
            audio_path = voice_result["voice_over"]["file_path"]
            
            # Step 2: Generate captions from audio
            caption_result = self.generate_captions(audio_path, language, caption_style)
            
            if not caption_result["success"]:
                return caption_result
            
            subtitle_path = caption_result["captions"]["ass_path"] if burn_in_captions else caption_result["captions"]["srt_path"]
            
            # Step 3: Add voice over to video
            voice_video_result = self.add_voice_over_to_video(video_path, audio_path)
            
            if not voice_video_result["success"]:
                return voice_video_result
            
            video_with_voice = voice_video_result["output_path"]
            
            # Step 4: Add captions to video
            final_result = self.add_captions_to_video(video_with_voice, subtitle_path, 
                                                    burn_in_captions, caption_style)
            
            if not final_result["success"]:
                return final_result
            
            # Clean up intermediate file
            if os.path.exists(video_with_voice) and video_with_voice != final_result["output_path"]:
                os.remove(video_with_voice)
            
            return {
                "success": True,
                "final_video": {
                    "path": final_result["output_path"],
                    "url": final_result["output_url"]
                },
                "voice_over": voice_result["voice_over"],
                "captions": caption_result["captions"],
                "message": "Video mit Voice-Over und Untertiteln erfolgreich erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler bei der Videoverarbeitung"
            }
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices"""
        return {
            "success": True,
            "voices": self.available_voices,
            "elevenlabs_configured": bool(self.elevenlabs_api_key)
        }
    
    def get_caption_styles(self) -> Dict[str, Any]:
        """Get available caption styles"""
        return {
            "success": True,
            "styles": self.caption_styles
        }
    
    def get_voice_overs(self) -> Dict[str, Any]:
        """Get all generated voice overs"""
        try:
            return {
                "success": True,
                "voice_overs": self.voice_storage.get("voice_overs", []),
                "count": len(self.voice_storage.get("voice_overs", []))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der Voice-Overs"
            }