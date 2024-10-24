from datetime import datetime
import json
import os
import time

import jinja2


class Assistant():

    def __init__(self, *, name, model, system_template=None, temperature=0.0, description=""):
        self.name = name
        self.description = description
        self.model = model
        self.temperature = temperature

        if system_template is None:
            self.system_template = system_template

        else:
            # To enable template caching and configuration of Jinja behaviour.
            env = jinja2.Environment(
                loader=jinja2.DictLoader({f'{name}__template': system_template}),
                # Strips leading spaces/tabs from the start of blocks and
                # remove newlines after them.
                # https://jinja.palletsprojects.com/en/3.1.x/templates/#whitespace-control
                lstrip_blocks=True,
                trim_blocks=True
            )
            self.system_template = env.get_template(f'{name}__template')

    def generate_system_prompt(self, context=None):
        """
        Args:
            context: dict - A dictionary containing keys matching the variables
                in the system template, along with values with which to
                substitute them.
        """
        # TODO: Consider using @cache.

        if self.system_template is None:
            return "You are a helpful assistant."

        if context is None:
            context = dict()

        return self.system_template.render(context)

    def _prompt_streaming(self, user_prompt, images, system_prompt, messages, response_format, conversation, max_tokens):
        response = self.model.run_prompt(
            user_prompt=user_prompt,
            images=images,
            system_prompt=system_prompt,
            messages=messages,
            stream=True,
            response_format=response_format,
            temperature=self.temperature,
            max_tokens=max_tokens
        )

        all_chunks = []
        for chunk in response:
            all_chunks.append(chunk)
            yield chunk

        user_message = Message(sender="user", text=user_prompt, images=images)
        ai_message = Message(sender="assistant", text=''.join(all_chunks))
        # TODO: Think about making it mandatory to have conversations.
        # If one is not provided, then it's only used internally -- or have
        # another flag (send conversation history or something to that effect)
        # that is the main history-related argument, with the conversation object
        # just being implicit i.e. only provided if they want to continue a previous
        # conversation, or have access to the object.
        if conversation is not None:
            conversation.messages.append(user_message)
            conversation.messages.append(ai_message)

    def prompt(self, prompt, *, images=None, conversation=None, stream=False,
               response_format="text", system_prompt_context=None, max_tokens=500):
        """Send the assistant a prompt/message.

        Args:
            prompt: str - The prompt.
            images: list of brain.visual.image.Image - Optional images to go with
                the prompt.
            conversation: Conversation - Optional Conversation object to keep
                track of conversation history.
            stream: bool - Optional. Whether or not to return the response as a
                whole or stream it chunk by chunk. Default False.
            response_format: str - Optional. One of "text" or "json". Desired
                format for the assistant's response. Default "text".
            system_prompt_context: dict of str -> Any - Optional. A dictionary
                with keys/values representing variables in the system template and
                their substitutions respectively.
            max_tokens: int - Optional. Maximum number of output tokens. Default 500.

        Returns:
            str or str generator: The assistant's response. If stream=True, a
                generator is returned.
        """
        messages = []
        if conversation is not None:
            messages = conversation.messages

        if images is None or not self.model.supports_vision:
            images = []

        system_prompt = self.generate_system_prompt(system_prompt_context)

        if stream:
            return self._prompt_streaming(
                user_prompt=prompt,
                images=images,
                system_prompt=system_prompt,
                messages=messages,
                response_format=response_format,
                conversation=conversation,
                max_tokens=max_tokens
            )

        response = self.model.run_prompt(
            user_prompt=prompt,
            images=images,
            system_prompt=system_prompt,
            messages=messages,
            stream=False,
            response_format=response_format,
            temperature=self.temperature,
            max_tokens=max_tokens
        )

        user_message = Message(sender="user", text=prompt, images=images)
        ai_message = Message(sender="assistant", text=response)
        if conversation is not None:
            conversation.messages.append(user_message)
            conversation.messages.append(ai_message)

        return response


class Conversation():
    """Should be possible to rebuild (initialize) based on external e.g. db data."""
    def __init__(self, participants=None, messages=None):
        # Each message is a dict with sender{assistant, name}, text, time
        self.messages = messages or []
        # TODO: Figure out what to do with this. Allowing to be empty for now.
        self.participants = participants or []

    def add_message(self, message):
        # TODO: Should we check that the sender is party to this conversation?
        # OR should we be calculating participants based on senders in self.messages?
        self.messages.append(message)

    def to_dict(self):
        return {
            'participants': self.participants,
            'messages': [message.to_dict() for message in self.messages],
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Message():

    def __init__(self, sender, text, images=None, time=None):
        if time is None:
            # TODO: Use tz aware library.
            self.time = datetime.now()

        self.text = text
        self.sender = sender
        self.images = images or []

    def to_dict(self):
        return {
            'sender': self.sender,
            'text': self.text,
            # Should these be the base64 representations?
            'images': self.images,
            'time': self.time
        }

    def to_json(self):
        return json.dumps(self.to_dict())
