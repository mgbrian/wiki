import json
from typing import Optional

from pydantic import BaseModel, ValidationError

from llm.assistants import Assistant
from llm import models
from utils import read_text_file

MAX_PROMPT_RETRIES = 3

page_image_parser = Assistant(
    name="Page Image Parser",
    model=models.gemini_1_5_pro,
    system_template=read_text_file("prompts/page_parser.md"),
)


class ParserResponseModel(BaseModel):
    text: Optional[str]
    summary: Optional[str]
    description: str
    requestNextPage: Optional[bool] = None


def parse_page_image(page_image):
    """Parse a page and return its contents and other useful metadata.

    Args:
        page_image: image.Image - Image object representing the page.

    Returns:
        dict: A dictionary with the above metadata.
    """
    # To prevent errors caused by presence of an alpha channel.
    # TODO: We should probably do this at the LLM API level
    page_image.image = page_image.image.convert('RGB')
    errors_so_far = 0

    prompt = 'Please process the given image as requested.'
    while errors_so_far <= MAX_PROMPT_RETRIES:
        response_json = page_image_parser.prompt(
            prompt,
            images=[page_image],
            response_format='json',
            conversation=None,
            system_prompt_context={}
        )

        try:
            response_dict = json.loads(response_json)
            parsed_json = json.loads(response_json)
            validated_data = ParserResponseModel(**parsed_json)
            print("Validated Data:", validated_data)

            return validated_data.dict()

        except (json.JSONDecodeError, ValidationError) as e:
            print("Error:", e)
            print('')
            print("Response:")
            print("---------")
            print(response_json)
            errors_so_far += 1

            if errors_so_far == MAX_PROMPT_RETRIES:
                raise

            prompt = (
                'Please process the given image as requested. '
                'Your last response below resulted in the following error: '
                '\nResponse: \n'
                f'{response_json}'
                '\nError:{e} \n'
            )


if __name__ == '__main__':
    # TEST: python parser.py <url to page image>
    from image import Image
    import sys
    import os

    if len(sys.argv) < 2:
        print("Please supply a path to the image you want to parse.")
        sys.exit()

    image_url = sys.argv[1]
    if not os.path.isfile(image_url):
        print(f"Please provide a valid filepath. >> {image_url} << is not.")
        sys.exit()

    page_image = Image(image_url)
    result = parse_page_image(page_image)

    print(result)
