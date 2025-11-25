# MAIDX - Multimodal AI based Data Extraction

MAIDX is a powerful desktop application for extracting structured data from documents using AI language models. It supports multiple file formats and allows you to define custom extraction schemas.



## Features

- **Multi-Model Support**: Works with GPT, Qwen, Grok, Deepseek and custom API endpoints
  - Auto-load model settings from environment variables
- **Multiple File Formats**: Process TXT, PDF, JPG and PNG
  - Pending: DOCX
- **Flexible Schema Definition**: Define extraction schemas in JSON format
  - Supports LLM-generated schema based on research questions and a sample file
  - Pending: SQLite
- **Tool Use**: LLMs can execute tools for better calculation or understanding
  - Sandboxed Python code for calculations and transformations
      - Pending: Safer options
  - Web fetch tool to allow LLM search the web
      - Pending: Load some APIs
  - Self reflection (internal thinking) Tool
  - Schema Verification Tool
  - Pending: DB related tools (RAG), to-do tool
- **Batch Processing**: Process entire folders of documents automatically
- **Progress Tracking**: Progress bar and detailed logging
    - Pending: Pause & Resume; DB Cache of LLM streams




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



## Usage

1. Run the application:
    ```bash
    python main.py
    ```
2. **Model Setup Tab**:
   
   - Choose a preset (GPT, DeepSeek, Grok) or configure a custom endpoint
   - Enter your API key
   - Configure model parameters (temperature, max tokens, etc.)
3. **Schema Setup Tab**:
   
   - Define fields manually or write the schema directly
   - Add descriptions for each field to guide the LLM
   - Or define a research question and use LLM to generate the schema
4. **Method Setup Tab**
   
   - Define how you would like to load the data and call the LLM
   - Choose extraction mode (one or multiple records per file)
5. **Data Extraction Tab**:
   
   - Select input folder containing your documents
   - Specify output path
   - Check if you would like to see the log
   - Click "Start Extraction"



## Example Use Cases

### Example 1 (Enclosed): Extract information from news articles (text)

1. **Model Setup**: Choose a LLM and enter your API key, or set environment variables or `.env` file for auto-loading.
2. **Schema Setup**: Define a news schema with fields like title, person, timestamp, emotion. You can also auto-generate or use the preset in `sample/news-task-txt/txt-news-schema.txt`
3. **Method Setup**: Configure extraction mode based on document structure  (suggestion: disable segmentation).
4. **Data Extraction**: Select the `sample/news-task-txt/txt-news-raw` folder, choose an output folder, and start.

The LLM will:
- Read each news article
- Extract structured data according to your schema
- Use the Python tool for timestamp conversions
- Save results to JSON file



### Example 2 (Enclosed): Extract Nutrition Information: (Process Images, and mixed documents)

1. **Model Setup**: Choose a Vision Capable Model and enter your API key, or set environment variables or `.env` file for auto-loading.
2. **Schema Setup**: Define a news schema with fields like calories, sugar, etc. You can also auto-generate or use the preset.
3. **Method Setup**: Configure extraction mode (suggestion: disable segmentation).
4. **Data Extraction**: Select the `sample/food-task-multimodal` folder, choose output file, and start.





## Architecture

```
maidx/
├── main.py                  # Application entry point
├── sample/                  # Sample datasets
├── ui/
│   ├── main_window.py       # Main window with tabs
│   └── tabs/*.py            # Configuration Tabs UI
├── core/
|   ├── llm_tools/
|   |   ├── tools_manager.py # Manage all LLM tools
|   |   └── *.py             # LLM Tools
│   ├── llm_client.py        # LLM API client (httpx-based)
|   ├── llm_prompt.py       
|   ├── img_uri.py           # Stores image MIMEs
│   ├── file_manager.py      # Document parsers and controller
│   └── extraction_thread.py # Background extraction worker
└── requirements.txt
```



## Security

The Python execution tool runs in a restricted environment:
- Only safe built-in functions allowed
- Limited to datetime, time, json, math, and re modules
- File operations blocked
- No network access

Yet there is no guarantee that it 100% safe. 

The network fetch tool can GET and POST to any website. 



## API Compatibility

MAIDX works with any OpenAI-compatible API endpoint, preferably with image support.
The following services are tested and supported:

- GPT (OpenAI API)
- DeepSeek
- Qwen
- Grok (X.AI)
- Custom endpoints following the OpenAI API format

Environment variables can be used to auto-load model settings and API keys for quick setup.



## Requirements

- Windows 10, MacOS 15 (Other OSes supporting PyQT6 may run, but untested)
- Python 3.11 (Other version may be possible, but untested)
- Packages in `requirements.txt`



## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.
