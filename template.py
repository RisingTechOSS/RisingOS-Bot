import cairocffi as cairo
from io import BytesIO

def generate(codename, maintainer, font_size=20, text_color="#E9E9E9", text_x=45, text_y=130): #Define some variables like text colour, xy, blah blah
    template_surface = cairo.ImageSurface.create_from_png('template.png')
    img_width, img_height = template_surface.get_width(), template_surface.get_height()
    img_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_width, img_height)
    ctx = cairo.Context(img_surface)
    ctx.set_source_surface(template_surface)
    ctx.paint()
    font = cairo.ToyFontFace('template.ttf', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_face(font)
    ctx.set_font_size(font_size)
    text = f"for < {codename} by {maintainer} >" #Message to include inside banner
    text_width, text_height = ctx.text_extents(text)[2:4]
    x = text_x
    y = text_y
    ctx.move_to(x, y)
    ctx.set_source_rgba(int(text_color[1:3], 16)/255, int(text_color[3:5], 16)/255, int(text_color[5:7], 16)/255, 1)
    ctx.show_text(text)
    buffer = BytesIO()
    img_surface.write_to_png(buffer)
    buffer.seek(0)
    return buffer
