# MAIDX - Multimodel AI based Data Extraction

MAIDX is a powerful desktop application for extracting structured data from documents using AI language models. It supports multiple file formats and allows you to define custom extraction schemas.

## Features

- **Multi-Model Support**: Works with GPT, DeepSeek, Grok, and custom API endpoints
- **Multiple File Formats**: Process TXT
    - Pending: PDF, DOCX, and image files (JPG, PNG)

- **Flexible Schema Definition**: Define extraction schemas in JSON format
    - Pending: SQLite 

- **Tool Use**: LLMs can execute safe Python code for calculations and transformations
    - Pending: Safer options 

- **Batch Processing**: Process entire folders of documents automatically
- **Progress Tracking**: Real-time progress bar and detailed logging

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd maidx
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Pending: For OCR support (image parsing), you also need to install Tesseract OCR:

- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

## Usage

1. Run the application:
```bash
python main.py
```

2. **Model Setup Tab**:
   - Choose a preset (GPT, DeepSeek, Grok) or configure a custom endpoint
   - Enter your API key
   - Configure model parameters (temperature, max tokens, etc.)
   - Enable/disable the Python execution tool
3. **Schema Setup Tab**:
   - Define fields manually or write the schema directly
   - Add descriptions for each field to guide the LLM
4. **Data Extraction Tab**:
   - Select input folder containing your documents
       - Pending: Choose extraction mode (one or multiple records per file)
   - Specify output path
   - Click "Start Extraction"

## Example Use Case

Extract information from news articles:

1. **Model Setup**: Choose DeepSeek and enter your API key
2. **Schema Setup**: Define a news schema with fields like title, person, timestamp, emotion
3. **Data Extraction**: Select folder with .txt news files, choose output file, and start

The LLM will:
- Read each news article
- Extract structured data according to your schema
- Use the Python tool for timestamp conversions
- Save results to SQLite database or JSON file

## Architecture

```
maidx/
├── main.py                 # Application entry point
├── ui/
│   ├── main_window.py      # Main window with tabs
│   └── tabs/
│       ├── model_setup_tab.py      # Model configuration UI
│       ├── schema_setup_tab.py     # Schema definition UI
│       └── data_extraction_tab.py  # Extraction control UI
├── core/
│   ├── llm_client.py       # LLM API client (httpx-based)
│   ├── tools.py            # Safe Python execution tool
│   ├── file_parsers.py     # Document parsers
│   └── extraction_worker.py # Background extraction worker
└── requirements.txt
```

## Security

The Python execution tool runs in a restricted environment:
- Only safe built-in functions allowed
- Limited to datetime, json, math, and re modules
- File operations blocked
- No network access

## API Compatibility

MAIDX works with any OpenAI-compatible API endpoint. The following services are tested:
- OpenAI GPT models
- DeepSeek
- Grok (X.AI)
- Custom endpoints following the OpenAI API format

## Requirements

- Python 3.8+
- PySide6 (Qt GUI framework)
- httpx (HTTP client)
- PyPDF2 (PDF parsing)
- python-docx (DOCX parsing)
- Pillow + pytesseract (Image OCR)

## License

WTFPL

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.
