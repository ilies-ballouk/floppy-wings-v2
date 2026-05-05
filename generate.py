from PIL import Image, ImageDraw
import math, struct, zlib, os

def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size

    def sc(v): return v * s / 512

    # Rounded rect background clip (approximate with rounded rect fill)
    radius = sc(114)
    # Draw background gradient manually via circles + rects
    # Background: dark purple to near-black
    for i in range(size):
        t = i / size
        r = int(26 * (1 - t) + 6 * t)
        g = int(10 * (1 - t) + 6 * t)
        b = int(62 * (1 - t) + 15 * t)
        d.line([(0, i), (size, i)], fill=(r, g, b, 255))

    # Mask to rounded rect
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    rx = int(radius)
    md.rounded_rectangle([0, 0, size-1, size-1], radius=rx, fill=255)
    img.putalpha(mask)
    # Recomposite bg with mask
    bg = Image.new("RGBA", (size, size), (0,0,0,0))
    bg_draw = ImageDraw.Draw(bg)
    for i in range(size):
        t = i / size
        r = int(26 * (1-t) + 6*t)
        g = int(10 * (1-t) + 6*t)
        b = int(62 * (1-t) + 15*t)
        bg_draw.line([(0,i),(size,i)], fill=(r,g,b,255))
    bg.putalpha(mask)
    img = bg.copy()
    d = ImageDraw.Draw(img)

    def ellipse(cx, cy, rx, ry, fill, alpha=255, angle=0):
        cx, cy, rx, ry = sc(cx), sc(cy), sc(rx), sc(ry)
        if alpha < 255:
            overlay = Image.new("RGBA", (size, size), (0,0,0,0))
            od = ImageDraw.Draw(overlay)
            fr = (fill[0], fill[1], fill[2], alpha)
            od.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=fr)
            img.alpha_composite(overlay)
        else:
            d.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=fill)

    def star(cx, cy, r, alpha=180):
        cx, cy, r = sc(cx), sc(cy), sc(r)
        overlay = Image.new("RGBA", (size, size), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255,255,255,alpha))
        img.alpha_composite(overlay)

    # Stars
    stars = [
        (83,72,1.7,165),(155,117,1.2,127),(418,64,1.4,153),
        (449,148,1.1,102),(57,204,1.4,127),(471,234,1.4,140),
        (226,57,1.5,153),(343,95,1.1,115),(98,370,1.2,89),
        (437,400,1.1,97),(45,422,1.4,115),(468,453,1.0,76),
        (256,460,1.2,82),(370,430,1.1,89),
    ]
    for sx,sy,sr,sa in stars:
        star(sx,sy,sr,sa)

    # Glow
    for i in range(12):
        t = 1 - i/12
        a = int(28 * t * t * 0.7)
        ellipse(256, 286, 166*(1-i*0.04), 68*(1-i*0.04), (124,0,255), a)

    # Trail
    ellipse(82, 253, 15, 10, (255,230,0), 25)
    ellipse(119, 248, 20, 12, (255,230,0), 41)
    ellipse(161, 244, 23, 14, (255,230,0), 56)

    # Wing (rotated ellipse approximation)
    wing_overlay = Image.new("RGBA", (size, size), (0,0,0,0))
    wd = ImageDraw.Draw(wing_overlay)
    wcx, wcy = sc(210), sc(280)
    wrx, wry = sc(69), sc(38)
    wd.ellipse([wcx-wrx, wcy-wry, wcx+wrx, wcy+wry], fill=(255,193,7,255))
    wing_overlay = wing_overlay.rotate(18, center=(wcx, wcy))
    img.alpha_composite(wing_overlay)

    # Wing highlight
    wh_overlay = Image.new("RGBA", (size, size), (0,0,0,0))
    whd = ImageDraw.Draw(wh_overlay)
    whcx, whcy = sc(201), sc(272)
    whrx, whry = sc(39), sc(20)
    whd.ellipse([whcx-whrx, whcy-whry, whcx+whrx, whcy+whry], fill=(255,224,102,107))
    wh_overlay = wh_overlay.rotate(18, center=(whcx, whcy))
    img.alpha_composite(wh_overlay)

    # Body gradient
    body_overlay = Image.new("RGBA", (size, size), (0,0,0,0))
    bd = ImageDraw.Draw(body_overlay)
    bcx, bcy = sc(268), sc(252)
    brx, bry = sc(134), sc(107)
    # Simple radial gradient via concentric ellipses
    steps = 40
    for i in range(steps, 0, -1):
        t = i / steps
        r = int(255 * (1 - t) + 255 * t * 0.7)
        g = int(247 * (1-t)*0.3 + 230 * t)
        b = int(160 * (1-t)*0.0)
        rx2 = brx * t
        ry2 = bry * t
        # gradient from outside in: ff8c00 -> ffe600 -> fff7a0
        if t > 0.55:
            tt = (t - 0.55) / 0.45
            r = int(255 * 1)
            g = int(140 + (230-140)*tt)  # ff8c00 -> ffe600
            b = 0
        else:
            tt = t / 0.55
            r = 255
            g = int(230 + (247-230)*tt)  # ffe600 -> fff7a0
            b = int(0 + 160*tt)
        bd.ellipse([bcx-rx2, bcy-ry2, bcx+rx2, bcy+ry2], fill=(r,g,b,255))
    img.alpha_composite(body_overlay)

    # Body stroke
    d2 = ImageDraw.Draw(img)
    sw = max(2, int(sc(5.5)))
    d2.ellipse([bcx-brx, bcy-bry, bcx+brx, bcy+bry], outline=(255,102,0,255), width=sw)

    # Belly highlight
    ellipse(252, 274, 79, 54, (255,247,204), 64)

    # Cheek
    ellipse(313, 272, 35, 22, (255,128,128), 133)

    # Eye white
    ecx, ecy = sc(337), sc(220)
    erx, ery = sc(45), sc(43)
    d2.ellipse([ecx-erx, ecy-ery, ecx+erx, ecy+ery], fill=(255,255,255,255))

    # Pupil
    pcx, pcy = sc(350), sc(215)
    pr = sc(23)
    d2.ellipse([pcx-pr, pcy-pr, pcx+pr, pcy+pr], fill=(26,26,26,255))

    # Shine
    sh1x, sh1y, sh1r = sc(358), sc(205), sc(9)
    d2.ellipse([sh1x-sh1r, sh1y-sh1r, sh1x+sh1r, sh1y+sh1r], fill=(255,255,255,255))
    sh2x, sh2y, sh2r = sc(341), sc(228), sc(4)
    overlay2 = Image.new("RGBA", (size, size), (0,0,0,0))
    od2 = ImageDraw.Draw(overlay2)
    od2.ellipse([sh2x-sh2r, sh2y-sh2r, sh2x+sh2r, sh2y+sh2r], fill=(255,255,255,140))
    img.alpha_composite(overlay2)

    # Beak
    bx1, by1 = sc(386), sc(224)
    bx2, by2 = sc(473), sc(243)
    bx3, by3 = sc(386), sc(265)
    d2.polygon([(bx1,by1),(bx2,by2),(bx3,by3)], fill=(255,109,0,255))
    # Beak shadow
    beak_shadow = Image.new("RGBA", (size, size), (0,0,0,0))
    bsd = ImageDraw.Draw(beak_shadow)
    bsx1,bsy1 = sc(386),sc(248)
    bsx2,bsy2 = sc(458),sc(243)
    bsx3,bsy3 = sc(386),sc(265)
    bsd.polygon([(bsx1,bsy1),(bsx2,bsy2),(bsx3,bsy3)], fill=(204,68,0,115))
    img.alpha_composite(beak_shadow)

    # Apply rounded rect mask again to clip everything
    final_mask = Image.new("L", (size, size), 0)
    fmd = ImageDraw.Draw(final_mask)
    fmd.rounded_rectangle([0,0,size-1,size-1], radius=int(size*114/512), fill=255)
    img.putalpha(final_mask)

    return img

sizes = [512, 192, 180, 32, 16]
os.makedirs("/home/claude/floppy-wings-icons", exist_ok=True)

for sz in sizes:
    icon = draw_icon(sz)
    icon.save(f"/home/claude/floppy-wings-icons/icon-{sz}.png")
    print(f"Generated icon-{sz}.png")

# Also generate favicon.ico (multi-size)
icons_for_ico = [draw_icon(s) for s in [16, 32, 48]]
icons_for_ico[0].save(
    "/home/claude/floppy-wings-icons/favicon.ico",
    format="ICO",
    sizes=[(16,16),(32,32),(48,48)],
    append_images=icons_for_ico[1:]
)
print("Generated favicon.ico")
print("All done!")
