from PIL import Image, ImageDraw, ImageFont
import random
import base64
from io import BytesIO

def generate_captcha() -> str:
    # 随机生成验证码文本
    captcha_text = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=4))
    
    # 生成验证码图片
    image = Image.new('RGB', (120, 30), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 5), captcha_text, fill=(0, 0, 0))
    
    # 将图片保存为 Base64 编码的字符串
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return captcha_text, img_str
