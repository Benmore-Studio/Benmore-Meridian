---
name: nano_banana
description: Generates or edits an image using the Gemini 2.5 Flash Image (Nano Banana) model via the API.
license: Google Generative AI SDK License
context: fork
---
## Skill Instructions
Provide clear, step-by-step instructions for Claude to follow when this skill is invoked. Use specific, action-oriented language.

**Goal:** To generate or edit an image based on a text prompt (and optionally, input images) by calling the Gemini API's dedicated image model.

**Steps:**
1.  **Analyze the Request:** Determine the user's need:
    * **Text-to-Image Generation:** Only a text prompt is provided.
    * **Image Editing/Fusion:** A text prompt and one or more input images (e.g., file paths, URLs, or Base64 data) are provided.
2.  **Utilize Tools (if any):**
    * Use the **Generative AI SDK** (Python, Node.js, etc.) for API interaction.
    * Use file handling tools (e.g., `read` in a `bash` context, or file I/O libraries in code) to read local image files and convert them into API-compatible `Part` objects.
3.  **Process Data:**
    * **API Configuration:** Ensure the `GEMINI_API_KEY` is loaded from the environment. The model name for the API call must be **`gemini-2.5-flash-image`**.
    * **Prepare `contents` List:**
        * **Generation:** `contents = [prompt_text]`
        * **Editing/Fusion:** `contents = [image_part_1, ..., image_part_n, prompt_text]`. Input images must be placed *before* the text prompt.
    * **Execute Call:** Make the `generate_content()` API call with the specified model and contents.
    * **Decode Output:** Access the generated image data, which is returned as **Base64-encoded binary data** in the `inline_data` field of a `Part` object. Decode this data back into a binary image file (e.g., PNG or JPEG).
4.  **Format Output:** Respond to the user with a confirmation message, indicating the successful generation or edit and confirming the location/availability of the resulting image file. If an error occurs (e.g., API key issue, safety violation), report the error clearly.

## Examples
Include example inputs and the expected outputs to help Claude understand success.

### Example 1: Basic Input/Output (Text-to-Image)
* **User Prompt:** "Generate a surreal image of a golden mechanical banana floating in space near a constellation."
* **Expected Behavior:** Claude uses the prompt in the `contents` list, calls the `gemini-2.5-flash-image` model, decodes the Base64 response, and outputs a confirmation like: "Image generation successful. The surreal image has been saved to the working directory."

### Example 2: Edge Case (Image Editing with File Input)
* **User Prompt:** "Please edit the image at 'input/photo.jpg' by changing the person's shirt to bright yellow."
* **Expected Behavior:** Claude first converts 'input/photo.jpg' into a `Part` object. The API call is made with `contents=[image_part, "change the person's shirt to bright yellow"]`. The model performs the localized edit, and Claude saves the final image and outputs: "Image editing complete. The updated image with the yellow shirt has been saved."

## Best Practices & Constraints
* Keep this skill focused on one specific workflow; do not try to make a "Swiss Army knife" skill.
* Ensure all referenced files exist in the correct locations within the skill's directory.
* Do not hardcode sensitive information like API keys or passwords.
* Always specify the full model name: **`gemini-2.5-flash-image`**.

-----

## Practical work through

Before you can use the model, you need to complete a few setup steps:

1.  **Get an API Key**: Obtain a Gemini API key from Google AI Studio.
2.  **Install the SDK**: You'll need the appropriate Google Generative AI SDK for your programming language (e.g., `google-generativeai` for Python).
3.  **Set Up Environment**: For security, store your API key in an environment variable, typically named `GEMINI_API_KEY`.

For Python, you'll generally install it like this:

```bash
pip install google-generativeai pillow
```

-----

## 💻 API Usage: Python Example

You use the same `generate_content` call as with other Gemini models, but specify the image model and provide your prompt (and optionally, input images). The model name to use is **`gemini-2.5-flash-image`**.

### 1\. Text-to-Image Generation (Simple Prompt)

This is a basic text-to-image request.

```python
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# The client automatically picks up the GEMINI_API_KEY from your environment
client = genai.Client()

prompt = "A hyper-realistic image of a cat wearing a party hat, sitting on a banana-shaped sofa."

response = client.models.generate_content(
    model="gemini-2.5-flash-image", # The Nano Banana model
    contents=[prompt],
)

# Extract and save the generated image
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        # The image is returned as base64-encoded data
        image_data = part.inline_data.data
        image = Image.open(BytesIO(image_data))
        image.save("generated_image.png")
        print("Image generated and saved as generated_image.png")
```

-----

### 2\. Image Editing (Image + Text-to-Image)

To edit an existing image, you pass **both the image data and the text prompt** as the `contents`.

1.  **Load the Image**: You need a function to convert your local image file into a format the API can accept.
2.  **Call the API**: Send the image and your editing instruction.

<!-- end list -->

```python
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client()

# Helper function to convert a local file to a Part object for the API
def file_to_part(path: str, mime_type: str):
  """Converts a local file path to a GenerativePart object."""
  return types.Part.from_uri(uri=path, mime_type=mime_type)

# --- Example of editing a local image ---
# NOTE: Replace 'path/to/your/image.png' with a real image file path
# For this example to run, you must have an image at this path.

image_part = file_to_part(path="path/to/your/image.png", mime_type="image/png")
edit_prompt = "Change the background of this image to a vibrant, neon-lit cityscape at night."

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[image_part, edit_prompt], # Pass both the image and the prompt
)

# Extract and save the edited image (same logic as before)
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        image_data = part.inline_data.data
        edited_image = Image.open(BytesIO(image_data))
        edited_image.save("edited_image.png")
        print("Image edited and saved as edited_image.png")
```
