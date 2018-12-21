from flask import Flask, request, send_from_directory, render_template, send_file
app = Flask(__name__, static_url_path='')

import numpy as np
from io import BytesIO
import glob

from AnsiGraphics import AnsiGraphics
from AnsiImage import AnsiImage
from AnsiPalette import AnsiPalette

ansi_graphics = AnsiGraphics('config/cp866_8x16.fnt', 8, 16)

pal_styles = ""
for i in range(16):
    col = np.floor(np.array(ansi_graphics.cga_colour(i)) * 255.0)
    pal_entry = ".fg" + str(i) + "{\n"
    pal_entry += "    color: rgb(" + str(col[0]) + ", " + str(col[1]) + ", " + str(col[2]) + ");\n"
    pal_entry += "}\n\n"
    pal_entry += ".bg" + str(i) + "{\n"
    pal_entry += "    background: rgb(" + str(col[0]) + ", " + str(col[1]) + ", " + str(col[2]) + ");\n"
    pal_entry += "}\n\n"
    pal_styles += pal_entry


@app.route('/')
def file_list():
    file_list = list(glob.glob('*.ans'))
    list_html = '<h1>Files</h1><div style="text-align: left; font-size: 28px; width: 600px;">'
    for ansi_file in file_list:
        list_html += '--> <a href="/view/' + ansi_file + '">' + ansi_file + '</a><br/>'
    list_html += "</div>"
    return(render_template("default.html", title="files", content=list_html))
           
@app.route('/view/<path:path>')
def render_ansi(path):
    try:
        ansi_image = AnsiImage(ansi_graphics)
        ansi_image.clear_image(80, 24)
        ansi_image.load_ans(path, False)
        width, height = ansi_image.get_size()
    except:
       return(render_template("default.html", title="Loading error, sorry."))
    
    html_ansi = ""
    for y in range(height):
        for x in range(width):
            char = ansi_image.get_cell(x, y)
            html_ansi += '<span class="fg' + str(char[1]) + ' bg' + str(char[2]) + '">'
            html_ansi += chr(char[0])
            html_ansi += '</span>'
        html_ansi += "\n"
    return(render_template("default.html", title=path, styles=pal_styles, content=html_ansi, show_dl=True))

@app.route('/image/<path:path>')
def render_ansi_png(path):
    transparent = False
    if request.args.get('transparent', False) != False:
        transparent = True
    try:
        ansi_image = AnsiImage(ansi_graphics)
        ansi_image.clear_image(80, 24)
        ansi_image.load_ans(path, False)
        bitmap = ansi_image.to_bitmap(transparent = transparent)
    except:
       return(render_template("default.html", title="Loading error, sorry."))
   
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
    
