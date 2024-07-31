from PIL import Image, ImageDraw
import numpy as np
import os

from alfa_functions import *

class Mask:
    def __init__(self, orig_image, filename):
        self.orig_image = orig_image
        self.NN_squere_mask = None
        self.kov_coords = None
        self.oxid_coords = None
        self.alfa_prava = None
        self.filename = os.path.splitext(filename)[0]
        self.inner = self.inner_from_filename()
        self.conture = []

        self.final_mask = Image.new('RGB', self.orig_image.size, (0,0,0))

    def inner_from_filename(self):
        inner = 2*[] #first val. is upper part, second val. is lower part of image
        image_info = self.filename.split('_')
        if image_info[1][0] == 'A':
            inner = [False, True]
        else:
            inner = [True, False]
        return inner

    def set_kov_coord(self, y_min, y_max):
        self.kov_coords = [y_min, y_max]

    def set_oxid_coords(self, y_min, y_max):
        self.oxid_coords = [y_min, y_max]

    def set_alfa_prava(self, y_min, y_max):
        self.alfa_prava = [y_min, y_max]

    # bend alfa_prava list to the original coordinates of kov
    def bend_alfa_prava(self):
        width = self.NN_squere_mask.width
        height = self.NN_squere_mask.height

        for x in range(width):
            min_y = self.kov_coords[0][x]
            max_y = self.kov_coords[1][x]

            if self.alfa_prava[0][x] != None:
                down = (self.alfa_prava[0][x]) / height * (max_y - min_y) + min_y
                self.alfa_prava[0][x] = int(down)
            if self.alfa_prava[1][x] != None:
                up = (self.alfa_prava[1][x]) / height * (max_y - min_y) + min_y
                self.alfa_prava[1][x] = int(up)

    def zobraz_hranici(self, image, y_min, y_max , color = (0, 255, 0, 128)):
        draw = ImageDraw.Draw(image, 'RGBA')

        # Draw border lines
        points = [(x, y_min[x]) for x in range(len(y_min))]
        draw.line(points, fill=color, width=6)

        points = [(x, y_max[x]) for x in range(len(y_max))]
        draw.line(points, fill=color, width=6)

        return image

    def create_final_mask_kov(self):
        self.NN_squere_mask = self.NN_squere_mask.resize(self.orig_image.size)
        width = self.NN_squere_mask.width
        height = self.NN_squere_mask.height

        col_back = (255, 255, 140) # color background = yellow
        col_alfa_prava = (255, 255, 0) # more yellow yellow
        col_for = (255, 153, 255) # color foreground = purple

        # find alfa_prava coordinates
        low, up = self.highest_and_lowest_y_coordinates()
        # tady jsi prehazoval up a low poyor jestli to je nakonecspravne
        self.set_alfa_prava([up]*self.orig_image.width, [low]*self.orig_image.width)
        
        # sel all topixel from edge of image to alfa_prava to 255
        self.NN_squere_mask = simplify_to_alfa_prava(self.NN_squere_mask, low, up)

        # set alfa_prava coordinates to original coordinates of whole original image
        self.bend_alfa_prava()

        result, conture = simplify_alfa(self.NN_squere_mask, up, low)
        self.NN_squere_mask = result

        for one_conture in conture:
            if one_conture is None:
                self.conture.append(None)
                continue
            self.conture.append(transform_conture(one_conture, self.kov_coords[0], \
                            self.kov_coords[1], self.NN_squere_mask.height))

        if up is None:
            self.alfa_prava[0] = [0]*width
        if low is None:
            self.alfa_prava[1] = [height-1]*width

        for x in range(width):
            min_y = self.kov_coords[0][x]
            max_y = self.kov_coords[1][x]

            for y in range(min_y, max_y):
                y_src = (y - min_y) * height / (max_y - min_y)

                down = np.floor(y_src)
                up = np.ceil(y_src)

                # fraction to which of source pixels is closer computed value y_src
                frac = y_src - down

                ci = self.NN_squere_mask.getpixel((x, int(down)))
                ci1 = self.NN_squere_mask.getpixel((x, int(up)))

                # get value of new pixel based on fraction of source pixels
                new_pixel_value = tuple((1 - frac) * ci[channel] + frac * ci1[channel] \
                                        for channel in range(3))
                
                if y < self.alfa_prava[0][x] or y > self.alfa_prava[1][x]:
                        new_new_pixel_value = col_alfa_prava 
                else:
                    if new_pixel_value[0] == 255:
                        new_new_pixel_value = col_back
                    else:
                        new_new_pixel_value = col_for

                self.final_mask.putpixel((x, y), new_new_pixel_value)

    # find alfa prava in rectangle mask
    def highest_and_lowest_y_coordinates(self):
        binary_image = np.array(self.NN_squere_mask)
        
        # Get the height of the image
        width, height = self.NN_squere_mask.size
        
        highest_y = None
        lowest_y = None

        # od pulky smerem dolu     
        for y in range(height // 2, height-1):
            if np.all(binary_image[y, :] == 255):
                highest_y = y
                break
        
        # od pulky smerem nahoru
        for y in range(height // 2, 0, -1):
            if np.all(binary_image[y, :] == 255):
                lowest_y = y
                break
        
        return highest_y, lowest_y

    def create_final_mask_oxid(self):
        #color = [inner color, outer color]
        color = [(255, 0 ,0), (255, 100, 0)]
        if self.inner[0] == True:
            color.reverse()

        self.draw_oxid(self.oxid_coords[0], self.kov_coords[0], color[0])
        self.draw_oxid(self.kov_coords[1], self.oxid_coords[1], color[1])

    def draw_oxid(self, y_min, y_max, color):
        draw = ImageDraw.Draw(self.final_mask)
        for x in range(self.orig_image.width):
            y_min_local = int(y_min[x])
            y_max_local = int(y_max[x])
            for y in range(y_min_local, y_max_local):
                #self.final_mask.putpixel((x,y), color)
                draw.point((x, y), fill=color)
        del draw

    def put_on_mask(self, alpha, save=False, show=False, output_file=""):
        blended_image = Image.blend(self.orig_image, self.final_mask, alpha)
        if show == True:
            blended_image.show()
        if save == True and output_file:
            output = os.path.join(output_file, self.filename + ".jpg")
            blended_image.save(output)
