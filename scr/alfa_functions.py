import numpy as np
import cv2
from PIL import Image

# find contures of ofla for both sides of image, based on low and up (alfa prava)
def find_alfa_border(mask, low, up):
    height, _  = mask.shape

    alfa_bottom_conture = None
    alfa_upper_conture = None

    half = height//2

    if low != 0 and low != None:
        bottom_half = mask[half:, :]
        bottom_seed = (0, bottom_half.shape[0] - 1)
        alfa_bottom_conture = find_conture(bottom_half, bottom_seed)

    if up!= 0 and up != None:
        upper_half = mask[:height-half, :]
        upper_seed = (0, 0)
        alfa_upper_conture = find_conture(upper_half, upper_seed)

    return alfa_bottom_conture, alfa_upper_conture

def find_conture(image, seed):
    mask = np.zeros((image.shape[0] + 2, image.shape[1] + 2), dtype=np.uint8)
    floodfill = cv2.floodFill(image, mask, seed, 255)[1]

    # Find contours in the floodfill image
    contours, _ = cv2.findContours(floodfill, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find the contour with the largest area
    largest_contour = max(contours, key=cv2.contourArea)

    largest_contour_mask = np.zeros_like(image)
    cv2.drawContours(largest_contour_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    result_image = np.zeros_like(image)
    result_image[largest_contour_mask == 255] = 255

    return largest_contour

# same as bend_alfa - transform y_coord from rectangle to original shape
def transform_conture(contour, down_border, up_border, new_height):
    transformed_contour = contour.copy() 
    for i, point in enumerate(contour):
        x, y = point[0]

        max_y = up_border[x]
        min_y = down_border[x]

        transformed_y = int((y / new_height) * (max_y - min_y) + min_y)
        
        transformed_contour[i][0][1] = transformed_y  # Update the y-coordinate of the contour point

    return transformed_contour

def simplify_alfa(image, up, low):
    mask = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    height, width = mask.shape
    conture = find_alfa_border(mask, low, up)

    half = height//2
    bottom_half = mask[half:, :]
    upper_half = mask[:height-half, :]

    bottom_half1 = draw_conture_mask(bottom_half, conture[0])
    upper_half1 = draw_conture_mask(upper_half, conture[1])

    combined_image = np.zeros((height, width, 3), dtype=np.uint8)
    combined_image[half:, :] = cv2.cvtColor(bottom_half1, cv2.COLOR_GRAY2BGR)
    combined_image[:half, :] = cv2.cvtColor(upper_half1, cv2.COLOR_GRAY2BGR)

    # adjust the bottom conture for the combined image
    if conture[0] is not None:
        conture[0][:, :, 1] += half

    rgb_image = cv2.cvtColor(combined_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    #pil_image.show()
    #pil_image.save('alfa_po_uprave.png')

    return pil_image, conture

def draw_conture_mask(image, conture):
    largest_contour_mask = np.zeros_like(image)
    if conture is None:
        return largest_contour_mask

    cv2.drawContours(largest_contour_mask, [conture], -1, 255, thickness=cv2.FILLED)
    result_image = np.zeros_like(image)
    result_image[largest_contour_mask == 255] = 255

    return result_image

def draw_conture(image, conture_list):
    mask = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    for conture in conture_list:
        if conture is not None:
            cv2.drawContours(mask, conture, -1, (0, 255, 0), thickness=3)

    rgb_image = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    pil_image.show()

def simplify_to_alfa_prava(mask, low, up):
    new_mask = np.array(mask)

    # Set all pixels from 'low' to the bottom to white if 'low' is specified
    if low is not None:
        new_mask[low:, :] = 255

    # Set all pixels from the top to 'up' to white if 'up' is specified
    if up is not None:
        new_mask[:up, :] = 255
    
    new_mask = Image.fromarray(new_mask)

    return new_mask
