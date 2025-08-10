PDF Outline Extractor – Adobe Connecting the Dots Challenge (Part 1A)
📌 Overview
This application extracts structured outlines (document title, H1/H2/H3 headings with page numbers) from PDF documents and outputs them in JSON format.
It is designed to meet the requirements of Part 1A of Adobe's Connecting the Dots Challenge.

🛠 Requirements
Docker compatible with AMD64 architecture

CPU-only execution (no GPU required)

Model size (if used) ≤ 200MB

Processing time ≤ 10 seconds for a 50-page PDF

No internet access required during execution

📚 Libraries Used
PyMuPDF (Fitz) – High-performance PDF processing library for text extraction, font details, and page layout analysis.

🔍 Heading Detection Methodology
The application uses a heuristic-based approach based on font size analysis.

Steps:
Text Extraction

Extracts text blocks from each page, along with font sizes and positions using PyMuPDF.

Font Size Analysis

Collects all unique font sizes in the document.

Largest font sizes are assigned as H1, H2, and H3 headings.

Uses a small epsilon for floating-point comparison to handle rendering variations.

Hierarchical Assignment

Classifies text spans into H1, H2, or H3 levels based on relative font size thresholds (H1 > H2 > H3).

Page Number Association

Associates each heading with its corresponding page number.

Title Extraction

Attempts to read the title from PDF metadata.

If missing/unreliable, uses the largest font size text on the first page.

📤 Output Format
The output is stored as a JSON file:

json
Copy
Edit
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
⚙️ How to Build and Run
1️⃣ Create Input & Output Directories
bash
Copy
Edit
mkdir input
mkdir output
Place your PDF files in the input/ directory.

2️⃣ Build the Docker Image
bash
Copy
Edit
docker build --platform linux/amd64 -t pdf-outline-extractor:latest .
3️⃣ Run the Docker Container (Single File Example)
bash
Copy
Edit
docker run --rm \
    -v "${PWD}/input:/app/input" \
    -v "${PWD}/output:/app/output" \
    --network none \
    pdf-outline-extractor:latest
Note:
The current app.py version processes a single input PDF and outputs a single JSON file.
The CMD in the Dockerfile will need to be updated to iterate through /app/input for batch processing in the final version.

🚀 Future Improvements (Part 1B)
More Robust Heading Detection – Possibly integrate ML-based models (within size constraints) or advanced layout analysis.

Semantic Understanding – Identify relationships between sections for richer outlines.

