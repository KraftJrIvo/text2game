import sys
import os
from diffusers import AudioLDM2Pipeline
import torch
import scipy

from pydub import AudioSegment
from pydub.silence import split_on_silence

def calculate_silence_threshold(audio, initial_thresh=-40, step=5, min_parts=5):
    silence_thresh = initial_thresh
    chunks = []
    counter = 0
    while len(chunks) < min_parts and counter < 100:
        chunks = split_on_silence(audio, min_silence_len=100, silence_thresh=silence_thresh)
        silence_thresh += step
        counter += 1
    return silence_thresh

def split_wav(file_path, output_folder, min_silence_len=100, save_all=True):
    if save_all:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
    audio = AudioSegment.from_wav(file_path)
    silence_thresh = calculate_silence_threshold(audio)
    chunks = split_on_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    for i, chunk in enumerate(chunks):
        if save_all:
            output_file_path = os.path.join(output_folder, f"{i}.wav")
            chunk.export(output_file_path, format="wav")
        else:
            chunk.export(file_path, format="wav")
            break

def generate_audio(prompt, out_path=None, length=10.0):
    repo_id = "cvssp/audioldm2-large"
    pipe = AudioLDM2Pipeline.from_pretrained(repo_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda")
    print('GENERATING AUDIO: ', prompt)
    audio = pipe(prompt, num_inference_steps=200, audio_length_in_s=length).audios[0]
    if out_path is not None:
        scipy.io.wavfile.write(out_path, rate=16000, data=audio)
    return audio

def generate_short_audio(prompt, out_path, save_all=True):
    audio = generate_audio(prompt, out_path)
    if save_all:
        outdir = out_path.replace('.wav', '')
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        split_wav(out_path, outdir, 100, save_all)
    else:
        split_wav(out_path, '', 100, save_all)
