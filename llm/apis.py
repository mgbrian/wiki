import json
import os
import time

import requests

import env

class LLMAPIException(Exception):
    """Generic exception type for LLM API issues."""
    pass


class BaseAPI():
    """Base class for LLM APIs."""

    def __init__(self, name):
        self.name = name

    def generate_message_history(self, messages=None):
       raise NotImplementedError()

    def run_prompt(self, *args, **kwargs):
        raise NotImplementedError()


class OpenAIAPI(BaseAPI):
    """Interface to the OpenAI API."""

    ACCEPTABLE_MESSAGE_ROLES = {'assistant', 'user'}
    INCORRECT_MESSAGE_ROLE_MESSAGE = (
        f'Provided role is not an acceptable value. Must be one of: '
        f'{ACCEPTABLE_MESSAGE_ROLES}.'
    )

    def __init__(self, name='OpenAI'):
        from openai import OpenAI
        import tiktoken

        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.name = name
        self._tiktoken_encoding_for_model = tiktoken.encoding_for_model

    @property
    def available(self):
        try:
            _ = self.list_models()
            return True

        except Exception:
            return False

    def list_models(self):
        return set([model.id for model in self._client.models.list()])

    def num_tokens(self, string, model_name):
        """Returns the number of tokens in a text string."""
        encoding = self._tiktoken_encoding_for_model(model_name)

        return len(encoding.encode(string))

    def generate_message_history(self, messages=None):
        if messages is None:
           return []

        message_history = []
        for message in messages:
            message_history.append(
                self.generate_message(
                    "assistant" if message.sender == "assistant" else "user",
                    message.text,
                    # TODO: Decide if past images should be included.
                    images=message.images
                )
            )

        return message_history

    def generate_system_message(self, system_prompt):
        return {
            "role": "system",
            "content": system_prompt
        }

    def generate_message(self, role, text, images=None):
        """TODO: Make this a class method?"""
        if role not in self.ACCEPTABLE_MESSAGE_ROLES:
            raise ValueError(self.INCORRECT_MESSAGE_ROLE_MESSAGE)

        if images is None or len(images) == 0:
            content = text

        else:
            content = [{"type": "text", "text": text}]
            for image in images:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image.to_base64(format='JPEG')}"
                        }
                    }
                )

        return  {
            "role": role,
            "content": content,
        }

    def _package_messages_to_send(self, user_prompt, images, system_prompt, messages):
        if messages is None:
            messages = []

        if images is None:
            images = []

        if system_prompt is None:
            system_prompt = 'You are a helpful assistant.'

        message = self.generate_message('user', user_prompt, images)
        messages_to_send = [
            self.generate_system_message(system_prompt)
        ] + self.generate_message_history(messages) + [message]

        return messages_to_send

    def _run_prompt_streaming(self, model, messages, max_tokens, response_format, temperature):
        """Helper method for streaming prompt responses.

        This method exists to hide the peculiarities of each API's format for
        chunks so the calling code only need expect text chunks.
        """
        options = {}
        if response_format == "json":
            options['response_format'] = {"type": "json_object"}

        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
            temperature=temperature,
            **options
        )

        for chunk in response:
            # The first and last chunk seem to contain '' and None resp. Ignore those.
            chunk_text = chunk.choices[0].delta.content
            if chunk_text:
                yield chunk_text

    def run_prompt(self, model_name, user_prompt, images=None, system_prompt=None, messages=None, stream=False, max_tokens=500, response_format="text", temperature=0.0):

        messages_to_send = self._package_messages_to_send(user_prompt, images, system_prompt, messages)

        options = {}
        if response_format == "json":
            options['response_format'] = {"type": "json_object"}

        if stream:
            return self._run_prompt_streaming(
                model=model_name,
                messages=messages_to_send,
                max_tokens=max_tokens,
                response_format=response_format,
                temperature=temperature
            )

        response = self._client.chat.completions.create(
            model=model_name,
            messages=messages_to_send,
            max_tokens=max_tokens,
            stream=False,
            temperature=temperature,
            **options
        )

        return response.choices[0].message.content


class GroqAPI(OpenAIAPI):
    """Interface to the Groq API. Conforms to the OpenAI API."""

    def __init__(self, name='Groq'):
        from groq import Groq

        self._client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.name = name

    def list_models(self):
        return set([model.id for model in self._client.models.list().data])


class OllamaAPI(OpenAIAPI):
    """Interface to the Ollama API. Borrows some functionality from the OpenAI API."""

    def __init__(self, name='Ollama'):
        host = os.environ.get('OLLAMA_CLIENT_HOST', 'http://localhost:11434')
        if host[-1] == '/':
            host = host[:-1]

        self.chat_endpoint = f"{host}/api/chat"
        self.model_list_endpoint = f"{host}/api/tags"

    def list_models(self):
        response = requests.get(self.model_list_endpoint)
        response_data = json.loads(response.content)

        return set(
            [model['name'] for model in response_data['models']]
        )

    def generate_message(self, role, text, images=None):
        """TODO: Make this a class method?"""
        if role not in self.ACCEPTABLE_MESSAGE_ROLES:
            raise ValueError(self.INCORRECT_MESSAGE_ROLE_MESSAGE)

        message =  {
            "role": role,
            "content": text,
        }

        if images is not None and len(images) > 0:
            message["images"] = [img.to_base64(format='JPEG') for img in images]

        return message

    @staticmethod
    def _generate_request_payload(model, messages, stream, response_format, temperature):
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        if response_format == "json":
            payload["format"] = "json"

        return payload

    def _run_prompt_streaming(self, model, messages, max_tokens, response_format, temperature):
        """Helper method for streaming prompt responses.

        This method exists to hide the peculiarities of each API's format for
        chunks so the calling code only need expect text chunks.
        """

        response = requests.post(
            self.chat_endpoint,
            json=self._generate_request_payload(model, messages, True, response_format, temperature),
            # Important to have this here (in addition to stream in the payload)!
            # See commit message (June 2 2024 around 8:45 GMT+1)
            # https://requests.readthedocs.io/en/latest/user/advanced/#streaming-requests
            stream=True
        )

        for chunk in response.iter_lines():
            body = json.loads(chunk)
            if "error" in body:
                raise LLMAPIException(body["error"])

            # Phrasing it like this because we want "done" to be in body and
            # be equal to False (i.e. we don't want to evaluate block if
            # "done" is not in body, which would return the Falsy None).
            if body.get("done") is False:
                message = body.get("message", "")
                content = message.get("content", "")

                yield content

    def run_prompt(self, model_name, user_prompt, images=None, system_prompt=None, messages=None, stream=False, max_tokens=500, response_format="text", temperature=0.0):

        messages_to_send = self._package_messages_to_send(user_prompt, images, system_prompt, messages)

        if stream:
            return self._run_prompt_streaming(
                model=model_name,
                messages=messages_to_send,
                max_tokens=max_tokens,
                response_format=response_format,
                temperature=temperature
            )

        response = requests.post(
            self.chat_endpoint,
            json=self._generate_request_payload(model_name, messages_to_send, False, response_format, temperature),
        )

        response_data = json.loads(response.content)

        if 'error' in response_data:
            raise LLMAPIException(response_data['error'])

        return response_data['message']['content']


class GoogleAPI(BaseAPI):
    """Interface to the Google GenAI API."""

    ACCEPTABLE_MESSAGE_ROLES = {'model', 'user'}
    INCORRECT_MESSAGE_ROLE_MESSAGE = (
        f'Provided role is not an acceptable value. Must be one of: '
        f'{ACCEPTABLE_MESSAGE_ROLES}.'
    )

    SAFETY_SETTINGS = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]

    def __init__(self, name="Google"):
        import google.generativeai as genai

        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        # Placeholder for GenerativeModel class so we don't have to import
        # lib globally.
        self._client = genai.GenerativeModel
        self.name = name

    @property
    def available(self):
        try:
            _ = self.list_models()
            return True

        except Exception:
            return False

    def list_models(self):
        import google.generativeai as genai

        return set(
            [model.name.replace('models/', '') for model in genai.list_models()]
        )

    def num_tokens(self, string, model_name):
        """Returns the number of tokens in a text string."""
        model = self._client(model_name=model_name)
        response = model.count_tokens(string)

        return response.total_tokens

    def generate_message_history(self, messages=None):
        if messages is None:
           return []

        message_history = []
        for message in messages:
            message_history.append(
                self.generate_message(
                    "model" if message.sender == "assistant" else "user",
                    # TODO: Send previous images?
                    message.text,
                    message.images
                )
            )

        return message_history

    def generate_message(self, role, text, images=None):
        """TODO: Make this a class method?"""
        if role not in self.ACCEPTABLE_MESSAGE_ROLES:
            raise ValueError(self.INCORRECT_MESSAGE_ROLE_MESSAGE)

        parts = [text]

        if images is not None:
            # https://ai.google.dev/api/python/google/generativeai/GenerativeModel#multi-turn
            for image in images:
                parts.append(
                    {
                        'mime_type': "image/jpeg",
                        'data': image.to_bytes(format="JPEG")
                    }
                )

        return {
            'role': role,
            'parts': parts
        }

    def _run_prompt_streaming(self, model, messages_to_send):
        response = model.generate_content(messages_to_send, stream=True)

        for chunk in response:
            yield chunk.text

    def run_prompt(self, model_name, user_prompt, images=None, system_prompt=None, messages=None, stream=False, max_tokens=500, response_format="text", temperature=0.0):
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 1,
            "max_output_tokens": max_tokens,
            "candidate_count": 1
        }

        # JSON mode only seems to be available on Gemini 1.5 (not 1).
        if response_format == "json":
            generation_config["response_mime_type"] = "application/json"

        # TODO: Handle deciding whether to pass system instruction better.
        # Gemini 1 does not allow system prompt.
        model = self._client(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=system_prompt or 'You are a helpful assistant.',
            safety_settings=self.SAFETY_SETTINGS
        )

        messages_to_send = self.generate_message_history(messages or [])
        messages_to_send.append(
            self.generate_message("user", user_prompt, images)
        )

        if stream:
            return self._run_prompt_streaming(model, messages_to_send)

        response = model.generate_content(messages_to_send)
        return response.candidates[0].content.parts[0].text


class TestAPI():
    """A fake API for tests and experiments."""

    LOREM_IPSUM = (
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do '
        'eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim '
        'ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut '
        'aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit '
        'in voluptate velit esse cillum dolore eu fugiat nulla pariatur. '
        'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui '
        'officia deserunt mollit anim id est laborum.'
    )

    def __init__(self, name="Test"):
        self.name = name

    @property
    def available(self):
        return True

    def list_models(self):
        """This is only here for compatibility with other APIs."""
        return {}

    def generate_message_history(self, messages=None):
       return messages

    def run_prompt(self, prompt=None, *args, stream=False, **kwargs):
        """Responds with the prompt passed to it, or predefined text if none is.

        Args:
            prompt: str - Text for the fake API to repeat back.
            stream: bool - Returns a generator that yields words if true,
                else returns all the text in one chunk.

        Returns:
            str Generator if stream is True, str otherwise.
        """
        if prompt is None:
            prompt = self.LOREM_IPSUM

        response_generator = self._stream_text_chunks()
        if stream:
            return response_generator

        return ''.join([word for word in response_generator])

    def _stream_text_chunks(self, num_words=20, delay_ms=100):
        """Streams a piece of text in chunks with a configurable delay.

        Args:
            num_words: The number of words to return.
            delay_ms: The delay between words in milliseconds.

        Yields:
            str: Words from lorem ipsum.
        """
        words = self.LOREM_IPSUM.split(' ')
        num_words = min(num_words, len(words))

        # Don't add a leading space before the first word.
        padding = ''
        for word in words[:num_words]:
            time.sleep(delay_ms / 1000)

            yield padding + word
            padding = ' '
