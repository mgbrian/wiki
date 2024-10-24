import json
from typing import Optional

from pydantic import BaseModel, ValidationError

from llm.assistants import Assistant
from llm import models
from utils import read_text_file


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
    errors_so_far = 0

    prompt = 'Please process the given image as requested.'
    while errors_so_far <= 3:
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
            errors_so_far += 1
            prompt = (
                'Please process the given image as requested. '
                'Your last response below resulted in the following error: '
                '\nResponse: \n'
                f'{response_json}'
                '\nError:{e} \n'
            )
