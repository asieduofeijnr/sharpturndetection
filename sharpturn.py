import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime
from io import StringIO
from math import radians, cos, sin, asin, sqrt
import math
import warnings


def data_frame(stream):
    """
    Load GPS data from a CSV file and return it as a pandas DataFrame.

    Parameters:
    filename (str): The path to the CSV file containing the GPS data.

    Returns:
    pandas.DataFrame: A DataFrame containing the GPS data with renamed columns.
    """
    stream_data = StringIO(stream)
    # Define the column headers
    headers = [
        'timestamp', 'latitude', 'longitude', 'direction',
        'vehicle_motion_status', 'speed_mph', 'acceleration_from_gps_speed'
    ]
    gps_df = pd.read_csv(stream_data, delimiter=',', append=True)

    # Add the columns of the DataFrame
    gps_df.columns = headers

    return gps_df


def date_time(date_time_str):

    t = str(date_time_str)
    parts = t.split('.')
    clean = parts[0].split(' ')
    date_parts = clean[0].split('-')
    time_parts = clean[1].split(':')
    date_parts = map(int, date_parts)
    time_parts = map(int, time_parts)

    year, month, day = date_parts
    hour, minute, second = time_parts
    date_time_obj = datetime(year, month, day, hour, minute, second)

    total_seconds = (date_time_obj - datetime(1970, 1, 1)).total_seconds()
    return total_seconds


def angular_distance(angle1, angle2):
    # Ensure both angles are between 0 and 360 degrees
    angle1 = angle1 % 360.0
    angle2 = angle2 % 360.0
    # Calculate the absolute angular distance
    distance = abs(angle1 - angle2)
    # Take the minimum of the direct distance and the wrapped-around distance
    distance = min(distance, 360.0 - distance)
    if angle1 > angle2:

        return distance * (np.pi/180)
    else:
        return -distance * (np.pi/180)


def aggregate_heading_time(dataframe):
    # Function to calculate difference in heading over change in time
    def calculate_diff(group):
        heading_diff = angular_distance(
            group['direction'].iloc[-1], group['direction'].iloc[0])
        time_diff = group['timestamp'].iloc[-1] - group['timestamp'].iloc[0]
        return pd.Series({'heading_diff': heading_diff, 'time_diff': time_diff})
    # Group the dataframe by each set of 10 rows and apply the calculation
    aggregated_data = dataframe.groupby(
        dataframe.index // 5).apply(calculate_diff)
    return aggregated_data


def height_of_center_of_gravity(mass_truckhead,
                                mass_reeftrailor,
                                height_of_center_of_gravity_truckhead,
                                height_of_center_of_gravity_trailer):
    h_cm = (mass_truckhead * height_of_center_of_gravity_truckhead
            + mass_reeftrailor * height_of_center_of_gravity_trailer)\
        / (mass_truckhead + mass_reeftrailor)
    return h_cm


def critical_speed(radius, height_of_center_of_gravity_trailer, track_width):
    """takes in r in meters, h in meters and t in meters gives back a critical speed value in miles per hour"""
    g = 9.81
    crit_speed = np.sqrt(
        (g*track_width)/(2*height_of_center_of_gravity_trailer)*radius)
    critical_speed_mph = crit_speed * 2.23694
    return critical_speed_mph


def curve(speed, avg):
    radius = []
    for i in range(len(speed)):
        if avg[i] == 0:
            radius.append(0)
        else:
            radius.append((speed[i]*.44707)/avg[i])
    return radius


if __name__ == '__main__':
    # Load the data from the CSV file into a dataframe (df)
    stream = 'input.csv'  # takes a batch of stream data after 10s

    # Define the parameters (Assumption of a semi-truck - Has to be defined for every partially loaded truck type)
    mass_truckhead = 9071.85
    mass_reeftrailor = 22679.619
    semi_trackwidth = 2.47
    height_of_center_of_gravity_truckhead = 0.8
    height_of_center_of_gravity_trailer = 1.35
    gravity = 9.81
    truck_length = 25

    h_cm = height_of_center_of_gravity(mass_truckhead,
                                       mass_reeftrailor,
                                       height_of_center_of_gravity_truckhead,
                                       height_of_center_of_gravity_trailer)

    df = data_frame(stream)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Aggregate the data into 10 second intervals at constant angular velocity
    aggregated_df = pd.DataFrame(aggregate_heading_time(df))
    w_avg = (aggregated_df['heading_diff']/10)

    repeated_w_avg = np.repeat(w_avg, 10)
    df_repeated = pd.DataFrame(repeated_w_avg)
    df_repeated = df_repeated.fillna(0)
    df_repeated = df_repeated.reset_index()
    df_repeated = df_repeated[:-1]

    df['w_avg'] = df_repeated['heading_diff']
