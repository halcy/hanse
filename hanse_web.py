from flask import Flask, request, send_from_directory, render_template, send_file, redirect
from werkzeug.contrib.cache import SimpleCache

app = Flask(__name__, static_url_path='')
cache = SimpleCache()
app_root = "hanseweb"
base_path = "images/"

import numpy as np
from io import BytesIO
import glob
import requests

from AnsiGraphics import AnsiGraphics
from AnsiImage import AnsiImage
from AnsiPalette import AnsiPalette

ansi_graphics = AnsiGraphics('config/cp866_8x16.fnt', 8, 16)

pal_styles = ""
for i in range(16):
    col = np.array(np.floor(np.array(ansi_graphics.cga_colour(i)) * 255.0), 'int')
    pal_entry = ".fg" + str(i) + "{\n"
    pal_entry += "    color: rgba(" + str(col[0]) + ", " + str(col[1]) + ", " + str(col[2]) + ", 0);\n"
    pal_entry += "}\n\n"
    pal_entry += ".bg" + str(i) + "{\n"
    pal_entry += "    background: rgba(" + str(col[0]) + ", " + str(col[1]) + ", " + str(col[2]) + ", 0);\n"
    pal_entry += "}\n\n"
    pal_styles += pal_entry

def get_remote_file(url, max_size = 200*1024):
    r = requests.get(url, stream=True)
    r.raise_for_status()

    if int(r.headers.get('Content-Length')) > max_size:
        raise ValueError('response too large')

    size = 0
    content = b""
    for chunk in r.iter_content(1024):
        size += len(chunk)
        if size > max_size:
            raise ValueError('response too large')
        content += chunk
    return content

def load_ansi(path):
    if ".." in path or path[0] == '/':
        raise(ValueError("dangerous."))
              
    wide_mode = False
    if request.args.get('wide', False) != False:
        wide_mode = True    
    
    ansi_image = AnsiImage(ansi_graphics)
    ansi_image.clear_image(1, 1)
    
    if path[0:4] == 'http':
        ansi_data = get_remote_file(path)
        ansi_image.parse_ans(ansi_data, wide_mode = wide_mode)
    else:
        ansi_image.load_ans(base_path + path, wide_mode = wide_mode)
    return ansi_image

@app.route('/', methods = ['GET', 'POST'])
def file_list():
    if request.form.get('load_url', None) != None:
        return(redirect('/view/' + request.form.get('load_url', None), code=302))
        
    file_list = list(glob.glob(base_path + '*.ans'))
    list_html = '<h1>Files</h1><div style="text-align: left; font-size: 28px; width: 600px;">'
    for ansi_file in file_list:
        ansi_file = ansi_file[len(base_path):]
        list_html += '--> <a href="/' + app_root + '/view/' + ansi_file + '">' + ansi_file + '</a><br/>'
    list_html += '<a href="/' + app_root + '/gallery">gallery</a>'
    list_html += '<form method="post" action="/' + app_root + '">url: <input type="text" name="load_url" style="width: 600px;"></input> <input type="submit" value="load"></input></form></div>'
    return(render_template("default.html", title="files", content=list_html, app_root=app_root))

@app.route('/gallery')
def gallery():
    file_list = list(glob.glob(base_path + '*.ans'))
    list_html = '<h1>Gallery</h1><div style="text-align: left; font-size: 28px;" class="gallery">'
    for ansi_file in file_list:
        ansi_file = ansi_file[len(base_path):]
        list_html += '<a href="/' + app_root + '/view/' + ansi_file + '"><img src="/' + app_root + '/image/' + ansi_file + '?thumb"></img></a>'
    list_html += '<a href="/' + app_root + '"><-- back</a></div>'
    return(render_template("default.html", title="gallery", content=list_html, app_root=app_root))

@app.route('/view/<path:path>')
def render_ansi(path):
    try:
        ansi_image = load_ansi(path)
    except:
        return(render_template("default.html", title="Loading error, sorry.", content="<h3>Loading error, sorry</h3>", app_root = app_root))
    width, height = ansi_image.get_size()
    
    html_ansi = ""
    html_ansi += '<div style="text-align: left; font-size: 28px;"><a href="/' + app_root + '"><-- back</a></div>'
    html_ansi += '<div style="display:inline-block; background:url(' + "'/" + app_root + '/image/' + path + "'" + ');">'
    for y in range(height):
        for x in range(width):
            char = ansi_image.get_cell(x, y)
            html_ansi += '<span class="fg' + str(char[1]) + ' bg' + str(char[2]) + '">'
            if char[0] < 32:
                char[0] = 32
            html_ansi += chr(char[0])
            html_ansi += '</span>'
        html_ansi += "\n"
    html_ansi += '</div>'
    return(render_template("default.html", title=path, styles=pal_styles, content=html_ansi, show_dl=True, app_root=app_root))

@app.route('/ansi/<path:path>')
def send_ansi(path):
    try:
        ansi_image = load_ansi(path)
    except:
        return(render_template("default.html", title="Loading error, sorry.", content="<h3>Loading error, sorry</h3>", app_root=app_root))
    img_io = BytesIO()
    img_io.write(ansi_image.to_ans())
    img_io.seek(0)
    return send_file(img_io, mimetype='plain/text')

@app.route('/image/<path:path>')
def render_ansi_png(path):
    transparent = False
    thumb = False
    
    if request.args.get('transparent', None) != None:
        transparent = True
    if request.args.get('thumb', None) != None:
        thumb = True    
    
    cached = cache.get(request.url)
    if not cached is None:
        bitmap = cached
    else:
        try:
            ansi_image = load_ansi(path)
        except:
            return(render_template("default.html", title="Loading error, sorry.", content="<h3>Loading error, sorry</h3>", app_root=app_root))

        bitmap = ansi_image.to_bitmap(transparent = transparent)
        if thumb == True:
            bitmap.thumbnail((256, 256))
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
    
