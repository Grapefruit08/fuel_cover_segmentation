# zirconium_fuel_cover_segmentation

## Installation

Clone the repository

```shell
git clone https://github.com/Grapefruit08/fuel_cover_segmentation.git
```

Install all needed packages

```bash
pip install -r requirements.txt
```

Download the trained model of UNet with `download_model.py` from the script folder `scripts`. Model will be downloaded into the newly created folder `models`.

## Input and output

Examples of different .jpg images used as input data for the program are in folder `input_images`.

Output of the program is feature map overlaid over original image in folder `output/visualization` and the Excel file in folder `output/stats`. In excel files, there are minimum, maximum and average height of the found segment.

