# 🎬 Video-to-Text Transcript Generator 📝

Ever wished you could get the **entire transcript of a video** without manually typing it out?  
This project does exactly that — turning any video with spoken audio into **clean, readable text** using Python and speech processing libraries.

---

## 🔍 What It Does

This tool:
1. Extracts audio from a video file 🎥🔊  
2. Converts audio to a format suitable for speech recognition 🔄  
3. Transcribes the spoken content to text using Google’s Speech API 💬  
4. Saves the full transcript in a `.txt` file 📄  

> Perfect for content creators, students, researchers, and anyone tired of typing!

---

## 📦 Requirements

Install all dependencies using:
```bash
pip install moviepy==1.0.3
pip install SpeechRecognition==3.8.1
pip install pydub==0.25.1
