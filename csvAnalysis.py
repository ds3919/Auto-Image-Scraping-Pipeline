import pandas as pd
import os
import sys

def process_csv(input_csv_path, output_dir, resolution_step=10000):
    df = pd.read_csv(input_csv_path)
    df['category'] = df["filename"].str.split('_').str[0]
    df = df[(df["width"] != 0) & (df["height"] != 0)]
    df["resolution"] = df["width"] * df["height"]
    df["diff"] = df.apply(lambda row: min(row["height"] / row["width"], row["width"] / row["height"]), axis=1)

    def get_mer_range(diff):
        if diff < 0.2: return "0.0-0.2"
        elif diff < 0.4: return "0.2-0.4"
        elif diff < 0.6: return "0.4-0.6"
        elif diff < 0.8: return "0.6-0.8"
        else: return "0.8-1.0"

    df["diffRange"] = df["diff"].apply(get_mer_range)

    max_resolution = df["resolution"].max()
    resolution_bins = list(range(0, int(max_resolution + resolution_step), resolution_step))
    resolution_bins.append(max_resolution + resolution_step)
    resolution_labels = [f"{resolution_bins[i]}-{resolution_bins[i+1]-1}" for i in range(len(resolution_bins)-2)] + [f"{resolution_bins[-2]}+"]
    df["resolution_bin"] = pd.cut(df["resolution"], bins=resolution_bins, labels=resolution_labels, include_lowest=True)

    os.makedirs(output_dir, exist_ok=True)
    output_xlsx = os.path.join(output_dir, "ResolutionAnalysisOutput.xlsx")

    with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='synthImageInfo', index=False)

        workbook = writer.book
        worksheet = writer.sheets['synthImageInfo']

        # Add Excel table to range
        worksheet.add_table(
            0, 0,
            len(df), len(df.columns) - 1,
            {
                'name': 'synthImageInfo',
                'columns': [{'header': col} for col in df.columns]
            }
        )


input_csv = sys.argv[1]
output_dir = sys.argv[2]
res_step = int(sys.argv[3])
process_csv(input_csv, output_dir, res_step)