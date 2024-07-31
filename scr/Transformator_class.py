from PIL import Image
import numpy as np

# resize surface defined by y_min_coords and y_max_coords to rectangle
# recsale this rectangle based on values of pixels in it
class Transformator:
    def __init__(self, image, y_min_coords, y_max_coords, NN_image_size):
        self.y_min_coords = y_min_coords
        self.y_max_coords = y_max_coords
        self.orig_image = image
        self.NN_image_size = NN_image_size

        # make new empty image, of the same width and height
        # based on max diff of y_coords
        self.new_width = count_new_dimension(image.width, NN_image_size)
        self.new_height = count_new_dimension(image.height, NN_image_size)
        
        #self.width = image.width
        #self.height = max(abs(y_min - y_max) \
        #                    for y_min, y_max in zip(y_min_coords, y_max_coords))
        
        self.new_image = None #Image.new("RGB", (self.width, self.height))

        # list of squeres (NN_image_size x NN_image_size) made from new_image 
        self.orig_squares = []
        self.mask = None #squere mask for kov, BW
        self.final_mask = None #orig image but just mask, rounded, RGBA

    # resize surface defined by y_min_coords and y_max_coords to rectangle
    def rectangle_transform(self):
        width = self.orig_image.width
        height = max(abs(y_min - y_max) \
                            for y_min, y_max in \
                                zip(self.y_min_coords, self.y_max_coords))
        
        self.new_image = Image.new("RGB", (width, height))

        for x in range(width):
            min_y = self.y_min_coords[x]
            max_y = self.y_max_coords[x]

            for y in range(height):
                # find source y
                y_src = y / height * (max_y - min_y) + min_y

                # find integer values of y_coords of source pixels
                down = np.floor(y_src)
                up = np.ceil(y_src)

                # fraction to which of source pixels is closer computed value y_src
                frac = y_src - down

                ci = self.orig_image.getpixel((x, int(down)))
                ci1 = self.orig_image.getpixel((x, int(up)))

                # get value of new pixel based on fraction of source pixels
                new_pixel_value = tuple((1 - frac) * ci[channel] + frac * ci1[channel] \
                                        for channel in range(3))

                truncated_pixel_value = tuple(int(channel) for channel in new_pixel_value)

                self.new_image.putpixel((x, y), truncated_pixel_value)

        self.new_image = self.new_image.resize((self.new_width, self.new_height))

    # divide image into squeres so one pixel is exactly on 3 squeres
    def divide_image_more(self):
        # Calculate the number of rows and columns of squares
        num_rows = (self.new_height + self.NN_image_size - 1) // self.NN_image_size
        num_cols = (self.new_width + self.NN_image_size - 1) // self.NN_image_size

        squares = []

        # Iterate through rows and columns
        for y in range(num_rows):
            for x in range(num_cols):
                # Define coordinates for cropping
                x_start = max(0, x * self.NN_image_size)
                y_start = y * self.NN_image_size
                x_end = min((x + 3) * self.NN_image_size, self.new_width)
                y_end = min((y + 3) * self.NN_image_size, self.new_height)

                # Crop each square from the resized image
                square = self.new_image.crop((x_start, y_start, x_end, y_end))
                squares.append(square)

        self.orig_squares = squares

    # recsale this rectangle based on values of pixels in it
    def trim_image(self):
        # Convert the image to grayscale
        image_gray = self.new_image.convert('L')

        image_array = np.array(image_gray, dtype=np.float64)
        
        # find the bottom and top xth percentiles
        bottom_percentile = np.percentile(image_array, 5)
        top_percentile = np.percentile(image_array, 95)
        
        # trashold pixels
        image_array[image_array < bottom_percentile] = bottom_percentile # puvodne 0
        image_array[image_array > top_percentile] = top_percentile # puvodne 255

        # scale not trasholded values to [0, 1]
        scale_factor = 255 / (top_percentile - bottom_percentile)
        image_array = (image_array - bottom_percentile) * scale_factor
        
        # convert numpy array back to image
        self.new_image = Image.fromarray(image_array.astype(np.uint8))

    # divide image to squeres one pixel in exactly one image
    def divide_image(self): 
        # Calculate the number of rows and columns of squares
        num_rows = self.new_height // self.NN_image_size
        num_cols = self.new_width // self.NN_image_size

        squares = []

        # Iterate through rows and columns
        for y in range(num_rows):
            for x in range(num_cols):
                # Crop each square from the resized image
                square = self.new_image.crop((x * self.NN_image_size, \
                                            y * self.NN_image_size, \
                                            (x + 1) * self.NN_image_size, \
                                            (y + 1) * self.NN_image_size))
                squares.append(square)

        self.orig_squares = squares

    def divide_image_rect(self): 
        # Calculate the number of rectangles horizontally
        num_rectangles = self.new_width // self.NN_image_size

        rectangles = []

        # Iterate through each rectangle
        for x in range(num_rectangles):
            # Crop each rectangle from the resized image
            rectangle = self.new_image.crop((x * self.NN_image_size, 0,
                                            (x + 1) * self.NN_image_size, 
                                            self.new_height))
            rectangles.append(rectangle)

        self.orig_rectangles = rectangles

    def compose_image_rect(self, masks):
        composed_width = sum(mask.width for mask in masks)

        # Create a new blank image with the same height as the original image
        composed_image = Image.new('RGB', (composed_width, self.new_height))

        # Paste each rectangle onto the composed image
        current_width = 0
        for mask in masks:
            composed_image.paste(mask, (current_width, 0))
            current_width += mask.width

        self.mask = composed_image

    # compose image if there is exactly one image for one pixel
    def compose_image(self, masks):
        num_cols = self.new_width // self.NN_image_size
        
        # Calculate the number of rows based on the number of squares and columns
        num_rows = len(masks) // num_cols
        
        # Calculate the dimensions of the composed image
        width = num_cols * self.NN_image_size
        height = num_rows * self.NN_image_size
        
        # Create a new blank image with the calculated dimensions
        composed_image = Image.new("RGB", (width, height))

        # Paste each square into the composed image
        for i, square in enumerate(masks):
            x = (i % num_cols) * self.NN_image_size
            y = (i // num_cols) * self.NN_image_size
            composed_image.paste(square, (x, y))

        self.mask = composed_image

    def reverse_transform(self):
        self.mask = self.mask.resize(self.orig_image.size)
        width = self.mask.width
        height = self.mask.height
        
        for x in range(width):
            min_y = self.y_min_coords[x]
            max_y = self.y_max_coords[x]

            for y in range(min_y, max_y):
                y_src = (y - min_y) * height / (max_y - min_y)

                down = np.floor(y_src)
                up = np.ceil(y_src)

                # fraction to which of source pixels is closer computed value y_src
                frac = y_src - down

                ci = self.mask.getpixel((x, int(down)))
                ci1 = self.mask.getpixel((x, int(up)))

                # get value of new pixel based on fraction of source pixels
                new_pixel_value = tuple((1 - frac) * ci[channel] + frac * ci1[channel] \
                                        for channel in range(3))

                truncated_pixel_value = tuple(int(channel) for channel in new_pixel_value)

                self.orig_image.putpixel((x, y), truncated_pixel_value)

    def create_final_mask(self):
        self.mask = self.mask.resize(self.orig_image.size)
        width = self.mask.width
        height = self.mask.height

        self.final_mask = Image.new('RGB', (width, height), (0,0,0))

        col_back = (255, 255, 100) # color background = yellow
        col_for = (255, 153, 255) # color foreground = purple
        
        for x in range(width):
            min_y = self.y_min_coords[x]
            max_y = self.y_max_coords[x]

            for y in range(min_y, max_y):
                y_src = (y - min_y) * height / (max_y - min_y)

                down = np.floor(y_src)
                up = np.ceil(y_src)

                # fraction to which of source pixels is closer computed value y_src
                frac = y_src - down

                ci = self.mask.getpixel((x, int(down)))
                ci1 = self.mask.getpixel((x, int(up)))

                # get value of new pixel based on fraction of source pixels
                new_pixel_value = tuple((1 - frac) * ci[channel] + frac * ci1[channel] \
                                        for channel in range(3))
                
                if new_pixel_value[0] == 255:
                    new_new_pixel_value = col_back
                else:
                    new_new_pixel_value = col_for

                #truncated_pixel_value = tuple(int(channel) for channel in new_pixel_value)

                self.final_mask.putpixel((x, y), new_new_pixel_value)#truncated_pixel_value)

def count_new_dimension(old_dimension, factor):
    division = np.round(old_dimension / factor)
    if division == 0:
        division = 1

    new_dimension = int(division * factor)
    
    return new_dimension
        