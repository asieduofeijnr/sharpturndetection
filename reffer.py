import numpy as np                              
import pandas as pd
from datetime import datetime                                                                        


gps_df = pd.read_csv('./sample_gps_data.csv')

"""
calculate the raduis of the turn for each row of the data based upon the direction and speed
the raduis in in meters
"""
w = gps_df['direction']*0.0174533
v = gps_df['speed_mph']*.44704
R = v/w

m_truck = (6800 + 11300)/2
m_trailor = (7500 + 36287)/2
semi = 264.16
h_truck = 1
h_trailor = 1.5

h_cm = (m_truck * h_truck + m_trailor * h_trailor)/(m_trailor + m_truck)






def v_crit(r,h,t):
    """takes in r in meters, h in meters and t in meters gives back a velo crical value in miles per hour"""
    g = 9.81
    rest = (g*t)/(2*h)
    pre_sq = rest*r
    crit = np.sqrt(pre_sq)
    mph_crit = crit * 2.23694
    return mph_crit
def r_crit(v,h,t):
    """takes in v in m/s, h in meters and t in meters gives back a radius crical value in meters"""
    velo = np.array(v)
    g = 9.81
    output = ((v**2) * (2 * h)) / (g * t)
    return output




m_truck = (6800 + 11300)/2
m_trailor = (7500 + 36,287)/2
h_truck = 1
h_trailor = 1.5

h_cm = (m_truck * h_truck + m_trailor * h_trailor)/(m_trailor + m_truck)

velocity_crit = v_crit(R,h_cm,semi)
gps_df['velocity_crit'] = velocity_crit
result_velo = np.where(gps_df['velocity_crit'] < gps_df['speed_mph'],1,0)
indices_with_one_velo = np.where(result_velo == 1)[0]
elements = gps_df.loc[indices_with_one_velo, 'timestamp']
if len(elements) != 0:
    print('These were the times in which you reached the critical velocity threhold')
    print(elements)

