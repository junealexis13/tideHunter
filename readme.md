# tideHunter

tideHunter is a Streamlit-based application designed to process and analyze NAMRIA tide data. It provides a user-friendly interface for both single and multiple file processing, allowing users to generate statistical inferences and visualizations.

## Features

- **Single Processor**: Process individual NAMRIA tide data files.
- **Multiple Processor**: Process and compare multiple NAMRIA tide data files spanning over 10 years.
- **Data Visualization**: Generate various plots and statistical summaries.
- **Date Filtering**: Filter data by specific date ranges.
- **Monthly and Yearly Averages**: Calculate and visualize monthly and yearly tide level averages.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/junealexissantos/tideHunter.git
    cd tideHunter
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

To run this locally, streamlit library is needed.

Run the Streamlit application:
```sh
streamlit run main.py
```

## Project Structure

- `main.py`: The main entry point of the application.
- `local_classes/variables.py`: Contains enumerations for accepted upload formats and key codes.
- `appcore.py`: Core logic for parsing and processing tide data.
- `page_design.py`: Contains the Streamlit widgets and layout for single and multiple file processing.

## Developed and Designed By

>> VISIT @ **June Alexis**(https://junealexis.vercel.app)

## Dedication
*tideHunter* is a passion project by June Alexis Santos for the Coastal Assessment Team of the Mines and Geosciences Bureau - Regional Office 3

### Coastal Assessment Team 2025
- Maam Weng
- Sir Carlo
- Dara
- June
- Georgette
