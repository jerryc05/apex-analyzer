# coding = UTF-8
from pathlib import Path
import pandas as pd


def main() -> None:
    for filename in ['./Temp/event_chart', './Temp/readdata_original', './Temp/firing_list']:
        input_file_path = Path(filename + '.feather')
        if input_file_path.is_file():
            output_file_path = Path(filename + '.xlsx')
            dtf = pd.read_feather(input_file_path)
            dtf.to_excel(output_file_path, index=False)
            print('{}.xlsx generated successfully!'.format(filename))
        else:
            print('{}.feather not found!'.format(filename))


if __name__ == '__main__':
    main()
