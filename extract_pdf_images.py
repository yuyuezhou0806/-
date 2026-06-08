import fitz, os

doc = fitz.open(r'C:\Users\admin\Desktop\拟定AI出图项目更新 (1).pdf')
out_dir = r'C:\Users\admin\Desktop\aigc_reference_images'
os.makedirs(out_dir, exist_ok=True)

count = 0
for i in range(doc.page_count):
    page = doc[i]
    images = page.get_images(full=True)
    for idx, img in enumerate(images):
        xref = img[0]
        base = doc.extract_image(xref)
        w, h = base['width'], base['height']
        if w > 100 and h > 100:
            count += 1
            ext = base['ext']
            fname = os.path.join(out_dir, f'ref_{count:02d}_p{i+1}.{ext}')
            with open(fname, 'wb') as f:
                f.write(base['image'])
            print(f'ref_{count:02d} - Page {i+1} - {w}x{h}')

print(f'\nDone: {count} images -> 桌面/aigc_reference_images/')
