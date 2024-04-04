import os
import random
import sys
from typing import Sequence, Mapping, Any, Union
import torch

import glob
import hashlib
import numpy as np
import ollama
from pathlib import Path
import yaml

from PIL import Image


def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    """Returns the value at the given index of a sequence or mapping.

    If the object is a sequence (like list or string), returns the value at the given index.
    If the object is a mapping (like a dictionary), returns the value at the index-th key.

    Some return a dictionary, in these cases, we look for the "results" key

    Args:
        obj (Union[Sequence, Mapping]): The object to retrieve the value from.
        index (int): The index of the value to retrieve.

    Returns:
        Any: The value at the given index.

    Raises:
        IndexError: If the index is out of bounds for the object and the object is not a mapping.
    """
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]


def find_path(name: str, path: str = None) -> str:
    """
    Recursively looks at parent folders starting from the given path until it finds the given name.
    Returns the path as a Path object if found, or None otherwise.
    """
    # If no path is given, use the current working directory
    if path is None:
        path = os.getcwd()

    # Check if the current directory contains the name
    if name in os.listdir(path):
        path_name = os.path.join(path, name)
        print(f"{name} found: {path_name}")
        return path_name

    # Get the parent directory
    parent_directory = os.path.dirname(path)

    # If the parent directory is the same as the current directory, we've reached the root and stop the search
    if parent_directory == path:
        return None

    # Recursively call the function with the parent directory
    return find_path(name, parent_directory)


def add_comfyui_directory_to_sys_path() -> None:
    """
    Add 'ComfyUI' to the sys.path
    """
    # comfyui_path = find_path("ComfyUI")
    comfyui_path = "C:/Users/Rory/Desktop/Misc/StabilityMatrix/Data/Packages/ComfyUI"
    if comfyui_path is not None and os.path.isdir(comfyui_path):
        sys.path.append(comfyui_path)
        print(f"'{comfyui_path}' added to sys.path")


def add_extra_model_paths() -> None:
    """
    Parse the optional extra_model_paths.yaml file and add the parsed paths to the sys.path.
    """
    from main import load_extra_path_config

    # extra_model_paths = find_path("extra_model_paths.yaml")
    extra_model_paths = "C:/Users/Rory/Desktop/Misc/StabilityMatrix/Data/Packages/ComfyUI/extra_model_paths.yaml"

    if extra_model_paths is not None:
        load_extra_path_config(extra_model_paths)
    else:
        print("Could not find the extra_model_paths config file.")


add_comfyui_directory_to_sys_path()
add_extra_model_paths()

from nodes import (
    LatentUpscale,
    NODE_CLASS_MAPPINGS,
    KSampler,
    CLIPTextEncode,
    CheckpointLoaderSimple,
    EmptyLatentImage,
    SaveImage,
    VAEDecode,
)


def process(filepath, prompt):
    with torch.inference_mode():
        emptylatentimage = EmptyLatentImage()
        emptylatentimage_5 = emptylatentimage.generate(
            width=512, height=512, batch_size=1
        )

        checkpointloadersimple = CheckpointLoaderSimple()
        checkpointloadersimple_16 = checkpointloadersimple.load_checkpoint(
            ckpt_name="dreamshaperXL_v21TurboDPMSDE.safetensors"
        )

        cliptextencode = CLIPTextEncode()
        cliptextencode_6 = cliptextencode.encode(
            text=prompt,
            clip=get_value_at_index(checkpointloadersimple_16, 1),
        )

        cliptextencode_7 = cliptextencode.encode(
            text="nsfw, bad hands, text, watermark, low quality, person, human, man, woman, 1boy, 1girl",
            clip=get_value_at_index(checkpointloadersimple_16, 1),
        )

        ksampler = KSampler()
        vaedecode = VAEDecode()
        saveimage = SaveImage()
        latentupscale = LatentUpscale()

        ksampler_3 = ksampler.sample(
            seed=random.randint(1, 2**64),
            steps=8,
            cfg=2,
            sampler_name="dpmpp_sde",
            scheduler="normal",
            denoise=1,
            model=get_value_at_index(checkpointloadersimple_16, 0),
            positive=get_value_at_index(cliptextencode_6, 0),
            negative=get_value_at_index(cliptextencode_7, 0),
            latent_image=get_value_at_index(emptylatentimage_5, 0),
        )

        latentupscale_10 = latentupscale.upscale(
            upscale_method="nearest-exact",
            width=768,
            height=768,
            crop="disabled",
            samples=get_value_at_index(ksampler_3, 0),
        )

        ksampler_11 = ksampler.sample(
            seed=random.randint(1, 2**64),
            steps=5,
            cfg=2,
            sampler_name="dpmpp_sde",
            scheduler="simple",
            denoise=0.5,
            model=get_value_at_index(checkpointloadersimple_16, 0),
            positive=get_value_at_index(cliptextencode_6, 0),
            negative=get_value_at_index(cliptextencode_7, 0),
            latent_image=get_value_at_index(latentupscale_10, 0),
        )

        vaedecode_13 = vaedecode.decode(
            samples=get_value_at_index(ksampler_11, 0),
            vae=get_value_at_index(checkpointloadersimple_16, 2),
        )

        images = get_value_at_index(vaedecode_13, 0)
        i = 255. * images[0].cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        img.save(filepath, quality=95, optimize=True)


def run_ollama(prompt):
    ollama.pull('llama2')
    response = ollama.generate(model='llama2', prompt=prompt)['response']
    return response.strip()


def main():
    for filepath in glob.iglob('src/_data/talents/*.yaml'):
        class_name = Path(filepath).stem
        print('Processing class:', class_name)
        with open(filepath, 'r') as file:
            contents = yaml.safe_load(file)
            for name, entry in contents.items():
                filepath = 'src/assets/generated_images/' + name + '.jpg'
                if os.path.exists(filepath):
                    continue

                print('Processing power:', name)

                prompt1 = 'The following is an ability in a medieval fantasy tabletop rpg system. Describe an image that shows this ability in action. The image should NOT focus on a person. Describe the focus of the image, then describe the background of the image, then describe the emotions and tone of the image. The image should NOT focus on a person. Your description should be formatted as a single very short paragraph of natural english writing. Be brief, be concise, and only include details the viewer can see with their eyes. Respond only with the description, nothing else.\n\n'
                prompt1 += name + "\nType: " + class_name + ", " + entry['type'] + "\nDescription: " + entry['brief'] + "\nEffect: " + entry['effect']
                description = run_ollama(prompt1)
                # print('Generated Description:', description)

                # prompt2 = 'Write a image generator prompt that matches the following description. The prompt should be formatted as a comma-separated list of about a dozen tags, where each tag is something you can see in the image. Respond only with the prompt, nothing else.\n\n' + name + ' (' + class_name + ')' + '\n' + description
                # image_prompt = run_ollama(prompt2)
                image_prompt = 'D&D, anime style, digital art, high quality, landscape, wallpaper, distant camera. ' + description
                print('Generated Prompt:', image_prompt)

                process(filepath, image_prompt)


if __name__ == "__main__":
    main()
