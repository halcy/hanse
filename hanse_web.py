from flask import Flask, request, send_from_directory, render_template, send_file
from werkzeug.contrib.cache import SimpleCache

app = Flask(__name__, static_url_path='')
cache = SimpleCache()

base_path = "images/"

import numpy as np
from io import BytesIO
import glob

from AnsiGraphics import AnsiGraphics
from AnsiImage import AnsiImage
from AnsiPalette import AnsiPalette

ansi_graphics = AnsiGraphics('config/cp866_8x16.fnt', 8, 16)

pal_styles = ""
for i in range(16):
    col = np.array(np.floor(np.array(ansi_graphics.cga_colour(i)) * 255.0), 'int')
    pal_entry = ".fg" + str(i) + "{\n"
    pal_entry += "    color: rgb(" + str(col[0]) + ", " + str(col[1]) + ", " + str(col[2]) + ");\n"
    pal_entry += "}\n\n"
    pal_entry += ".bg" + str(i) + "{\n"
    pal_entry += "    background: rgb(" + str(col[0]) + ", " + str(col[1]) + ", " + str(col[2]) + ");\n"
    pal_entry += "}\n\n"
    pal_styles += pal_entry


@app.route('/')
def file_list():
    file_list = list(glob.glob(base_path + '*.ans'))
    list_html = '<h1>Files</h1><div style="text-align: left; font-size: 28px; width: 600px;">'
    for ansi_file in file_list:
        ansi_file = ansi_file[len(base_path):]
        list_html += '--> <a href="/view/' + ansi_file + '">' + ansi_file + '</a><br/>'
    list_html += '<a href="/gallery">gallery</a></div>'
    return(render_template("default.html", title="files", content=list_html))

@app.route('/gallery')
def gallery():
    file_list = list(glob.glob(base_path + '*.ans'))
    list_html = '<h1>Gallery</h1><div style="text-align: left; font-size: 28px;" class="gallery">'
    for ansi_file in file_list:
        ansi_file = ansi_file[len(base_path):]
        list_html += '<a href="/view/' + ansi_file + '"><img src="/image/' + ansi_file + '?thumb"></img></a>'
    list_html += '<a href="/"><-- back</a></div>'
    return(render_template("default.html", title="gallery", content=list_html))

@app.route('/view/<path:path>')
def render_ansi(path):
    wide_mode = False
    if request.args.get('wide', False) != False:
        wide_mode = True    
        
    try:
        ansi_image = AnsiImage(ansi_graphics)
        ansi_image.clear_image(80, 24)
        ansi_image.load_ans(base_path + path, wide_mode = wide_mode)
        width, height = ansi_image.get_size()
    except:
       return(render_template("default.html", title="Loading error, sorry."))
    
    html_ansi = ""
    html_ansi += '<div style="text-align: left; font-size: 28px;"><a href="/"><-- back</a></div>'
    for y in range(height):
        for x in range(width):
            char = ansi_image.get_cell(x, y)
            html_ansi += '<span class="fg' + str(char[1]) + ' bg' + str(char[2]) + '">'
            if char[0] < 32:
                char[0] = 32
            html_ansi += chr(char[0])
            html_ansi += '</span>'
        html_ansi += "\n"
    return(render_template("default.html", title=path, styles=pal_styles, content=html_ansi, show_dl=True))

@app.route('/image/<path:path>')
def render_ansi_png(path):
    transparent = False
    wide_mode = False
    thumb = False
    
    if request.args.get('transparent', None) != None:
        transparent = True
    if request.args.get('wide', None) != None:
        wide_mode = True    
    if request.args.get('thumb', None) != None:
        thumb = True    
    
    cached = cache.get(request.url)
    if not cached is None:
        bitmap = cached
    else:
        try:
            ansi_image = AnsiImage(ansi_graphics)
            ansi_image.clear_image(1000, 1000)
            ansi_image.load_ans(base_path + path, wide_mode = wide_mode)
            bitmap = ansi_image.to_bitmap(transparent = transparent)
        except:
            return(render_template("default.html", title="Loading error, sorry."))
        if thumb == True:
            bitmap.thumbnail((128, 128))
        cache.set(request.url, bitmap)
        
    img_io = BytesIO()
    bitmap.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')
   
@app.route('/webfont/<path:path>')
def webfont(path):
    return send_from_directory('webfont', path)

if __name__ == "__main__":     
    port = 5000
    app.run(host='0.0.0.0', port=port)
    
