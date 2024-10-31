import os

from .apis import GoogleAPI, OpenAIAPI, OllamaAPI, GroqAPI


class Model():
    """Representation of an LLM."""

    def __init__(self, name, api, input_token_limit=1024, output_token_limit=1024,
            supports_vision=False, uncensored=False, supports_system_message=True,
            supports_json_mode=True):

        self.name = name
        self.api = api
        # Conservative defaults above in case these are not supplied.
        self.input_token_limit = input_token_limit
        self.output_token_limit = output_token_limit
        self.supports_vision = supports_vision
        self.uncensored = uncensored
        self.supports_system_message = supports_system_message
        self.supports_json_mode = supports_json_mode

    @property
    def censored(self):
        return not self.uncensored

    @property
    def available(self):
        if self.api.name.lower() == 'test':
            return True

        if self.api.name.lower() == 'ollama':
            local_models = self.api.list_models()
            name_with_tag = self.name if ':' in self.name else f"{self.name}:latest"

            return name_with_tag in local_models

        return self.name in self.api.list_models()

    def run_prompt(self, user_prompt, images=None, system_prompt=None,
            messages=None, stream=False, response_format="text",
            temperature=0.0, max_tokens=500):
        # TODO: Decide whether to raise an error if images are provided but model
        # does not support vision. Think about possible scenarios where images
        # may be present (non-accidentally) as an argument for keeping things
        # as they are now.
        if images is None or not self.supports_vision:
            images = []

        if max_tokens > self.output_token_limit:
            raise ValueError(
                f"max_tokens cannot be greater than model\'s' output token "
                f"limit ({self.output_token_limit})."
            )

        return self.api.run_prompt(
            model_name=self.name,
            user_prompt=user_prompt,
            images=images,
            system_prompt=system_prompt,
            messages=messages,
            stream=stream,
            # Force this to be text if model doesn't support JSON-mode.
            response_format=response_format if self.supports_json_mode else "text",
            temperature=temperature,
            max_tokens=max_tokens
        )


if os.environ.get('OPENAI_API_KEY', '').strip():
    openai_api = OpenAIAPI()
    # Token limits and other info here: https://platform.openai.com/docs/models
    # Pricing: https://openai.com/api/pricing/
    gpt_3_5_turbo = Model('gpt-3.5-turbo', openai_api, 16385, 4096)
    gpt_4_turbo = Model('gpt-4-turbo', openai_api, 128000, 4096, supports_vision=True)
    # This snapshot is currently (Aug 23, 2024) 1/2 the price of vanilla gpt-4o, with 16k vs 4k output tokens.
    gpt_4o = Model('gpt-4o-2024-08-06', openai_api, 128000, 16384, supports_vision=True)
    gpt_4o_mini = Model('gpt-4o-mini', openai_api, 128000, 16384, supports_vision=True)
    o1_preview = Model('o1-preview', openai_api, 128000, 32768)
    o1_mini = Model('o1-mini', openai_api, 128000, 65536)

if os.environ.get('GROQ_API_KEY', '').strip():
    groq_api = GroqAPI()
    mixtral_groq = Model('mixtral-8x7b-32768', groq_api, 32768)
    llama3_8b_groq = Model('llama3-8b-8192', groq_api, 8192)
    llama3_70b_groq = Model('llama3-70b-8192', groq_api, 8192)

    llama3_8b_tool_use_groq = Model('llama3-groq-8b-8192-tool-use-preview', groq_api, 8192)
    llama3_70b_tool_use_groq = Model('llama3-groq-70b-8192-tool-use-preview', groq_api, 8192)

    # Note (July '24): These are intrinsically 131072 input tokens, but limited during preview
    # https://console.groq.com/docs/models
    llama_3_1_8b_groq = Model('llama-3.1-8b-instant', groq_api, 8000)
    llama_3_1_70b_groq = Model('llama-3.1-70b-versatile', groq_api, 8000)
    llama_3_1_405b_groq = Model('llama-3.1-405b-reasoning', groq_api, 16000)

    llama_3_2_11b_vision_groq = Model('llama-3.2-11b-vision-preview', groq_api, 8000)
    llama_3_2_90b_vision_groq = Model('llama-3.2-90b-vision-preview', groq_api, 8000)

if os.environ.get('OLLAMA_CLIENT_HOST', '').strip():
    # Ollama models have a default context window of 2048 (as of Aug 2024),
    # to save on GPU memory
    # https://youtu.be/QfFRNF5AhME?si=ysBMQQc1uiGWU9Da&t=154
    # but this can be adjusted:
    # https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-specify-the-context-window-size
    ollama_api = OllamaAPI()
    # TODO: Download models if not available?
    # Should ask user if they want to -- perhaps do this with all models, along
    # with the disk space required.
    llama3_8b_ollama = Model('llama3', ollama_api, 8192)
    llava_1_6 = Model('llava:latest', ollama_api, 2048, supports_vision=True)
    llava_1_6_13b = Model('llava:13b', ollama_api, 2048, supports_vision=True)
    # Context length below is guessed.
    moondream = Model('moondream:1.8b-v2-fp16', ollama_api, 2048, supports_vision=True)

if os.environ.get('GOOGLE_API_KEY', '').strip():
    google_api = GoogleAPI()
    gemini_1_5_pro = Model('gemini-1.5-pro-latest', google_api, 1_048_576, 8192,
        supports_vision=True)
    gemini_1_5_flash = Model('gemini-1.5-flash-latest', google_api, 1_048_576, 8192,
        supports_vision=True)
