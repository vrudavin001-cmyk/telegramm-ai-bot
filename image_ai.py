import os
import io

from huggingface_hub import InferenceClient


HF_TOKEN = os.environ.get(
    "HF_TOKEN"
)


image_client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN
)


IMAGE_MODEL = (
    "black-forest-labs/FLUX.1-schnell"
)


EDIT_MODEL = (
    "Qwen/Qwen-Image-Edit"
)


def generate_image(
    prompt,
    filename
):

    try:

        image = image_client.text_to_image(

            prompt,

            model=IMAGE_MODEL
        )

        image.save(
            filename
        )

        return True

    except Exception as e:

        print(
            "IMAGE GENERATION ERROR:",
            e
        )

        return False


def edit_image(
    image_bytes,
    prompt,
    filename
):

    try:

        image = image_client.image_to_image(

            image_bytes,

            prompt=prompt,

            model=EDIT_MODEL
        )

        image.save(
            filename
        )

        return True

    except Exception as e:

        print(
            "IMAGE EDIT ERROR:",
            e
        )

        return False
