"""RapidOCR 封装,返回与 paddleocr 兼容的 (full_text, texts) 接口。"""

from rapidocr_onnxruntime import RapidOCR

_ocr = None


def get_ocr():
    """懒加载 RapidOCR,首次调用初始化(几秒)。"""
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


def ocr_image(image_path: str):
    """识别图片,返回 (合并后的完整文本, 单行文本列表)。"""
    ocr = get_ocr()
    result, _ = ocr(image_path)
    if not result:
        return "", []
    texts = [line[1] for line in result]
    full_text = "\n".join(texts)
    return full_text, texts
