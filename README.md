# Image Analysis API

This FastAPI-based application, deployed on Railway, provides an endpoint to analyze images and identify real-world issues such as safety hazards, infrastructure damage, or environmental concerns. It uses Google's Gemini model to describe and analyze images, returning a JSON response with identified problems, their types, and suggested actions.

## Base URL
```
https://ai-powered-suggestions-app-production-196d.up.railway.app/
```

## Features
- Upload an image via a POST request to `/analyze-image`.
- Validates image type and size (must be an image file, <5MB).
- Uses Gemini AI to describe the image and identify issues.
- Returns a JSON object with:
  - `problems`: Array of identified issues (e.g., "pothole in road").
  - `problem_types`: Array of categories (e.g., "infrastructure").
  - `suggestions`: Array of actionable suggestions (e.g., "Report to local authorities").

## Usage

### Endpoint
- **POST `/analyze-image`**
  - **URL**: `https://ai-powered-suggestions-app-production-196d.up.railway.app/analyze-image`
  - **Content-Type**: `multipart/form-data`
  - **Request Body**: A single file field named `file` containing the image (PNG, JPEG, etc.).
  - **Response**: JSON object with `problems`, `problem_types`, and `suggestions`.

### Example Request
Using `curl`:
```bash
curl -X POST "https://ai-powered-suggestions-app-production-196d.up.railway.app/analyze-image" -F "file=@/path/to/image.png"
```

Using Python (`requests`):
```python
import requests

url = "https://ai-powered-suggestions-app-production-196d.up.railway.app/analyze-image"
files = {"file": open("image.png", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Example Response
```json
{
  "problems": ["Broken lock on door", "Cracked sidewalk"],
  "problem_types": ["security", "infrastructure"],
  "suggestions": [
    "Replace the lock and report to building management",
    "Report to local authorities for sidewalk repair"
  ]
}
```
If no issues are found or an error occurs:
```json
{
  "problems": [],
  "problem_types": [],
  "suggestions": []
}
```

### Error Responses
- **400 Bad Request**: Invalid file type, size >5MB, or corrupted image.
  ```json
  {"detail": "File must be an image"}
  ```
- **500 Internal Server Error**: Unexpected errors (returns empty arrays).

## Notes
- Ensure the image is clear and relevant to public reporting (e.g., infrastructure, safety).
- The API allows CORS from all origins for flexibility in client-side applications.
- The Gemini model’s accuracy depends on image quality and description clarity.

## Troubleshooting
- **Invalid image**: Ensure the file is a valid image (<5MB, PNG/JPEG).
- **API errors**: Check the response for details (e.g., invalid file type).
- **CORS issues**: The API allows all origins; ensure your client handles responses correctly.

## License
MIT License. See `LICENSE` file in the repository for details.
