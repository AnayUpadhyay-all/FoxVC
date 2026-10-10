from PIL import Image, ImageDraw

SIZE = 1024

img = Image.new("RGBA", (SIZE, SIZE), (24, 25, 29, 255))
draw = ImageDraw.Draw(img)

ORANGE = (245, 126, 32, 255)
GOLD = (255, 190, 55, 255)
WHITE = (248, 248, 245, 255)
DARK = (24, 25, 29, 255)

# Main rounded icon
draw.rounded_rectangle(
    (70, 70, 954, 954),
    radius=190,
    fill=WHITE
)

# Fox silhouette
fox = [
    (270, 365),
    (350, 185),
    (455, 285),
    (512, 250),
    (569, 285),
    (674, 185),
    (754, 365),
    (735, 590),
    (650, 720),
    (512, 785),
    (374, 720),
    (289, 590)
]

draw.polygon(fox, fill=ORANGE)

# Inner face
face = [
    (335, 390),
    (405, 330),
    (512, 365),
    (619, 330),
    (689, 390),
    (668, 555),
    (610, 650),
    (512, 700),
    (414, 650),
    (356, 555)
]

draw.polygon(face, fill=GOLD)

# White muzzle
muzzle = [
    (400, 525),
    (512, 460),
    (624, 525),
    (585, 625),
    (512, 680),
    (439, 625)
]

draw.polygon(muzzle, fill=WHITE)

# Eyes
draw.polygon(
    [(380, 435), (450, 405), (468, 465), (410, 475)],
    fill=DARK
)

draw.polygon(
    [(644, 435), (574, 405), (556, 465), (614, 475)],
    fill=DARK
)

# Nose
draw.polygon(
    [(487, 535), (512, 520), (537, 535), (512, 558)],
    fill=DARK
)

# Code/evolution path
code_path = [
    (350, 790),
    (430, 835),
    (512, 790),
    (594, 835),
    (674, 790)
]

draw.line(
    code_path,
    fill=ORANGE,
    width=28,
    joint="curve"
)

# Code nodes
for x in (390, 512, 634):
    draw.ellipse(
        (x - 10, 810, x + 10, 830),
        fill=DARK
    )

# Technical accent
draw.arc(
    (125, 125, 899, 899),
    start=205,
    end=335,
    fill=GOLD,
    width=10
)

# Save as REAL PNG
output = "foxvc-icon.png"

img.save(
    output,
    "PNG",
    optimize=True
)

print("FoxVC icon generated successfully.")
print("File:", output)
print("Size:", SIZE, "x", SIZE)
print("Format: PNG")
