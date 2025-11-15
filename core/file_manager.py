import base64
import json
import os.path
from pathlib import Path
from typing import List, Literal
import fitz
import pypdf
from pypdf.errors import PdfReadError
import logging
from core import img_uri


def read_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ""


def read_img(file_path):
    try:
        mime_type = img_uri.convert_ext_to_mime(file_path)
        with open(file_path, 'rb') as f:
            img_content = f.read()
        base64_encoded_image = base64.b64encode(img_content).decode()
        return f"data:{mime_type};base64,{base64_encoded_image}"
    except Exception as e:
        return ""


def pdf_render_img(pdf_file_path, dpi: int = 300, output_format: Literal['jpg', 'png'] = "jpg"):
    """
    Reads a PDF file, renders each page as an image, and returns a list
    of images in base64 format.
    """
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
    def __init__(self, file_list: List[str], output_path: str,
                 pdf_parse_mode="text", use_segment=False,
                 max_seg_text_len=0, max_seg_page_cnt=0, seg_overlap=0):
        """
        File manager for LLM
        path_list: list of file paths
        pdf_parse_mode: decide how to parse PDF files. "text", "text_with_img", "page_as_img"
        """
        pdf_parse_mode: Literal["text", "text_with_img", "page_as_img"]
        self.path_list = file_list
        self.output_path = output_path
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path, exist_ok=True)
        self.pdf_parse_mode = pdf_parse_mode
        self.use_segment = use_segment
        self.max_seg_text_len = max_seg_text_len
        self.max_seg_page_cnt = max_seg_page_cnt
        self.seg_overlap = seg_overlap

        self.files = {}
        self.load_files()
        """
        files: {
            "X:/xxx.pdf": {
                # must have attributes
                "type": "pdf" or "txt" or "img" or "unknown"
                "segments": [{"text": "text", "img": [img1, img2]}, {seg2}, {...}]

                # below optional attributes
                "result": [parsed_json1, parsed_json2, ...]
                
                "text": "all_my_texts"
                "img": "page1_img1_base64"
                "paged_text": ["page1", "page2", "page3"]
                "paged_img": [[page1_img1_base64, p1_img2, ...], [page2_img_1_base64], ..],
                "mode": "text_with_img", (pdf)
            },
        }
        """

    def get_file_names(self):
        return self.files.keys()

    def get_file_count(self):
        return len(self.files)

    def get_segments(self, filename):
        return self.files[filename]['segments']

    @staticmethod
    def strip_file_name(s: str):
        return Path(s).name

    def append_result_for_file(self, filename: str, result: List[str]):
        if filename not in self.files:
            raise ValueError(f"File {filename} not found.")
        if 'result' not in self.files[filename]:
            self.files[filename]['result'] = []
        base_id = len(self.files[filename]['result'])
        self.files[filename]['result'].extend(result)
        for cnt, content in enumerate(result):
            output_file = Path(self.output_path) / f"{self.strip_file_name(filename)}" \
                                                   f"_output_{base_id + cnt + 1}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

    def append_log_for_file(self, filename: str, log):
        if filename not in self.files:
            raise ValueError(f"File {filename} not found.")
        if 'log_id' not in self.files[filename]:
            self.files[filename]['log_id'] = 0
        self.files[filename]['log_id'] += 1
        log_id = self.files[filename]['log_id']
        output_file = Path(self.output_path) / f"{self.strip_file_name(filename)}" \
                                               f"_log_{log_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(log, ensure_ascii=False, indent=2))


    @staticmethod
    def segment_text(s, max_len, overlap):
        if max_len <= overlap:
            raise ValueError("Segment max_len <= overlap")
        result = []
        cur_pos = 0
        while cur_pos + overlap < len(s):
            result.append(s[cur_pos: cur_pos+max_len])
            cur_pos += max_len - overlap
        return result

    @staticmethod
    def segment_pages(page_list, max_len, overlap):
        if max_len <= overlap:
            raise ValueError("Segment max_len <= overlap")
        segments = []
        cur_pos = 0
        while cur_pos + overlap < len(page_list):
            segments.append(page_list[cur_pos: cur_pos+max_len])
            cur_pos += max_len - overlap
        result = []
        for cid, pages in enumerate(segments):
            all_text = []
            all_imgs = []
            for p in pages:
                if p['text']:
                    all_text.append(p['text'])
                if p['img']:
                    all_imgs.extend(p['img'])
            all_text = '\n\n'.join(all_text) if all_text else None
            result.append({
                "text": all_text,
                "img": all_imgs
            })
        return result

    def load_files(self):
        for file in self.path_list:
            if file.endswith(".txt"):
                text = read_txt(file)
                if self.use_segment:
                    segments = self.segment_text(text, self.max_seg_text_len, self.seg_overlap)
                else:
                    segments = [text]
                self.files[file] = {
                    "type": "txt",
                    "text": text,
                    "segments": [{"text": i, "img": []} for i in segments],
                }

            if file.endswith(".pdf"):
                if self.pdf_parse_mode == "text":
                    ptxt, pimg = pdf_reader(file)
                    text = "\n\n".join(ptxt)
                    if self.use_segment:
                        segments = self.segment_text(text, self.max_seg_text_len, self.seg_overlap)
                    else:
                        segments = [text]
                    self.files[file] = {
                        "type": "pdf",
                        "text": text,
                        "segments": [{"text": i, "img": []} for i in segments],
                        "paged_text": ptxt,
                        "mode": "text",
                    }
                elif self.pdf_parse_mode == "text_with_img":
                    ptxt, pimg = pdf_reader(file)
                    pages = [{"text": i, "img": j} for i, j in zip(ptxt, pimg)]
                    self.files[file] = {
                        "type": "pdf",
                        "paged_text": ptxt,
                        "paged_img": pimg,
                        "segments": self.segment_pages(pages, self.max_seg_page_cnt, self.seg_overlap),
                        "mode": "text_with_img",
                    }
                elif self.pdf_parse_mode == "page_as_img":
                    pimg = pdf_render_img(file)
                    pages = [{"text": None, "img": j} for j in pimg]
                    self.files[file] = {
                        "type": "pdf",
                        "pimg": pimg,
                        "segments": self.segment_pages(pages, self.max_seg_page_cnt, self.seg_overlap),
                        "mode": "page_as_img",
                    }
            if file.endswith("png") or file.endswith("jpg") or file.endswith("jpeg"):
                img = read_img(file)
                self.files[file] = {
                    "type": "img",
                    "img": img,
                    "segments": [{"text": None, "img": img}]
                }
            if file not in self.files:
                self.files[file] = {
                    "type": "unknown"
                }






