import base64
import io
from typing import List, Literal

import fitz
import pypdf
from pypdf.errors import PdfReadError
import logging

from core import img_uri


def pdf_render_img(pdf_file_path, dpi: int = 300, output_format: Literal['jpg', 'png'] = "jpg"):
    try:
        doc = fitz.open(pdf_file_path)
        # Calculate the scale factor for rendering based on DPI
        # PyMuPDF's default resolution is 72 DPI.
        zoom_factor = dpi / 72.0
        mat = fitz.Matrix(zoom_factor, zoom_factor)  # Matrix(zoom-x, zoom-y) - zoom
        base64_images = []
        mime_type = img_uri.convert_ext_to_mime(output_format)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)

            # Convert pixmap to bytes in the desired image format
            img_bytes: bytes
            if output_format.lower() == "jpg":
                img_bytes = pix.tobytes(output="jpg", jpg_quality=90)
            else:  # png
                img_bytes = pix.tobytes(output="png")
            base64_encoded_image = base64.b64encode(img_bytes).decode('utf-8')
            base64_images.append(f"data:{mime_type};base64,{base64_encoded_image}")
        doc.close()
        return base64_images
    except FileNotFoundError:
        logging.warning(f"Error: PDF file not found at '{pdf_file_path}'")
        return []
    except Exception as e:
        logging.warning(f"Error when rasterizing (rendering) pdf: {e}")
        return []


def pdf_reader(pdf_file_path):
    """
    Reads a PDF file, extracts text content page by page, and converts embedded images
    into base64 encoded data URIs.
    """
    page_texts = []
    page_images = []
    try:
        with open(pdf_file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                images = []
                if text:
                    page_texts.append(text)
                else:
                    page_texts.append("")

                for img_ref in page.images:
                    try:
                        image_bytes = img_ref.data
                        mime_type = img_uri.convert_ext_to_mime(img_ref.name)
                        base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                        data_uri = f"data:{mime_type};base64,{base64_encoded_image}"
                        images.append(data_uri)
                        print(f"Processing {img_ref.name}")
                    except Exception as e:
                        logging.warning(f"Could not process image on page {page_num + 1} ({img_ref.name}): {e}")
                        continue  # Skip to the next image

                page_images.append(images)
        return page_texts, page_images
    except FileNotFoundError:
        logging.warning(f"File {pdf_file_path} not found")
        return [], []
    except PdfReadError:
        logging.warning(f"PDF {pdf_file_path} not readable.")
        return [], []


class FileManager:
    def __init__(self, file_list: List[str], output_path: str, pdf_parse_mode="text"):
        """
        File manager for LLM
        path_list: list of file paths
        pdf_parse_mode: decide how to parse PDF files. "text", "text_with_img", "page_as_img"

        files: {
            "X:/xxx.pdf": {
                "text": ["page1", "page2", "page3"],
                "img": [base64, base64, ..],
                "type": "pdf",
            },
            "X:/xxx.txt": {
                "text": "",
                "type": "txt",
            },
        }
        """
        self.path_list = file_list
        self.output_path = output_path
        self.pdf_parse_mode = pdf_parse_mode
        self.files = {}

    def load_files(self):
        for file in self.path_list:
            pass






