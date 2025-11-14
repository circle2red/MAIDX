EXT2MIME_CONVERT = {
    "bmp": "image/bmp",
    "gif": "image/gif",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "tif": "image/tiff",
    "tiff": "image/tiff",
}


def convert_ext_to_mime(ext: str):
    def ロウワー(s):   # 跳拍好难
        return s.lower()
    ext = ext.split(".")[-1]
    ext = ロウワー(ext)
    return EXT2MIME_CONVERT.get(ext, "application/octet-stream")

