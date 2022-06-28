import subprocess
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
import json
import zipfile

from reconstruction import runReconstruction

id_dict = {}
id_max = {}
id_name = {}


def run_calculations(id):
    print('calculations: ' + id)
    id_dict[id] = -1
    # start of your code
    # files in folder = 'resources/' + id with original names, result must be located in this folder too
    zip_file = 'resources/' + id + '/images/' + id_name[id]
    with zipfile.ZipFile(zip_file) as z:
        z.extractall('resources/' + id + '/images/')
    os.remove(zip_file)
    # model reconstruction
    data_dir = os.path.abspath('resources/' + id)
    runReconstruction(data_dir)
    os.chdir('../../..')

    # copy example
    # with open('resources/' + id + '/res.ply', 'wb') as res:
    #     with open('resources/pmvs_options.txt.ply', 'rb') as image:
    #         res.write(image.read())
    # end of your code
    id_dict[id] = -2
    print('end of calculations: ' + id)


class MyHandler(SimpleHTTPRequestHandler):

    def do_POST(self):
        res_path = os.path.abspath('resources')
        length = self.headers['content-length']
        type = self.headers['content-type']
        if type == 'application/zip':
            id = os.path.dirname(self.path)[1:].replace('/images', '')

            if id in id_dict:
                if id_dict[id] >= 0:
                    data = self.rfile.read(int(length))
                    with open(res_path + self.path, 'wb') as f:
                        f.write(data)
                    id_dict[id] += 1
                if id_dict[id] == id_max[id]:
                    run_calculations(id)
        if type == 'application/json; charset=utf-8':
            data = self.rfile.read(int(length))
            if not os.path.exists(res_path + self.path):
                with open(res_path + self.path, 'wb') as f:
                    f.write(data)
                with open(res_path + self.path) as f:
                    data = json.load(f)
                    id = data['id']
                    num = data['count']
                    name = data['name']
                    if not os.path.exists(id):
                        os.mkdir(res_path + '/' + id)
                        os.mkdir(res_path + '/' + id + '/images')
                    if id not in id_dict:
                        id_dict[id] = 0
                        id_max[id] = int(num)
                        id_name[id] = name
                os.remove(res_path + self.path)
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        f = self.send_head()
        id = os.path.dirname(self.path).replace('/resources/', '').replace('/reconstruction_sequential/PMVS/models', '')

        if id in id_dict and id_dict[id] == -2:
            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()
                    id_dict.pop(id)
                    subprocess.call('rm -rf ./resources/' + id, shell=True)
            self.send_response(200)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()


if __name__ == '__main__':
    port = 8888
    server = ThreadingHTTPServer(('127.0.0.1', port), MyHandler)
    server.serve_forever()
