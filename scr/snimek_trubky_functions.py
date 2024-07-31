import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import curve_fit

def my_smart_thrashold(image):
    gray_image = image.convert('L')

    # Get the darkest and brightest pixel values
    darkest, brightest = gray_image.getextrema()

    # Calculate the threshold value
    threshold = (brightest + darkest) / 2

    # Apply thresholding to create a binary image
    thresholded_image = gray_image.point(lambda p: p > threshold and 255)

    return thresholded_image

# finds the y_coords from thrasholded image
# y_coords is lower and upper border of ones 
def find_y_coords(image):
    min_y_coordinates = [None] * image.width
    max_y_coordinates = [None] * image.width

    for x in range(image.width):
        min_y = image.height
        max_y = 0
        for y in range (image.height - 1, -1, -1):
            pixel_value = image.getpixel((x,y))
            if pixel_value > 0:
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        
        min_y_coordinates[x] = min_y
        max_y_coordinates[x] = max_y
    
    return min_y_coordinates, max_y_coordinates

# draw in color into image from min_y_coords to max_y_coords
def merge_with_color(image, min_y_coords, max_y_coords, color):
    new_image = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(new_image)
    for x in range(image.width):
        if isinstance(min_y_coords, int):  # check if it is a single value
            min_y = min_y_coords
            max_y = max_y_coords
        else:  # for fitted values
            min_y = int(min_y_coords[x])
            max_y = int(max_y_coords[x])

        for y in range(min_y, max_y + 1):
            draw.point((x, y), fill=color)  
    del draw

    return Image.alpha_composite(image.convert('RGBA'), new_image)

# dolni polovina kruhu
def plus_circle_equation(x, xc, yc, R):
    y = np.sqrt(R**2 - (x - xc)**2) + yc
    return y

#horni polovina kruhu
def minus_circle_equation(x, xc, yc, R):
    y = - np.sqrt(R**2 - (x - xc)**2) + yc
    return y

# fit y_coords with equation of circle
def fit_circle_equation(y_coords, image_width):
    x_data = np.arange(image_width)

    y_data = np.array(y_coords)

    # prvotni pomocny odhad parametru krivky kruhu
    # p0 = [xc, yc, R]
    p0 = [image_width / 2, np.mean(y_data), image_width]

    # fit pomoci rovnice "dolni poloviny" kruhu
    parameters_plus, _ = curve_fit(plus_circle_equation, x_data, y_data, p0=p0)
    
    # fit pomoci rovnice "horni poloviny kruhu"
    parameters_minus, _ = curve_fit(minus_circle_equation, x_data, y_data, p0=p0)

    # vypocet fitovanych y a absolutni chyby pro oba fity
    y_fit_positive = plus_circle_equation(x_data, *parameters_plus)
    ssd_positive = np.sum(np.abs(y_data - y_fit_positive))

    y_fit_negative = minus_circle_equation(x_data, *parameters_minus)
    ssd_negative = np.sum(np.abs(y_data - y_fit_negative))

    # vyber vhodne poloviny kruhu
    if ssd_positive < ssd_negative:
        # pridat do parametru o jakou z nerovnic se jedna
        parameters = [parameters_plus, 1]
        y_fit = y_fit_positive
    else:
        # pridat do parametru o jakou z nerovnic se jedna
        parameters = [parameters_minus, -1]
        y_fit = y_fit_negative

    # Return the fitted y-coordinate of the bottom of the circle
    y_fit_int = list(map(int, y_fit))
    return y_fit_int, parameters

def find_trubka(image):
    image_gray = image.convert('L')

    histogram = image_gray.histogram()

    histogram_array = np.array(histogram)

    image_array = np.array(image_gray, dtype=np.float64)
    
    bottom_percentile = np.percentile(image_array, 5)
    
    darkest, brightest = image_gray.getextrema()
    upper_limit = (brightest + darkest) / 2 # = thrashold for kov
    
    image_array[image_array < bottom_percentile] = 0

    # sub array of values of histogram that is important for finding kov thrashold
    sub_array = histogram_array[bottom_percentile.astype(int) : np.floor(upper_limit).astype(int)+1]

    # list of differences in subarray 
    differences = np.abs(np.diff(sub_array))
    mean = np.mean(differences)
    # take just indeces that have higher differences 
    indices_higher = np.where(differences > mean)[0]

    # the index with high difference has to also have higher number of pixels with that value
    # it should not be just one peak 
    sub_upper_percentile = np.percentile(sub_array, 50)
    for idx in reversed(range(len(indices_higher))):
        index = indices_higher[idx]
        if sub_array[index] >= sub_upper_percentile:
            upper_value = index
            break    

    # upper value was get from sub_array starting from bottom_percentile
    threshold = (bottom_percentile + (bottom_percentile + upper_value)) / 2

    # Apply thresholding to create a binary image
    thresholded_image = image_gray.point(lambda p: 255 if p > threshold else 0)

    return thresholded_image

def fit_posunem(y_coords, parameters, kov, upper_circle):
    [xc, yc, R], sign = parameters

    x_coords = np.arange(len(y_coords))

    max_posun = 2*max(np.abs(x - y) for x, y in zip(y_coords, kov))

    # Halving interval method
    if sign == -1:
        R_down = R - max_posun
        R_up = R + max_posun
    else:
        R_down = R + max_posun
        R_up = R - max_posun

    # toto plati pro horni pruh
    if upper_circle == True:         
        C = R_down
        R_down = R_up
        R_up = C
    
    while True:
        R_mid = (R_down + R_up) / 2
        parameters = [xc, yc, R_mid]

        if sign == 1:
            y_fit = plus_circle_equation(x_coords, *parameters)
        else: # sign == -1
            y_fit = minus_circle_equation(x_coords, *parameters)

        # verze pro horni pruh upper_circle == True
        if upper_circle == True:
            over_fit = sum(x < y for x, y in zip(y_fit, y_coords)) / len(y_coords)
        else:
            over_fit = sum(x > y for x, y in zip(y_fit, y_coords)) / len(y_coords)
        
        # if it is not moving
        if np.abs(R_up - R_down) < 1:
            break

        # halving method for R
        if (over_fit >= 0.80) and (over_fit <= 0.90):
            break
        if over_fit < 0.80:
            R_up = R_mid
        else:
            R_down = R_mid

    return list(map(int, y_fit))