import os
import json
import base64
from tqdm import tqdm


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    

def evaluate_on_priviq(args, model):
    if os.path.exists(args.result_path) is False:
        os.makedirs(args.result_path)
    results_path = os.path.join(args.result_path, f"{args.model_name}.json")
    image_folder = os.path.join(args.priviq_path, "images")
    meta_data = os.path.join(args.priviq_path, f"priv-IQ.json")

    with open(meta_data, 'r') as f:
        data = json.load(f)

    results = {}

    for id in tqdm(data.keys(), desc="Processing images"):
        imagename = data[id]['imagename']
        img_path = os.path.join(image_folder, imagename)
        prompt = data[id]['question']
        response = model.get_response(img_path, prompt)
        results[id] = response        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=4)