import math
import numpy as np
import pandas as pd
from io import StringIO

# Global DataFrame to store GPS data
gps_data_accumulated = None

# Global variables
mass_truckhead = 9071.85
mass_reeftrailor = 22679.619
semi_trackwidth = 2.47
height_of_center_of_gravity_truckhead = 0.8
height_of_center_of_gravity_trailer = 1.35
gravity = 9.81
truck_length = 25


# Function definitions

def data_frame(stream):
    """
    Append GPS data from a string containing CSV data to a global DataFrame and return it.

    Parameters:
    stream (str): A string containing the CSV data of the GPS data.

    Returns:
    pandas.DataFrame: A DataFrame containing the accumulated GPS data.
    """
    global gps_data_accumulated, current_index

    stream_data = StringIO(stream)
    new_data = pd.read_csv(stream_data, delimiter=',', header=None)
    headers = ['timestamp', 'direction', 'speed_mph']
    new_data.columns = headers

    # Add an index column to the new data
    new_data['index'] = range(current_index, current_index + len(new_data))
    current_index += len(new_data)  # Update the global index counter

    if gps_data_accumulated is None:
        gps_data_accumulated = new_data
    else:
        # Keep only the last row of the existing data and append the new data
        gps_data_accumulated = pd.concat(
            [gps_data_accumulated.iloc[-1:], new_data], ignore_index=True)

    # Reset the index to align with the 'index' column
    gps_data_accumulated.reset_index(drop=True, inplace=True)

    return gps_data_accumulated


def angular_distance(angle1, angle2):
    """
    Calculate the angular distance between two angles.

    Parameters:
    angle1 (float): The first angle in degrees.
    angle2 (float): The second angle in degrees.

    Returns:
    float: The angular distance between the two angles in radians.
    """
    angle1 = angle1 % 360.0
    angle2 = angle2 % 360.0

    distance = abs(angle1 - angle2)
    distance = min(distance, 360.0 - distance)
    if angle1 > angle2:
        return distance * (np.pi/180)
    else:
        return -distance * (np.pi/180)


def find_adjacent(angle_radians, truck_length):
    """
    Calculate the radius of the circle formed by the given angle and truck length.

    Parameters:
    angle_radians (float): The angle in radians.
    truck_length (float): The length of the truck in meters.

    Returns:
    float: The radius of the circle in meters. Returns positive infinity for edge cases.
    """

    # Validate input parameters
    if not isinstance(angle_radians, (int, float)):
        raise ValueError("The angle must be a number (int or float).")

    if not isinstance(truck_length, (int, float)) or truck_length <= 0:
        raise ValueError(
            "Truck length must be a positive number (int or float).")

    # Handle edge cases for angle being 0 or π radians
    if math.isclose(angle_radians, 0, abs_tol=1e-9) or math.isclose(angle_radians, math.pi, abs_tol=1e-9):
        return float('inf')

    # Calculate the radius
    r = truck_length / (math.tan(angle_radians) + 1e-5)

    return np.abs(r)


def critical_speed(r, h_cm, semi_trackwidth):
    """
    Calculate the critical speed for a given radius, height, and semi track width.

    Parameters:
    r (float): The radius of the turn in meters.
    h_cm (float): The height of the vehicle's center of mass in meters.
    semi_trackwidth (float): The semi track width of the vehicle in meters.

    Returns:
    float: The critical speed in miles per hour.

    Raises:
    ValueError: If the input parameters are not of the expected type or are non-positive.
    """

    # Validate input parameters
    if not all(isinstance(param, (int, float)) and param > 0 for param in [r, h_cm, semi_trackwidth]):
        raise ValueError(
            "All parameters must be positive numbers (int or float).")

    # Constants
    g = 9.81  # Acceleration due to gravity in m/s^2
    METER_PER_SECOND_TO_MILES_PER_HOUR = 2.23694  # Conversion factor

    # Calculate critical speed in meters per second
    crit_speed = np.sqrt((g * semi_trackwidth) / (2 * h_cm) * r)

    # Convert to miles per hour
    critical_speed_mph = crit_speed * METER_PER_SECOND_TO_MILES_PER_HOUR

    return critical_speed_mph


def height_of_center_of_gravity(mass_truckhead, mass_reeftrailor,
                                height_of_center_of_gravity_truckhead,
                                height_of_center_of_gravity_trailer):
    """
    Calculate the combined height of the center of gravity for a truck and its trailer.

    Parameters:
    mass_truckhead (float): The mass of the truck head in kilograms.
    mass_reeftrailor (float): The mass of the reef trailer in kilograms.
    height_of_center_of_gravity_truckhead (float): The height of the truck head's center of gravity in meters.
    height_of_center_of_gravity_trailer (float): The height of the trailer's center of gravity in meters.

    Returns:
    float: The combined height of the center of gravity for the truck and trailer in meters.
    """
    h_cm = ((mass_truckhead * height_of_center_of_gravity_truckhead) +
            (mass_reeftrailor * height_of_center_of_gravity_trailer)) / \
        (mass_truckhead + mass_reeftrailor)

    return h_cm


if __name__ == '__main__':
    # Load the data from the CSV file into a dataframe (df)

    stream = 'input.csv'  # takes a batch of stream data after 10s
    gps_df = data_frame(stream)

    # Convert 'timestamp' to datetime object
    gps_df['timestamp'] = pd.to_datetime(gps_df['timestamp'])

    # Calculate the angular distance between consecutive headings
    gps_df['previous_heading'] = gps_df['direction'].shift()
    gps_df['angular_distance'] = gps_df.apply(lambda row: angular_distance(
        row['previous_heading'], row['direction']), axis=1)

    # Convert speed from miles per hour to meters per second
    gps_df['speed_mps'] = gps_df['speed_mph']*.44704

    # Calculate the radius of the circle formed by the angular distance and truck length
    gps_df['radius'] = gps_df['angular_distance'].apply(find_adjacent)

    # Calculate the combined height of the center of gravity for the truck and trailer
    h_cm = height_of_center_of_gravity(mass_truckhead,
                                       mass_reeftrailor,
                                       height_of_center_of_gravity_truckhead,
                                       height_of_center_of_gravity_trailer)

    # Calculate the critical speed for each radius
    gps_df['critical_speed'] = gps_df['radius'].apply(critical_speed)

    # Determine if the speed is greater than the critical speed
    gps_df['result'] = np.where(
        gps_df.critical_speed <= gps_df['speed_mph'], 1, 0)
    sharpTurn_index = np.where(gps_df.result == 1)

    # Get the rows where the speed is greater than the critical speed
    sharp_turn_rows = gps_df.iloc[sharpTurn_index[0]]
    print(sharp_turn_rows)

    # Return boolean value if the truck is in a sharp turn--[store metadata in seperate file]
    # append the data to a csv file
