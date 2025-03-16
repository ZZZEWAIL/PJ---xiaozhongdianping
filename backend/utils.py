from PIL import Image, ImageDraw, ImageFont
import random
import base64
from io import BytesIO
import string
from fastapi import HTTPException

def generate_captcha() -> tuple[str, str]:
    try:
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        image = Image.new('RGB', (150, 50), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        for _ in range(100):
            x = random.randint(0, 149)
            y = random.randint(0, 49)
            draw.point((x, y), fill=(random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)))
        
        try:
            font = ImageFont.load_default()
        except Exception as e:
            print(f"Font loading failed: {e}")
            raise HTTPException(status_code=500, detail=f"Font loading failed: {str(e)}")
        
        for i, char in enumerate(captcha_text):
            color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 200))
            x = 10 + i * 35
            y = 10 + random.randint(-5, 5)
            draw.text((x, y), char, fill=color, font=font)
        
        params = [
            1 - float(random.randint(1, 2)) / 100,
            0,
            0,
            0,
            1 - float(random.randint(1, 10)) / 100,
            float(random.randint(1, 2)) / 500,
            0,
            0
        ]
        image = image.transform(image.size, Image.PERSPECTIVE, params, Image.BICUBIC)
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return captcha_text, img_str
    except Exception as e:
        print(f"Error in generate_captcha: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate captcha: {str(e)}")