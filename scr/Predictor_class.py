import matplotlib.pyplot as plt
from PIL import Image

from predict import load_trained_model, predict, Images_to_tensor, preprocess

class Predictor:
    def __init__(self, images, img_size, Type):
        self.Type = Type
        self.img_size = img_size
        self.model = load_trained_model(self.Type)
        self.images = images
        self.masks = []
        self.preprocesed = []
        self.rescaled = []

    def predict(self):
        self.images = Images_to_tensor(self.images, self.img_size)

        for image in self.images:
            preprocesed = preprocess(image, self.img_size)
            mask, preprocesed = predict(self.model, preprocesed)

            self.masks.append(mask)
            self.preprocesed.append(preprocesed)

    def show_result(self, img_number):
        plt.subplot(1, 3, 1)
        plt.imshow(self.images[img_number]/255)
        plt.title('Transformed Image')
        plt.axis('off')

        plt.subplot(1, 3, 2)
        plt.imshow(self.preprocesed[img_number])
        plt.title('Normalized Image')
        plt.axis('off')

        plt.subplot(1, 3, 3)
        plt.imshow(self.masks[img_number])
        plt.title('Predicted Mask')
        plt.axis('off')

        plt.show()

    def mask_to_Image(self):
        for i in range(len(self.masks)):
            mask_np = self.masks[i].numpy()
            # Convert numpy array to PIL image
            self.masks[i] = Image.fromarray(mask_np)
