from PIL import Image, ImageDraw
import os

SIZE = 1024
img = Image.new("RGBA", (SIZE, SIZE), (25, 27, 32, 255))
draw = ImageDraw.Draw(img)

# White rounded-square base
draw.rounded_rectangle(
    (100, 100, 924, 924),
    radius=150,
    fill=(245, 245, 245, 255)
)

# Fox ears
draw.polygon(
    [(270, 390), (300, 190), (465, 315)],
    fill=(242, 112, 25, 255)
)
draw.polygon(
    [(554, 315), (724, 190), (754, 390)],
    fill=(242, 112, 25, 255)
)

# Fox head
draw.ellipse(
    (245, 275, 779, 735),
    fill=(242, 112, 25, 255)
)

# Inner face
draw.polygon(
    [(350, 390), (674, 390), (620, 650), (404, 650)],
    fill=(247, 178, 45, 255)
)

# White muzzle
draw.ellipse(
    (385, 520, 639, 710),
    fill=(250, 250, 250, 255)
)

# Eyes
draw.ellipse((365, 455, 425, 520), fill=(30, 30, 30, 255))
draw.ellipse((599, 455, 659, 520), fill=(30, 30, 30, 255))

# Nose
draw.polygon(
    [(480, 545), (544, 545), (512, 585)],
    fill=(30, 30, 30, 255)
)

# Code/evolution path
draw.line(
    [(300, 805), (410, 755), (520, 805), (630, 755), (740, 805)],
    fill=(242, 112, 25, 255),
    width=24
)
for x, y in [(300, 805), (410, 755), (520, 805), (630, 755), (740, 805)]:
    draw.ellipse(
        (x - 25, y - 25, x + 25, y + 25),
        fill=(247, 178, 45, 255)
    )

# Gold arc
draw.arc(
    (215, 215, 809, 809),
    start=205,
    end=335,
    fill=(247, 178, 45, 255),
    width=18
)

base_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(base_dir, "assets")
os.makedirs(assets_dir, exist_ok=True)
output = os.path.join(assets_dir, "foxvc-icon.png")
img.save(output, "PNG")
print(f"Created: {output}")
print(f"Size: {SIZE}x{SIZE}")
