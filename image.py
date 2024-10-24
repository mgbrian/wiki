import base64
from io import BytesIO

import requests
import numpy as np
from PIL import Image as PILImage


class Image():
    """
    Flexible representation of an image with convenient loading and conversion methods.

    Example:
        img = Image("https://example.com/image.jpg")
        base64_data = img.to_base64()
    """
    def __init__(self, data):
        """
         Initializes an Image object.

         Args:
             data (str, bytes, or np.ndarray): The image data. Can be a filepath,
                 URL, raw bytes, NumPy array or PIL Image.

         Raises:
                 ValueError: If the provided data type is not supported.
        """
        if isinstance(data, str):
            if data.startswith("http"):
                response = requests.get(data)
                self.image = PILImage.open(BytesIO(response.content))

            else:
                self.image = PILImage.open(data)

        elif isinstance(data, bytes):
            self.image = PILImage.open(BytesIO(data))

        elif isinstance(data, np.ndarray):
            self.image = self._load_from_numpy_array(data)

        elif isinstance(data, PILImage.Image):
            self.image = data

        else:
            raise ValueError("Unsupported data type.")

    def _load_from_numpy_array(self, data):
        if data.ndim == 2:  # grayscale
            mode = "L"

        elif data.shape[2] == 3:  # RGB
            mode = "RGB"

        else:
            raise ValueError("Unsupported image shape.")

        return PILImage.fromarray(data, mode=mode)

    @property
    def mimetype(self):
       return "image/" + self.image.format.lower() if self.image.format else None

    @property
    def mode(self):
        return self.image.mode

    @property
    def size(self):
        # TODO: Figure out if this is being used somewhere and remove in favour of w/h below.
        #  (width, height)
        return self.image.size

    @property
    def width(self):
        return self.image.width

    @property
    def height(self):
        return self.image.height

    def to_rgb(self):
        if self.mode == "RGB":
            return self

        return Image(self.image.convert("RGB"))

    def to_grayscale(self):
        if self.mode == "L":
            return self

        return Image(self.image.convert("L"))

    def to_base64(self, format=None):
        """Return a base64 representation of the Image.

        Args:
            format - str - (default None). The format to represent the
                image in. If no value is provided, the Image's format is used.

                Example options: "JPEG", "PNG", "WebP", and more.
                See below for all possible options.
                https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html

        Returns:
            str - A base64 representation of the image (in the supplied format
            if one is provided).
        """
        buffer = BytesIO()
        self.image.save(buffer, format=format or self.image.format)

        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def to_numpy_array(self):
        return np.array(self.image)

    def to_pil_image(self):
        return self.image

    def to_bytes(self, format=None):
        """Return a bytes representation of the Image.

        Args:
            format - str - (default None). The format to represent the
                image in. If no value is provided, the Image's format is used.

                See to_base64 for details.

        Returns:
            bytes - A bytes representation of the image (in the supplied format
            if one is provided).
        """
        buffer = BytesIO()
        self.image.save(buffer, format=format or self.image.format)

        return buffer.getvalue()

    def save(self, path):
        """Save the Image to the given path. Format is inferred from the file extension."""
        self.image.save(path)
