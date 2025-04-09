import os
import shutil
from moviepy.editor import VideoFileClip, AudioFileClip
import speech_recognition as sr
from difflib import SequenceMatcher
from pytube import YouTube
import tempfile
from typing import Optional, Tuple, List
import wave
import contextlib
import math

def download_youtube_video(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Download YouTube video and return tuple of (local path, temp directory)
    Returns (None, None) if download fails
    """
    temp_dir = None
    try:
        yt = YouTube(url, on_progress_callback=lambda stream, chunk, bytes_remaining: 
            print(f"Downloading... {(1 - bytes_remaining / stream.filesize) * 100:.1f}%"))
        
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            raise Exception("No suitable video stream found")
            
        temp_dir = tempfile.mkdtemp()
        print(f"Downloading: {yt.title}...")
        video_path = stream.download(output_path=temp_dir)
        return video_path, temp_dir
        
    except Exception as e:
        print(f"Error downloading YouTube video: {str(e)}")
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None, None

def extract_audio(video_path: str, audio_path: str) -> Optional[str]:
    """Extract audio from video file using moviepy"""
    video = None
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        if audio is None:
            raise Exception("No audio track found in video")
        audio.write_audiofile(audio_path)
        return audio_path
    except Exception as e:
        print(f"Error extracting audio: {str(e)}")
        return None
    finally:
        if video:
            try:
                video.close()
            except:
                pass

def get_audio_duration(audio_path: str) -> float:
    """Get the duration of an audio file in seconds"""
    with contextlib.closing(wave.open(audio_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        return duration

def split_audio(audio_path: str, chunk_duration: int = 60) -> List[str]:
    """Split audio file into chunks of specified duration"""
    chunks = []
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        num_chunks = math.ceil(duration / chunk_duration)
        
        for i in range(num_chunks):
            start_time = i * chunk_duration
            end_time = min((i + 1) * chunk_duration, duration)
            
            chunk_path = audio_path.replace('.wav', f'_chunk_{i}.wav')
            chunk = audio.subclip(start_time, end_time)
            chunk.write_audiofile(chunk_path)
            chunks.append(chunk_path)
            
        audio.close()
        return chunks
    except Exception as e:
        print(f"Error splitting audio: {str(e)}")
        return []

def transcribe_audio_chunks(chunks: List[str]) -> str:
    """Transcribe multiple audio chunks and combine results"""
    recognizer = sr.Recognizer()
    full_text = []
    
    for i, chunk_path in enumerate(chunks):
        try:
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            with sr.AudioFile(chunk_path) as source:
                recognizer.adjust_for_ambient_noise(source)
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                full_text.append(text)
        except sr.UnknownValueError:
            print(f"Could not understand audio in chunk {i+1}")
        except sr.RequestError as e:
            print(f"Error processing chunk {i+1}: {e}")
        except Exception as e:
            print(f"Unexpected error in chunk {i+1}: {str(e)}")
        finally:
            # Clean up chunk file
            try:
                os.remove(chunk_path)
            except:
                pass
    
    return " ".join(full_text)

def compare_texts(original: str, transcribed: str) -> float:
    """Compare two texts and return accuracy score"""
    if not original or not transcribed:
        return 0.0
    return SequenceMatcher(None, original.lower(), transcribed.lower()).ratio()

def process_video_file(video_path: str) -> Optional[str]:
    """Process a single video file and return transcript"""
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return None

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join("output", f"{base_name}_audio.wav")
    transcript_path = os.path.join("output", f"{base_name}_transcript.txt")

    try:
        print(f"\nProcessing: {os.path.basename(video_path)}")
        print("Extracting audio...")
        
        if not extract_audio(video_path, audio_path):
            print("Failed to extract audio")
            return None

        print("Splitting audio into chunks...")
        chunks = split_audio(audio_path)
        if not chunks:
            print("Failed to split audio")
            return None

        print(f"Processing {len(chunks)} audio chunks...")
        transcribed_text = transcribe_audio_chunks(chunks)
        
        if not transcribed_text:
            print("No text was transcribed")
            return None

        # Save transcript
        try:
            with open(transcript_path, "w", encoding='utf-8') as f:
                f.write(transcribed_text)
        except Exception as e:
            print(f"Error saving transcript: {str(e)}")
            return None

        print("\n=== Transcript ===")
        print(transcribed_text)
        print("==================\n")
        
        return transcribed_text

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return None
    finally:
        # Cleanup audio file
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass

def main():
    try:
        # Create directories if they don't exist
        os.makedirs("input", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        # Get all MP4 files in input folder
        video_files = [f for f in os.listdir("input") if f.lower().endswith('.mp4')]
        
        if not video_files:
            print("No MP4 files found in input folder")
            return

        print(f"Found {len(video_files)} video(s) to process")
        
        successful = 0
        for video_file in video_files:
            video_path = os.path.join("input", video_file)
            if process_video_file(video_path):
                successful += 1

        print(f"\nProcessing complete: {successful}/{len(video_files)} videos processed successfully!")

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
