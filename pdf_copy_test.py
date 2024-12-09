import pymupdf
doc = pymupdf.open("./test/原图.pdf")
page = doc[0]
paths = page.get_drawings()  # extract existing drawings
# this is a list of "paths", which can directly be drawn again using Shape
# -------------------------------------------------------------------------
#
# define some output page with the same dimensions
outpdf = pymupdf.open()
outpage = outpdf.new_page(width=page.rect.width, height=page.rect.height)
shape = outpage.new_shape()  # make a drawing canvas for the output page
# --------------------------------------
# loop through the paths and draw them
# --------------------------------------
for path in paths:
    # ------------------------------------
    # draw each entry of the 'items' list
    # ------------------------------------
    for item in path["items"]:  # these are the draw commands
        if item[0] == "l":  # line
            shape.draw_line(item[1], item[2])
        elif item[0] == "re":  # rectangle
            shape.draw_rect(item[1])
        elif item[0] == "qu":  # quad
            shape.draw_quad(item[1])
        elif item[0] == "c":  # curve
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        else:
            raise ValueError("unhandled drawing", item)
    # ------------------------------------------------------
    # all items are drawn, now apply the common properties
    # to finish the path
    # ------------------------------------------------------
    fill=path["fill"] if path["fill"] else None,  # fill color
    color=path["color"] if path["color"] else None,  # line color
    dashes=path["dashes"] if path["dashes"] else None,  # line dashing
    even_odd=path.get("even_odd", True),  # control color of overlaps
    closePath=path["closePath"] if path["closePath"] else None,  # whether to connect last and first point
    lineJoin=path["lineJoin"] if path["lineJoin"] else None,  # how line joins should look like
    lineCap=max(path["lineCap"]) if path["lineCap"] else None,  # how line ends should look like
    width=path["width"] if path["width"] else None,  # line width
    stroke_opacity=path.get("stroke_opacity", 1)
    fill_opacity=path.get("fill_opacity", 1)

    if isinstance(color, tuple) and len(color) == 1:
        color = color[0]
    if isinstance(fill, tuple) and len(fill) == 1:
        fill = fill[0]
    if isinstance(lineCap, tuple) and len(lineCap) == 1:
        lineCap = lineCap[0]
    if isinstance(lineJoin, tuple) and len(lineJoin) == 1:
        lineJoin = lineJoin[0]

    # defaults
    if fill is None: fill = None # continuous line
    if color is None: color = None # black
    if dashes is None: dashes = None # no dashes
    if even_odd is None: even_odd = True
    if closePath is None: closePath = False # do not close
    if lineJoin is None: lineJoin = 0 # sharp line
    if lineCap is None: lineCap = 0 # sharp edge
    if width is None: width = 1.0
    if stroke_opacity is None: stroke_opacity = 1.0
    if fill_opacity is None: fill_opacity = 1.0

    # print(f'[debug] color = {color}')
    # print(f'[debug] fill = {fill}')
    # print(f'[debug] linecap = {lineCap}')

    shape.finish(
        fill=fill,
        color=color,
        dashes=dashes,
        even_odd=even_odd,
        closePath=closePath,
        lineJoin=lineJoin,
        lineCap=lineCap,
        width=width,
        stroke_opacity=stroke_opacity,
        fill_opacity=fill_opacity,
        )
# all paths processed - commit the shape to its page
shape.commit()
outpdf.save("drawings-page-0.pdf")