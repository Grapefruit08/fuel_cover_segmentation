from numpy import float32
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model

# list of Images to list of np.array for pretrained DeepLabV3
def Images_to_tensor(pil_images, img_size):
    tensor_list = []

    for pil_image in pil_images: 
        # need to be in RGB (3 channels) for DeepLab       
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        pil_image = pil_image.resize((img_size, img_size))
        numpy_image = np.array(pil_image, dtype=float32)
        
        tensor_list.append(numpy_image)

    return tensor_list

def build_in_preproces(img, Type):
    #img is np.array
    # Type is based on used NN model

    if Type == 0: #DeepLabV3
        reshaped_image = tf.keras.applications.resnet50.preprocess_input(img)
        reshaped_image = np.reshape(reshaped_image, \
                            (1, reshaped_image.shape[0], reshaped_image.shape[1], \
                             reshaped_image.shape[2]))
        
    return reshaped_image

# return predicted map for 2 lasses
def predict(model, image):
    preprocesed_image = image #build_in_preproces(image, Type = 0)

    y_predicted = model.predict(preprocesed_image)
    y_predicted = y_predicted > 0.5
    
    y_predicted = tf.squeeze(y_predicted)
    preprocesed_image = tf.squeeze(preprocesed_image)

    return y_predicted, preprocesed_image

# trying to make preproces form scratch for newes NN on my own dataset
def preprocess(image, img_size):
    reshaped_image = tf.image.resize(image, (img_size, img_size))
    reshaped_image = np.array(reshaped_image)
    reshaped_image = np.reshape(reshaped_image, (1, reshaped_image.shape[0], 
                                    reshaped_image.shape[1], 
                                    reshaped_image.shape[2]))
    
    return reshaped_image

def load_trained_model(Type):
    path = None
    if Type == 0: #UNet
        path = r"./models/unet_my_dataset.h5"
    if Type == 1:
        path = r"./models/unet_downloaded.h5"

    model = load_model(path)
    return model
