#! /bin/env python
# -*- coding:utf-8 -*-

import re
import os
import sys

def webp_convert(dir_path):
    IMAGE_FILE_REGEX = '^.+\.(png|jpg|jpeg|tif|tiff|gif|bmp)$'
    for root,dirs,files in os.walk(dir_path):
        print('convert {} files...'.format(root))
        for file in files:
            filename = os.path.join(root,file)
            if re.match(IMAGE_FILE_REGEX,file,re.IGNORECASE):
                outfile = filename[:-5] + "a.webp"
                if file.endswith('.gif'):
                    os.system('gif2webp -lossy ' + filename + ' -o ' + outfile)
                    os.unlink(filename)
                else:
                    os.system('cwebp ' + filename + ' -o ' + outfile)
                    os.unlink(filename)

def main():
    dir_path = sys.argv[-1]
    webp_convert(dir_path)

if __name__ == '__main__':
    main()

