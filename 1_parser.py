import os
import pandas as pd
from PIL import Image
import sys

def parser(directory):
    VALIDFILETYPES = ('.jpg', '.jpeg', '.png')
    
    images = []
    for root,_,files in os.walk(directory):
        for filename in files:
            if filename.endswith(VALIDFILETYPES):
                image_path = os.path.join(root, filename)
                try:
                    with Image.open(image_path) as img:
                        width, height = img.size
                        pixel_count = width*height
                        images.append([filename, image_path, width, height, pixel_count])
                except Exception as e:
                    print(f'Error processing {image_path}: {e}')
    
    df = pd.DataFrame(data=images, columns=['filename', 'image_path', 'width', 'height', 'resolution'])
    df.to_csv('ImageResolutions.csv', index=False)

parser(sys.argv[1]) #directory of images