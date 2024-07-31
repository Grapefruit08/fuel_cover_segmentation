import os

from Snimek_trubky_class import Snimek_trubky
from Transformator_class import Transformator
from Predictor_class import Predictor
from Mask_class import Mask
from Statistik import Statistik

if __name__ == "__main__":
    
    DIR = r"./input_images"
    all_filenames = os.listdir(DIR)
    filenames = sorted([file for file in all_filenames if file.lower().endswith('.jpg')])

    Snimky = []
    for filename in filenames:
        snimek = Snimek_trubky(None, os.path.join(DIR, filename))
        Snimky.append(snimek)

    for SNIMEK_NUM in range(len(Snimky)):
        Snimek = Snimky[SNIMEK_NUM]
        Snimek.kov()
        
        transform = Transformator(Snimek.image, Snimek.y_min_kov, Snimek.y_max_kov, 224)
        transform.rectangle_transform()

        transform.trim_image()
        transform.divide_image()

        if SNIMEK_NUM == 0:
            predictor = Predictor(transform.orig_squares, 
                                   transform.NN_image_size, Type=0)
        else:
            predictor.images = transform.orig_squares
            predictor.masks = []
        
        predictor.predict()
        predictor.mask_to_Image()

        transform.compose_image(predictor.masks)        

        OUT_visual = r"./output/vis"
        OUT_mask = OUT_visual

        mask = Mask(Snimek.image, Snimek.get_filename())
        mask.NN_squere_mask = transform.mask

        mask.set_kov_coord(Snimek.y_min_kov, Snimek.y_max_kov)
        mask.set_oxid_coords(Snimek.y_min_trubka, Snimek.y_max_trubka)

        mask.create_final_mask_kov()
        mask.create_final_mask_oxid()

        mask.put_on_mask(0.3, save=True, output_file = OUT_visual)

        OUT_stats = r"./output/stats"

        statistik = Statistik(Snimek.get_filename()[:-4])
        statistik.alfa_prava_coords = mask.alfa_prava
        statistik.kov_coords = mask.kov_coords
        statistik.oxid_coords = mask.oxid_coords
        statistik.inner = mask.inner
        statistik.conture_coords = mask.conture
        statistik.output = OUT_stats
        statistik.image_shape = Snimek.image.size

        statistik.count_stats()
        statistik.export_to_xlx()
