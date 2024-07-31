from PIL import Image
from snimek_trubky_functions import *
import os

#from symbol import parameters
class Snimek_trubky:
    def __init__(self, image=None, file_path=None, file_name=None):
        if file_path:
            self.load_image(file_path)
            self.from_file_path(file_path)
        else:
            self.image = image
            self.from_file_name(file_name)

        self.mask = None

        if self.image:
            self.y_min_kov = [None] * self.image.width
            self.y_min_trubka = [None] * self.image.width
            self.y_max_kov = [None] * self.image.width
            self.y_max_trubka = [None] * self.image.width
        else:
            self.y_min_kov = []
            self.y_min_trubka = []
            self.y_max_kov = []
            self.y_max_trubka = []

    def get_filename(self):
        filename = self.image_info[0] + "_" + \
                self.image_info[1] + "_" + self.image_info[2]
        filename += ".jpg"
        return filename

    # extract info from file_path
    def from_file_path(self, file_path):
        file_name = os.path.basename(file_path)
        self.from_file_name(file_name)

    #extract info from file name about image: name, rotation, zoom
    def from_file_name(self, file_name):
        self.image_info = file_name.split('_')
        self.image_info[2] = self.image_info[2].split('.')[0] # get rid of .jpg

    def load_image(self, image_path):
        try:
            self.image = Image.open(image_path)

        except FileNotFoundError:
            self.image = None
            print(f"File '{image_path}' not found.")
        except Exception as e:
            self.image = None
            print(f"An error occurred while loading the image: {e}")
    
    def kov(self):
        thresholded_kov = my_smart_thrashold(self.image)
        y_min_kov, y_max_kov = find_y_coords(thresholded_kov)

        self.y_min_kov, parameters_min = \
            fit_circle_equation(y_min_kov, self.image.width)
        self.y_max_kov, parameters_max = \
            fit_circle_equation(y_max_kov, self.image.width)
        
        # if coords are touching the edge => the aproximation is bad so 
        # it has to be rounded => visible in stats 
        if (self.image.height - 1) in self.y_max_kov:
            self.y_max_kov = [self.image.height - 1] * len(self.y_max_kov)
        if 0 in self.y_min_kov:
            self.y_min_kov = [0] * len(self.y_min_kov)

        thresholded_trubka = find_trubka(self.image)
        y_min_trubka, y_max_trubka = find_y_coords(thresholded_trubka)

        self.y_min_trubka = fit_posunem(y_min_trubka, parameters_min, \
                                         self.y_min_kov, True)
        
        self.y_max_trubka = fit_posunem(y_max_trubka, parameters_max, \
                                        self.y_max_kov, False)
        
        # if coords are touching the edge => the aproximation is bad so 
        # it has to be rounded => visible in stats 
        if (self.image.height - 1) in self.y_max_trubka:
            self.y_max_trubka = [self.image.height - 1] * len(self.y_max_trubka)
        if 0 in self.y_min_trubka:
            self.y_min_trubka = [0] * len(self.y_min_trubka)

    def make_colored(self, kov=True, trubka=True):
        if None in self.y_max_kov or None in self.y_min_kov:
            self.kov()

        color_kov = (0, 255, 0, 128)
        color_trubka = (255, 0, 0, 128)
        
        colored_image = self.image
        if kov == True:
            colored_image = merge_with_color(colored_image, self.y_min_kov, self.y_max_kov, color_kov)
        if trubka == True:
            colored_image = merge_with_color(colored_image, self.y_min_trubka, self.y_min_kov, color_trubka)
            colored_image = merge_with_color(colored_image, self.y_max_kov, self.y_max_trubka, color_trubka)
        
        return colored_image

    def print_colored(self, kov=True, trubka=True):
        colored_image = self.make_colored(kov, trubka)
        colored_image.show()

    def save_colored(self, output_folder, kov=True, trubka=True):
        colored_image = self.make_colored(kov=kov, trubka=trubka)

        filename = "_".join(self.image_info)
        filename += '.jpg'

        output_path = os.path.join(output_folder, filename)

        if colored_image.mode == 'RGBA':
            colored_image = colored_image.convert('RGB')

        colored_image.save(output_path)
        