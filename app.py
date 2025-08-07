from shutil import which

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def read_remote_readings(file_path, meter: str = "Unknown"):
    # 1. Read the CSV file with only the required columns
    df = pd.read_csv(
        file_path,
        usecols=['Date', 'Reading', 'Amount'],
        parse_dates=['Date'],
        dayfirst=True
    )

    # 2. Set 'Date' as index and upsample to 1-minute intervals
    df.set_index('Date', inplace=True)
    df = df.resample('1min').asfreq()
    df['Reading'] = df['Reading'].interpolate(method='time')
    df['Amount'] = df['Amount'].interpolate(method='time')
    df['Type'] = "Main" if meter == 'All Buildings' else 'Secondary'

    # 3. Add 'FlowRateM3PerMinute' as the diff of 'Reading'
    df['FlowRateM3PerMinute'] = df['Reading'].diff().fillna(0)


    # 4. Add 'Meter' column
    df['Meter'] = meter

    # 5. Reset index and set ['Date', 'Meter'] as index
    df.reset_index(inplace=True)
    df.set_index(['Date', 'Meter', 'Type'], inplace=True)

    return df


def plot_all_days_histogram(readings):
    # start_date = pd.Timestamp('2025-01-01')
    # end_date = pd.Timestamp('2025-06-30')
    file_keys = ['6', '8', '10', '12', 'All']

    # Concat all data into a single DataFrame
    all_data = pd.concat([readings[key] for key in file_keys], axis=0)

    summed_data = all_data.groupby(level=['Date', 'Type']).sum()

    main = summed_data.loc[(slice(None),'Main'), :].droplevel('Type')
    secondary = summed_data.loc[(slice(None), 'Secondary'), :].droplevel('Type')
    diff = main - secondary

    # Group diff by hour
    diff['Day'] = diff.index.get_level_values('Date').date
    daily_diff = diff.groupby('Day').sum()
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=daily_diff.index, y=daily_diff['FlowRateM3PerMinute'], marker='o')
    plt.title('Hourly Difference in Flow Rate (Main - Secondary)')
    plt.xlabel('Date')
    plt.ylabel('Flow Rate Difference (m³/min)')
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()


readings_dict = {
    '6': read_remote_readings(r'Data\WaterReadings_6.csv', meter='Building 6'),
    '8': read_remote_readings(r'Data\WaterReadings_8.csv', meter='Building 8'),
    '10': read_remote_readings(r'Data\WaterReadings_10.csv', meter='Building 10'),
    '12': read_remote_readings(r'Data\WaterReadings_12.csv', meter='Building 12'),
    'All': read_remote_readings(r'Data\WaterReadings_All.csv', meter='All Buildings')
}

plot_all_days_histogram(readings_dict)

plt.show()