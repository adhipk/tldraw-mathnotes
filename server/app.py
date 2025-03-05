from PIL import Image
from io import BytesIO
import base64
import os
from flask import Flask, request, jsonify
from MathSolver import MathSolver

app = Flask(__name__)

# Update the Flask endpoints
@app.route("/calculate", methods=["POST"])
def calculate():
    """Endpoint to process an image and return the evaluated mathematical result."""
    try:
        data = request.json
        image_data = data.get("image")
        print(data)
        if not image_data:
            return jsonify({"error": "No image data provided"}), 400
        
        # Decode and open the image
        im = Image.open(BytesIO(base64.b64decode(image_data)))
        
        # Initialize the solver and process the image
        solver = MathSolver()
        temp_image = solver.save_image_to_temp(im)
        
        if not temp_image:
            return jsonify({"error": "Failed to save temporary image"}), 500
        
        result = solver.process_image(temp_image)
        
        # Clean up temporary file
        os.remove(temp_image)
        
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)