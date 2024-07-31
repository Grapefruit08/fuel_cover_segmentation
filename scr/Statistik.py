import pandas as pd
import os

class Statistik:
    def __init__(self, filename):
        self.kov_coords = None
        self.oxid_coords = None
        self.alfa_prava_coords = None
        self.filename = filename
        self.inner = [] # [upper, lower]
        self.conture_coords = []

        self.output = ""
        self.image_shape = ()

        self.statistiky = {}

        #measuring just in y-axis
        self.multiplier = self.get_multiplier_from_filename(filename)

    def pixels_to_mikrom(self, argument):
        """
        Pixely (w x h)	Měřítko (μm)
        1232 x 964	1620x1267
        1232 x 964	826x646
        1232 x 964	412x322
        1232 x 964	165x129
        """
        switcher = {
        5:  1269 / 964,
        10: 646 / 964,
        20: 322 / 964,
        50: 129 / 964 
        }
        
        return switcher.get(argument, None)

    def get_multiplier_from_filename(self, filename):
        last_part = filename.split('_')[-1]
        zoom = int(''.join(filter(str.isdigit, last_part)))

        mutliplier = self.pixels_to_mikrom(zoom)

        return mutliplier
    
    def give_statistik(self, list1, list2):
        differences = [abs(a - b) for a, b in zip(list1, list2)]
    
        # Compute the biggest, smallest, and average differences
        maximum = max(differences) * self.multiplier
        minimum = min(differences) * self.multiplier
        average = sum(differences) / len(differences) * self.multiplier

        return minimum, maximum, average
    
    def give_alfa_statistik(self, list, map):
        if map is None:
            return 0, 0, 0
        
        differences = []
        for point in map:
            x, y = point[0]
            # on the edges of conture it is always 0 => not relevant
            if x == 0 or x == self.image_shape[0]-1:
                continue
            differences.append(abs(y - list[x]))

        if not differences:
            return None, None, None
        
        maximum = max(differences) * self.multiplier
        minimum = min(differences) * self.multiplier
        average = sum(differences) / len(differences) * self.multiplier
    
        return minimum, maximum, average
    
    def count_stats(self):
        outer = 0
        inner = 1

        if self.inner[0] == True:
            outer, inner = inner, outer
        
        self.statistiky['metal'] = self.give_statistik(self.kov_coords[outer], self.kov_coords[inner])
        self.statistiky['wall'] = self.give_statistik(self.oxid_coords[outer], self.oxid_coords[inner])

        self.statistiky['oxid e'] = self.give_statistik(self.kov_coords[outer], self.oxid_coords[outer])
        self.statistiky['oxid i'] = self.give_statistik(self.kov_coords[inner], self.oxid_coords[inner])

        self.statistiky['alfa prava e'] = self.give_statistik(self.kov_coords[outer], self.alfa_prava_coords[outer])
        self.statistiky['alfa prava i'] = self.give_statistik(self.kov_coords[inner], self.alfa_prava_coords[inner])

        self.statistiky['alfa e'] = self.give_alfa_statistik(self.kov_coords[outer], self.conture_coords[inner])
        self.statistiky['alfa i'] = self.give_alfa_statistik(self.kov_coords[inner], self.conture_coords[outer])

    def export_to_xlx(self):
        df = pd.DataFrame.from_dict(self.statistiky, orient='index').transpose()

        # Create a DataFrame for labels
        labels_df = pd.DataFrame({
            '': ['min', 'max', 'average']
        })

        # Concatenate the labels DataFrame with the original DataFrame
        keys_df = pd.DataFrame([[''] + list(df.columns)], columns=[''] + list(df.columns))  # Add an empty string for the first column header
        values_df = pd.concat([labels_df, df], axis=1)  # Concatenate labels with the values DataFrame
        formatted_df = pd.concat([keys_df, values_df], ignore_index=True)  # Concatenate keys_df and values_df

        # Construct the full file path
        file_path = os.path.join(self.output, self.filename)
        file_path += ".xlsx"

        # Write the DataFrame to an Excel file
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            formatted_df.to_excel(writer, index=False, header=False, float_format="%.2f")
