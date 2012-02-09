from flask import Flask, Response, abort, redirect, url_for

app = Flask(__name__)

from PIL import Image
from cStringIO import StringIO
import random

# http://www.freewebs.com/gatorshark/SpindaDocumentation.htm

spinda_conf = {
    'ruby': {
        'coords': [(0,0), (24,1), (6,18), (18,19)],
        'origin': (8,6),
        'size': (64,64),
        'palette': {
            'normal': [49, 165, 82, 247, 230, 173, 230, 214, 165, 197, 181, 132, 173, 148, 107, 222, 140, 74, 222, 107, 58, 181, 90, 41, 156, 58, 25, 115, 66, 16, 173, 66, 90, 255, 255, 0, 255, 255, 0, 123, 99, 74, 90, 66, 49, 16, 16, 16],
            'shiny': [49, 165, 82, 247, 230, 173, 230, 214, 165, 197, 181, 132, 173, 148, 107, 181, 197, 90, 148, 165, 58, 115, 132, 25, 82, 99, 0, 49, 66, 0, 173, 66, 90, 255, 255, 0, 255, 255, 0, 123, 99, 74, 90, 66, 49, 16, 16, 16],
        },
        'transform': {1: 5, 2: 6, 3: 7},
        'spots': [
            ['    ***     ',
             '  *******   ',
             ' *********  ',
             ' ********** ',
             '*********** ',
             '************',
             '************',
             '************',
             ' ********** ',
             ' ********** ',
             '  ********  ',
             '     ****   '],
            ['     ****    ',
             '   *******   ',
             '  *********  ',
             ' *********** ',
             ' *********** ',
             '*************',
             '*************',
             '*************',
             ' *********** ',
             ' *********** ',
             '  *********  ',
             '   ********  ',
             '     ***     '],
            ['  ***  ',
             ' ***** ',
             '*******',
             '*******',
             '*******',
             '*******',
             '*******',
             ' ***** ',
             '  ***  '],
            ['  ****  ',
             ' ****** ',
             '********',
             '********',
             '********',
             '********',
             '********',
             ' ****** ',
             '  ****  '],
        ],
    },
    'diamond': {
        'coords': [(0,0), (24,2), (3,18), (15,18)],
#-Sprite's origin: 7px left and 7px up from right ear.
        'origin': (17, 7),
        'size': (160, 80),
        'palette': {
            'normal': [49, 165, 82, 247, 239, 189, 230, 214, 165, 206, 165, 115, 156, 132, 90, 115, 82, 66, 239, 148, 123, 239, 82, 74, 189, 74, 49, 123, 66, 49, 230, 99, 115, 255, 255, 0, 247, 239, 189, 230, 214, 165, 206, 165, 115, 16, 16, 16],
            'shiny': [49, 165, 82, 247, 239, 189, 230, 214, 165, 206, 165, 115, 156, 132, 90, 115, 82, 66, 206, 214, 90, 165, 206, 16, 123, 156, 0, 123, 66, 49, 230, 99, 115, 255, 255, 0, 247, 239, 189, 230, 214, 165, 206, 165, 115, 16, 16, 16],
        },
        'transform': {2: 7, 3: 8},
        'spots': [
            ['  ****  ',
             ' ****** ',
             '********',
             '********',
             '********',
             '********',
             ' ****** ',
             '  ****  '],
            ['  ****  ',
             ' ****** ',
             '********',
             '********',
             '********',
             '********',
             ' ****** ',
             '  ****  '],
            ['  ***  ',
             ' ***** ',
             '*******',
             '*******',
             '*******',
             '*******',
             '*******',
             ' ***** ',
             '  ***  '],
            ['   ***   ',
             ' ******* ',
             '*********',
             '*********',
             '*********',
             '*********',
             '*********',
             '*********',
             ' ******* ',
             '   ***   '],
        ]
    }
}

spinda_conf['ruby']['image'] = list(Image.open('ruby/327.png').getdata())
spinda_conf['diamond']['image'] = list(Image.open('diamond/327.png').getdata())

def coords_from_pid(pid):
    return [
        (pid       & 0xf, pid >> 4  & 0xf),
        (pid >> 8  & 0xf, pid >> 12 & 0xf),
        (pid >> 16 & 0xf, pid >> 20 & 0xf),
        (pid >> 24 & 0xf, pid >> 28 & 0xf),
    ]

def add_coords(c0, c1):
    return (c0[0] + c1[0], c0[1] + c1[1])

def draw_spot(img, spot, coords, transform):
    data = img.load()

    dim = (len(spot[0]), len(spot))
    for x in range(dim[0]):
        for y in range(dim[1]):
            if spot[y][x] == '*':
                i = (int(coords[0]) + x, int(coords[1]) + y)
                p = data[i]
                p = transform.get(p, p)
                data[i] = p

def make_spinda(conf, pid, color='normal'):
    pixels = list(conf['image'])
    size = conf['size']

    spots = coords_from_pid(pid)
    spots = [add_coords(x, y) for x, y in zip(spots, conf['coords'])]
    spots = [add_coords(x, conf['origin']) for x in spots]

    img = Image.new('P', size)
    img.putdata(pixels)
    img.putpalette(conf['palette'][color])

    for coords, spot in zip(spots, conf['spots']):
        draw_spot(img, spot, coords, conf['transform'])

    alpha = Image.new('1', size)
    alpha.putdata([int(x != 0) for x in pixels])
    img.putalpha(alpha)

    buf = StringIO()
    img.save(buf, 'PNG')
    return buf.getvalue()

@app.route("/<game>/327-<int:pid>.png", defaults={'shiny': False})
@app.route("/<game>/shiny/327-<int:pid>.png", defaults={'shiny': True})
def spinda(game, pid, shiny=False):
    if game not in spinda_conf:
        abort(404)
    if not 0 <= pid < 2**32:
        abort(404)

    color = 'shiny' if shiny else 'normal'
    imgdata = make_spinda(spinda_conf[game], pid, color=color)
    return Response(imgdata, mimetype='image/png')


@app.route("/", defaults={'shiny': None})
@app.route("/<game>/", defaults={'shiny': False})
@app.route("/<game>/shiny/", defaults={'shiny': True})
def randomize(game=None, shiny=None):
    if game is None:
        game = random.choice(['ruby', 'diamond'])
    if shiny is None:
        shiny = random.randint(0,1)
    pid = random.randint(0, 2**32-1)
    return redirect(url_for('spinda', game=game, pid=pid, shiny=shiny))

if __name__ == '__main__':
    app.run(port=5015, debug=True)
