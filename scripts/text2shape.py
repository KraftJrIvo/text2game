import torch
from diffusers import ShapEPipeline, DiffusionPipeline
from diffusers.utils import export_to_gif, export_to_obj

def generate_shape(prompt, out):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    repo = "openai/shap-e"
    pipe = DiffusionPipeline.from_pretrained(repo, torch_dtype=torch.float16)
    pipe = pipe.to(device)
    guidance_scale = 15.0
    images = pipe(prompt, guidance_scale=guidance_scale, num_inference_steps=64, frame_size=256, output_type="mesh").images
    export_to_obj(images[0], out)
