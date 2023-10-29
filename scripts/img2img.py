import sys
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline, AutoPipelineForImage2Image
import torch
import cv2
import numpy as np
# Importing Required Modules
from rembg import remove
from PIL import Image

def generate_pixelart(prompt, image, size = (1024, 1024)):
    pipeline = StableDiffusionXLPipeline.from_single_file("/home/ivan/onno/stable-diffusion-webui/models/Stable-diffusion/sd_xl_base_1.0.safetensors", torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("cuda")
    
    pipeline = AutoPipelineForImage2Image.from_pipe(pipeline).to("cuda")
    #pipeline.load_lora_weights("/home/ivan/onno/stable-diffusion-webui/models/Lora/pixel-art-xl-v1.1.safetensors")
    pipeline.enable_sequential_cpu_offload()
    image = pipeline(image=image, prompt=prompt, original_size=size, target_size=size, strength=0.4, guidance_scale=10.5, num_inference_steps=40).images[0]

    refiner = StableDiffusionXLImg2ImgPipeline.from_single_file("/home/ivan/onno/stable-diffusion-webui/models/Stable-diffusion/sd_xl_refiner_1.0.safetensors", torch_dtype=torch.float16, use_safetensors=True, variant="fp16").to("cuda")
    refiner.enable_sequential_cpu_offload()
    image = refiner(prompt=prompt, num_inference_steps=40, denoising_start=0.8, image=image,).images[0]

    image.save('test10.png')
    return image

generate_pixelart('digital art of a two masculine and beautiful men in baseball caps joking together in a sunlit summer forest, detailed, backlit, godrays', Image.open('/home/ivan/Downloads/Selection_007.png'))
