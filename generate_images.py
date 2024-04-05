import glob
import io
import json
import os
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import ollama
import websocket
import yaml
from PIL import Image

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())


def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())


def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(
        "http://{}/view?{}".format(server_address, url_values)
    ) as response:
        return response.read()


def get_history(prompt_id):
    with urllib.request.urlopen(
        "http://{}/history/{}".format(server_address, prompt_id)
    ) as response:
        return json.loads(response.read())


def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)["prompt_id"]
    output_images = {}
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["prompt_id"] == prompt_id:
                    if data["node"] is None:
                        break  # Execution is done
                    else:
                        current_node = data["node"]
                        print("Received data for", prompt[data["node"]]["class_type"])
        else:
            if prompt[current_node]["class_type"] == "SaveImageWebsocket":
                images_output = output_images.get(current_node, [])
                images_output.append(out[8:])
                output_images[current_node] = images_output

    return output_images


def process(filepath, image_prompt, turbo=False):
    if turbo:
        with open("workflow_api_turbo.json", "r") as file:
            prompt_text = file.read()

        prompt_api = json.loads(prompt_text)

        # Set positive prompt
        prompt_api["6"]["inputs"]["text"] = image_prompt

        # Set negative prompt
        prompt_api["7"]["inputs"]["text"] = "nsfw, text, watermark"

    else:
        with open("workflow_api.json", "r") as file:
            prompt_text = file.read()

        prompt_api = json.loads(prompt_text)

        # Set positive prompt
        prompt_api["6"]["inputs"]["text"] = prompt_api["15"]["inputs"]["text"] = (
            image_prompt
        )

        # Set negative prompt
        prompt_api["7"]["inputs"]["text"] = prompt_api["16"]["inputs"]["text"] = (
            "nsfw, text, watermark"
        )

    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    images = get_images(ws, prompt_api)
    ws.close()

    for node_id in images:
        for image_data in images[node_id]:
            image = Image.open(io.BytesIO(image_data))
            image.save(filepath, quality=95, optimize=True)


def run_ollama(prompt):
    ollama.pull("llama2")
    response = ollama.generate(model="llama2", prompt=prompt)["response"]
    return response.strip()


def main():
    for filepath in glob.iglob("src/_data/talents/*.yaml"):
        class_name = Path(filepath).stem
        print("Processing class:", class_name)
        with open(filepath, "r") as file:
            contents = yaml.safe_load(file)
            for name, entry in contents.items():
                filepath = "src/assets/generated_images/" + name + ".jpg"
                if os.path.exists(filepath):
                    continue

                power_desc = name
                power_desc += "\nType: " + class_name + ", " + entry["type"]
                power_desc += "\nDescription: " + entry["brief"]
                if "traits" in entry:
                    power_desc += "\nTraits: " + ", ".join(entry["traits"])
                if "tags" in entry:
                    for tag_name in entry["tags"]:
                        power_desc += "\n" + tag_name + ": " + entry["tags"][tag_name]
                power_desc += "\nEffect: " + entry["effect"]
                if "fluff" in entry:
                    power_desc += "\nFluff: " + entry["fluff"]
                print("Processing power:", power_desc)

                prompt1 = (
                    "The following is an ability in a medieval fantasy tabletop rpg system. Describe an image that shows this ability in action. The image should NOT focus on a person. Describe the focus of the image, then describe the background of the image, then describe the emotions and tone of the image. The image should NOT focus on a person. Your description should be formatted as a single very short paragraph of natural english writing. Be brief, be concise, and only include details the viewer can see with their eyes. Respond only with the description, nothing else.\n\n"
                    + power_desc
                )
                description = run_ollama(prompt1)
                image_prompt = "D&D, anime style, digital art. " + description
                print("Generated Prompt:", image_prompt)

                process(filepath, image_prompt)


if __name__ == "__main__":
    main()
