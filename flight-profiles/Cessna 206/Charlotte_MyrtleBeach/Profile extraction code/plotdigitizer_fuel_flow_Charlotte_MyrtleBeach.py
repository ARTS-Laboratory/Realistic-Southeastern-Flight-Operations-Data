import cv2
import matplotlib.pyplot as plt
import numpy as np

# Load the image
image_path =  r"c:\Users\oadebajo\OneDrive\Documents\Flight load profiles\Charlotte to Myrtle Beach\Profile10\Picture10_fuel.png" # Change this to your image file
image = cv2.imread(image_path)

# Convert to HSV (Hue, Saturation, Value) to detect blue
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define range for blue color (adjust if needed)
#lower_blue = np.array([100, 5, 50])
#upper_blue = np.array([130, 255, 255])
lower_blue = np.array([100, 15, 215])  
upper_blue = np.array([107, 60, 245])  


#lower_blue = np.array([100, 5, 80])  # Slightly lower than the minimum values
#upper_blue = np.array([210, 40, 245])

# Threshold to create a binary mask
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Find contours of the extracted blue region
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Extract curve points
data_points = []
for contour in contours:
    for point in contour:
        x, y = point[0]  # Get x, y pixel coordinates
        data_points.append((x, y))

# Convert to NumPy array and sort by x-values (time axis)
data_points = np.array(data_points)
data_points = data_points[data_points[:, 0].argsort()]
data_points[:, 1] *= -1
min_fuel_flow=np.min(data_points[:,1])
data_points[:, 1] += (min_fuel_flow*-1)
data_points[:,1] += 10
# Save extracted points

np.savetxt(r"C:\Users\oadebajo\OneDrive\Documents\Flight load profiles\Charlotte to Myrtle Beach\Profile10\fuel_flow\extracted_points.csv", data_points, delimiter=",", header="x_pixel,y_pixel", comments="")

# Plot for visualization
#plt.imshow(image)
plt.scatter(data_points[:, 0], data_points[:, 1], color='red', s=1)
plt.title("Extracted Data Points")
plt.show()

print("Extracted points saved as 'extracted_points.csv'")
# Get Y1 (first y-value) and Y2 (max y-value)
Y1 = data_points[0, 1]
Y2 = np.max(data_points[:, 1])

# Prompt user for RPM1 and RPM2
fuel_flow1 = float(input("Enter fuel_flow1 (corresponding to Y1, first point): "))
fuel_flow2 = float(input("Enter fuel_flow2 (corresponding to Y2, max point): "))

# Compute the scale factor
scale_y = (fuel_flow2 - fuel_flow1) / (Y2 - Y1)

# Adjust y-values to RPM scale
fuel_flow_values = fuel_flow1 + (data_points[:, 1] - Y1) * scale_y

# Prompt user for total time in minutes
total_time = float(input("Enter total time in minutes: "))

# Compute evenly spaced time values
num_points = len(data_points)
#time_values = np.linspace(0, total_time, num_points)
# Get min and max x-values from the image data
x_min = np.min(data_points[:, 0])  # Smallest x-value
x_max = np.max(data_points[:, 0])  # Largest x-value

# Remap x-values from [x_min, x_max] to [0, total_time]
time_values = (data_points[:, 0] - x_min) / (x_max - x_min) * total_time
#print(len(time_values))
#Create array of evenly spaced x values
new_time_values = np.linspace(np.min(time_values), np.max(time_values), len(time_values))

#interpolate to find y values for new x_values
new_fuel_flow_values = np.interp(new_time_values, time_values, fuel_flow_values)

#Create array with interpolated rpm and time
interp_time_vs_fuel_flow = np.column_stack((new_time_values, new_fuel_flow_values))

# Create array with Time vs Fuel flow
time_vs_fuel_flow = np.column_stack((time_values, fuel_flow_values))

# Print first few values to check
#print("First few rows of Time vs RPM data:")
#print(time_vs_rpm[:10])
plt.scatter(time_vs_fuel_flow[:, 0], time_vs_fuel_flow[:, 1], color='red', s=1)
plt.title("fuel flow vs time (Gal/Hr)")
plt.show()


#cONVERTING TO POWER
#interp_power_kw = 30 + ((new_rpm_values-1000)/150)
#interp_power_vs_time = np.column_stack((new_time_values, interp_power_kw))
fuel_flow_kg_hr = new_fuel_flow_values * 2.72  # Convert GPH → kg/hr
fuel_flow_kg_s = fuel_flow_kg_hr / 3600  # Convert kg/hr → kg/s
specific_energy_j_kg = 43.5e6  # 44.65 MJ/kg = 44.65 × 10^6 J/kg for 100VLL fuel
power_from_fuel_w = fuel_flow_kg_s * specific_energy_j_kg  # in watts
power_from_fuel_kw = power_from_fuel_w / 1000  # Convert to kW 

# Set varying bsfc values
takeoff_start = float(input("Enter time of takeoff start: "))
takeoff_stop = float(input("Enter takeoff stop time:"))
transition_duration = 0.2  # Transition lasts 60s (1 minute)
transition_duration2 = 0.3 # Transition lasts 60s (1 minute)


# Define transition points
efficiency_points_time = [
    0,                               # Before takeoff start
    takeoff_start,                   # Start of takeoff
    takeoff_start + transition_duration,  # End of first transition
    14.6,
    14.6,
    takeoff_stop - transition_duration2,  # Start of last transition
    takeoff_stop,                     # End of takeoff
    max(new_time_values)              # After takeoff (cruise)
]

efficiency_points_values = [
    0.28,  # Before takeoff
    0.28,  # Start of takeoff
    0.19,  # After first 1-minute transition (takeoff)
    0.19,
    0.23,
    0.23,  #0.19 # Before last 1-minute transition (takeoff)
    0.28,  # After takeoff stop (cruise)
    0.28   # After takeoff (cruise)
]

# Interpolate efficiency values smoothly
engine_efficiency_values = np.interp(new_time_values, efficiency_points_time, efficiency_points_values)

power_shaft_kw = power_from_fuel_kw * engine_efficiency_values

plt.plot(new_time_values, engine_efficiency_values, label="Engine Efficiency")
plt.xlabel("Time (s)")
plt.ylabel("Efficiency")
plt.title("Engine Efficiency Transition (Takeoff to Cruise)")
plt.show()
# Create array with power vs. time
power_shaft_vs_time_fuel = np.column_stack((new_time_values, np.full_like(time_values, power_shaft_kw)))

# Create array with power from fuel vs. time
power_vs_time_fuel = np.column_stack((new_time_values, np.full_like(time_values, power_from_fuel_kw)))

# Create array with power from fuel vs. time
#power_shaft2_vs_time_fuel = np.column_stack((new_time_values, np.full_like(time_values, power_shaft_kw_bsfc)))

plt.scatter(power_shaft_vs_time_fuel[:, 0], power_shaft_vs_time_fuel[:, 1], color='red', s=1)
plt.title("Power vs time (kW)")
plt.show()


#Save interpolated time and power to shaft as a csv file
np.savetxt(r"C:\Users\oadebajo\OneDrive\Documents\Flight load profiles\Charlotte to Myrtle Beach\Profile10\fuel_flow\interp_extracted_points_power1_shaft.csv", power_shaft_vs_time_fuel, delimiter=",", header="Time_mins,power_kw", comments="")

#Save Power versus time as csv file
np.savetxt(r"C:\Users\oadebajo\OneDrive\Documents\Flight load profiles\Charlotte to Myrtle Beach\Profile10\fuel_flow\interp_extracted_points_power_fuel.csv", power_vs_time_fuel, delimiter=",", header="Time_mins,Power_kW", comments="")

#Save Fuel flow vs. time file
np.savetxt(r"C:\Users\oadebajo\OneDrive\Documents\Flight load profiles\Charlotte to Myrtle Beach\Profile10\fuel_flow\extracted_points_fuel_flow.csv", time_vs_fuel_flow, delimiter=",", header="Time_mins,fuel flow (Gal/hr)", comments="")
print("Extracted points saved as '... extracted points.csv'")

