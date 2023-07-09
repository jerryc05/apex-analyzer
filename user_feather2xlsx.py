# coding = UTF-8
from pathlib import Path
import pandas as pd


def main() -> None:
    input_file_path = Path('./Temp/event_chart.feather')
    output_file_path = Path('./Temp/event_chart.xlsx')
    dtf = pd.read_feather(input_file_path)
    dtf.to_excel(output_file_path, index=False)
    input_file_path = Path('./Temp/readdata_original.feather')
    output_file_path = Path('./Temp/readdata_original.xlsx')
    dtf = pd.read_feather(input_file_path)
    dtf.to_excel(output_file_path, index=False)
    input_file_path = Path('./Temp/firing_list.feather')
    output_file_path = Path('./Temp/firing_list.xlsx')
    dtf = pd.read_feather(input_file_path)
    dtf.to_excel(output_file_path, index=False)


if __name__ == '__main__':
    main()
