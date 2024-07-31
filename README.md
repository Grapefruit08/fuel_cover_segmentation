# zirconium_fuel_cover_segmentation

## Instalation

Clone the repository

```shell
git clone https://github.com/yourusername/project-name.git
```

Install all needed packages

```bash
pip install -r requrements.txt
```

Download the trained model of UNet with the `download_model.py` from folder `scripts`. Model will be downloaded into the newly created folder `models`.

## Input and output

Examples of different .jpg images used as input data for the program are in folder `input_images`.

Output of the program is feature map overlayd over original image in folder `output/visualization` and the excel file in folder `output/stats`. In excel files there are minimum, maximum and average height of founded segment.

