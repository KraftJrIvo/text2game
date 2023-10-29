import sys
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
import torch
import cv2
import numpy as np
# Importing Required Modules
from rembg import remove
from PIL import Image

def extract_biggest_object(image, alpha_threshold=200):
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGRA)
    bgr = image[:, :, :3]
    alpha = image[:, :, 3]
    _, binary_alpha = cv2.threshold(alpha, alpha_threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary_alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    mask = np.zeros_like(alpha)
    cv2.drawContours(mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    masked_image = cv2.bitwise_and(bgr, bgr, mask=mask)
    masked_alpha = cv2.bitwise_and(alpha, alpha, mask=mask)
    biggest_object = np.concatenate((masked_image[y:y+h, x:x+w], np.expand_dims(masked_alpha[y:y+h, x:x+w], axis=2)), axis=2)
    return Image.fromarray(cv2.cvtColor(biggest_object, cv2.COLOR_BGRA2RGBA))

def generate_pixelart(prompt, out_path=None, size = (1024, 1024), negative_prompt='', iters = 25, uselora = True):
    pipeline = StableDiffusionXLPipeline.from_single_file("/home/ivan/onno/stable-diffusion-webui/models/Stable-diffusion/sd_xl_base_1.0.safetensors", torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("cuda")
    if uselora:    
        pipeline.load_lora_weights("/home/ivan/onno/stable-diffusion-webui/models/Lora/pixel-art-xl-v1.1.safetensors")
    #pipeline.enable_sequential_cpu_offload()
    pipeline.enable_model_cpu_offload()
    image = pipeline(prompt=prompt, negative_prompt=negative_prompt, original_size=size, target_size=size, width=size[0], height=size[1], num_inference_steps=iters).images[0]
    if out_path is not None:
        image.save(out_path)
    return image

def generate_panorama(prompt, out_path=None):
    specific_prompt = 'skybox, panorama, detailed, ' + prompt
    negative_prompt = 'noise, artifacts'
    size = (1344, 768)
    pano = generate_pixelart(specific_prompt, out_path, size, negative_prompt, 50, False)
    return pano

def generate_sprite(prompt, out_path=None, size = (1024, 1024)):
    specific_prompt = 'side-view, one single sprite, flat white background, detailed, centered, ' + prompt
    negative_prompt = 'noise, artifacts, shadow'
    image = generate_pixelart(specific_prompt, None, size, negative_prompt)
    image = remove(image)
    sprite = extract_biggest_object(image)
    if out_path is not None:
        sprite.save(out_path)
    return sprite
