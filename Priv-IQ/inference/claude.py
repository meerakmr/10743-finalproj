"""
Usage:
python claude.py --priviq_path /path/to/privIQ --anthropic_api_key <api_key>
python inference/claude.py --priviq_path . --anthropic_api_key $ANTHROPIC_API_KEY


"""
import os
import argparse
import anthropic
from utils import evaluate_on_priviq, encode_image


class Claude:
    def __init__(self, api_key, 
                 model="claude-sonnet-4-20250514", temperature=0.0,
                 max_tokens=512, system=None):
        self.model = model
        self.client = anthropic.Anthropic(
            api_key=api_key,
        )
        self.system = system
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def get_response(self, image_path, prompt="What's in this image?"):
        base64_image = encode_image(image_path)
        image_format = "png" if image_path.endswith('.png') else "jpeg"

        messages = []
        content = [
            {
                "type": "text",
                "text": prompt,
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": f"image/{image_format}",
                    "data": base64_image,
                }
            }

        ]

        messages.append({
            "role": "user",
            "content": content,
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if self.system:
            payload["system"] = self.system

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(**payload)
                response_text = response.content[0].text
                return response_text.strip()
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Retry {attempt + 1}/{max_retries - 1}: {type(e).__name__}")
                    import time
                    time.sleep(2 ** attempt)  # exponential backoff
                else:
                    raise


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--priviq_path",
        type=str,
        default="/path/to/privIQ",
        help="Download privIQ.zip and `unzip privIQ.zip` and change the path here",
    )
    parser.add_argument(
        "--result_path",
        type=str,
        default="results",
    )
    parser.add_argument(
        "--anthropic_api_key", type=str, default=None,
        help="refer to https://docs.anthropic.com/claude/reference/getting-started-with-the-api"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Claude model name",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = arg_parser()

    # prepare the model
    if args.anthropic_api_key:
        ANTHROPIC_API_KEY = args.anthropic_api_key
    else:
        ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    if ANTHROPIC_API_KEY is None:
        raise ValueError("Please set the ANTHROPIC_API_KEY environment variable or pass it as an argument")
    
    model = Claude(ANTHROPIC_API_KEY, model=args.model_name)

    # evalute on privIQ
    evaluate_on_priviq(args, model)