#!/usr/bin/env python

# BIG TAKEAWAY: sourcing camerawork moves PYTHONPATH (echo $PYTHONPATH) to ros kinetic directory
#               instead of the proper location

import os
import numpy as np
import matplotlib.pyplot as plt
import time
import rospy
from sensor_msgs.msg import Image as msg_image
from std_msgs.msg import Int32
from geometry_msgs.msg import Vector3, Twist
import message_filters
import pyrealsense2 as rs

from cv_bridge import CvBridge, CvBridgeError

import sys
#change path to insert correct version of cv2
#sys.path.insert(0,'/home/eecs106a/.local/lib/python2.7/site-packages')

import cv2



 # Create a CvBridge to convert ROS messages to OpenCV images
bridge = CvBridge()


class Tracker:
    def __init__(self, height, width, color_lower, color_upper):
        self.color_lower = color_lower
        self.color_upper = color_upper
        self.midx = int(width / 2)
        self.midy = int(height / 2)
        self.xoffset = 0
        self.yoffset = 0

    def draw_arrows(self, frame):
        return frame

    def track(self, frame):
        # Apply Gaussian Blur to filter image and blur out noise
        blurred = cv2.GaussianBlur(frame, (5, 5), 0) #pass in image, kernel size, and std dev
        # Convert blurred image from BGR to HSV (hue, saturation, value) color mode
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        # Threshold the HSV image using the low and high HSV threshold values
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        # Erode away boundaries of regions of foreground pixels (usually white)
        mask = cv2.erode(mask, None, iterations=2)
        # Expand the boundaries of regions of foreground pixels (usually white)
        mask = cv2.dilate(mask, None, iterations=2)
        # Show the image (now named mask) after applying filters
        #cv2.imshow('mask', mask)
        # Find contours in image (image, contour retrieval mode, contour approximation method)
        # Contours stored as vectors of points, hierarchy is unused
        contours, hierarchy= cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Initialize the centroid of the object
        center = None
        radius = 0

        if len(contours) > 0:
            # Find the contour with the greatest contour area
            c = max(contours, key=cv2.contourArea)
            # Find a circle of the minimum area enclosing the contour points
            # Outputs (x,y) center coordinates and radius of circle
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            # Get dictionary of all moment values calculated
            M = cv2.moments(c)
            # Calculate the centroid of the object
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            if radius > 8:
                # Draw a circle outlining the object (image, center, radius, color, thickness)
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                # Draw a circle tracking the centroid of the object
                # Negative thickness creates a filled circle
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                # Set the offset values to the current centroid
                self.xoffset = int(center[0])
                self.yoffset = int(center[1])
            else:
                self.xoffset = -1
                self.yoffset = -1
        else:
            self.xoffset = -1
            self.yoffset = -1
        #print(center)
        return self.xoffset, self.yoffset, frame, radius


def parabolic(radius):
    a0 = 2.59936585e+01
    a1 = -3.72791626e-01
    a2 = 1.32533945e-03
    return a2*radius*radius + a1*radius + a0

def get_height(radius):
    return parabolic(radius)


# Converts a ROS Image message to a NumPy array to be displayed by OpenCV
def ros_to_cv2_img(ros_img_msg):
	return np.array(bridge.imgmsg_to_cv2(ros_img_msg,'bgr8'))


### ROS subscriber nonsense
def callback(message):

	#converts from ROS format to cv2 format
    image = ros_to_cv2_img(message)


    #cv2.imwrite("7.jpeg", image)
    print(cv2.__version__)

    #EDIT THIS TO LOAD IMAGE IN TRACK
    '''X, Y, img1, radius = ball_tracker.track(image)

    Z = get_height(radius)
    tw = Twist()
    tw.linear.x = X
    tw.linear.y = Y
    tw.linear.z = Z
    tw.angular.x = 0.0
    tw.angular.y = 0.0
    tw.angular.z = 0.0

    camera_pub.publish(tw)

    # print("image save")
    cv2.imshow("Image window", img1)
    cv2.waitKey(1)'''


    #X,Y,Z should be changed based on image processing




#Define the method which contains the node's main functionality
def listener():

    #Run this program as a new node in the ROS computation graph
    #called /listener_<id>, where <id> is a randomly generated numeric
    #string. This randomly generated name means we can start multiple
    #copies of this node without having multiple nodes with the same
    #name, which ROS doesn't allow.
    rospy.init_node('Image_Processor', anonymous=True)

    #Create a new instance of the rospy.Subscriber object which we can
    #use to receive messages of type std_msgs/String from the topic /chatter_talk.
    #Whenever a new message is received, the method callback() will be called
    #with the received message as its first argument.


    #/camera/color/image_raw - Should be something along this line

    ############################### Might have to change on Cassie##################
    rospy.Subscriber("/device_0/sensor_1/Color_0/image/data", msg_image, callback)

    #Wait for messages to arrive on the subscribed topics, and exit the node
    #when it is killed with Ctrl+C
    rospy.spin()

def main():

    z0 = 103.1875 #[mm]
    r0 = 153.6826171875

    r1 = (60.24595642089844 + 61.16786193847656)/2
    z1 = z0 + 203.2 #[mm]

    r2 = 38.5520133972168
    z2 = z0 + 381 #[mm]

    # Initialize lower and upper HSV threshold values for ping pong ball
    H_scale = 255/360.0 #H values span from 0-360
    S_V_scale = 255/100.0 #S and V values span from 0-100

    #CHANGE THESE HSV VALUES
    H_low = 0
    S_low = 16
    V_low = 44
    H_high = 20
    S_high = 100
    V_high = 100

    #Use HSV Color Picker values and scale to 0-255 range
    ball_lower = (int(H_low*H_scale), int(S_low*S_V_scale), int(V_low*S_V_scale))
    ball_upper = (int(H_high*H_scale), int(S_high*S_V_scale), int(V_high*S_V_scale))


    # Configure the depth and colour streams
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)

    # Start streaming
    profile = pipeline.start(config)

    # Intrinsic matrix
    depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
    depth_intrinsics = depth_profile.get_intrinsics()

    # Get the depth sensor's depth scale
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()

    # Align the depth stream to the RGB stream
    align_to = rs.stream.color
    align = rs.align(align_to)

    # Create a ball tracker
    ball_tracker = Tracker(640, 480, ball_lower, ball_upper)

    # Create a camera node
    rospy.init_node('ball_tracker', anonymous=True)
    camera_pub = rospy.Publisher('/middleware/ball_position', Twist, queue_size=10)

    # Set loop rate
    loop_rate = 600
    dt = 1/loop_rate
    rate = rospy.Rate(loop_rate)

    for i in range(0,50):
        frames = pipeline.wait_for_frames()

    while not rospy.is_shutdown():
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not aligned_depth_frame or not color_frame:
            continue

        #color_frame = frames.get_color_frame()
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        depth_intrinsics = rs.video_stream_profile(aligned_frames.profile).get_intrinsics()
        depth_to_color_extrin = aligned_depth_frame.profile.get_extrinsics_to(color_frame.profile)

        #use track method to find radius
        X, Y,img1,radius = ball_tracker.track(color_image)
        print(X,Y)
        #cv2.imshow('RealSense', images)
        cv2.imshow('RealSense', img1)
        cv2.waitKey(1)

        Depth_rgb = get_height(radius)
        color_image = ball_tracker.draw_arrows(color_image)
        #Take depth at the centroid and above/below/left/right at a distance of radius/3
        Depth = rs.depth_frame.get_distance(aligned_depth_frame, X, Y)
        Depth_a = rs.depth_frame.get_distance(aligned_depth_frame, X, np.uint8(Y+radius/5))
        Depth_b = rs.depth_frame.get_distance(aligned_depth_frame, X, np.uint8(Y-radius/5))
        Depth_l = rs.depth_frame.get_distance(aligned_depth_frame, np.uint8(X-radius/5), Y)
        Depth_r = rs.depth_frame.get_distance(aligned_depth_frame, np.uint8(X+radius/5), Y)
        X, Y, Z = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [X, Y], Depth*depth_scale)
        X_a, Y_a, Z_a = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [X, np.uint8(Y+radius/5)], Depth_a)
        X_b, Y_b, Z_b = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [X, np.uint8(Y-radius/5)], Depth_b)
        X_l, Y_l, Z_l = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [np.uint8(X-radius/5), Y], Depth_l)
        X_r, Y_r, Z_r = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [np.uint8(X+radius/5), Y], Depth_r)
        color_point = rs.rs2_transform_point_to_point(depth_to_color_extrin, [X, Y, Z])
        '''Z_values = np.array([Z, Z_a, Z_b, Z_l, Z_r])
        #Calculate min Z value out of all 5 data points (excluding those that are 0 and nan)
        Z_avg = Z_values[Z_values!=0]'''
        Depth_values = np.array([Depth, Depth_a, Depth_b, Depth_l, Depth_r])
        #Calculate min Z value out of all 5 data points (excluding those that are 0 and nan)
        Depth_avg = Depth_values[Depth_values!=0]

        #publish the x,y,z
        tw = Twist()
        tw.linear.x = color_point[0]
        tw.linear.y = color_point[1]
        tw.linear.z = 0.0
        tw.angular.x = 0.0
        tw.angular.y = 0.0
        tw.angular.z = 0.0

        #publish the x,y,z
        if len(Depth_avg) > 0:
            Depth_avg = np.nanmin(Depth_avg)
            #tw.linear.z = Depth_avg
            tw.linear.z = color_point[2]
            #print(X,Y,Depth_avg)
        else:
            tw.linear.z = Depth_rgb*.0254
        #print(tw.linear)
        camera_pub.publish(tw)


        # print("depth_sensor: " +str(Z_avg) + "; Other Z:" + str(.0254*Z_rgb))


       # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        #images = np.hstack((color_image, depth_colormap))
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img1, 'Y: %.4f, X: %.4f Depth Sensor: %.4f RGB Depth: %.4f'%(Y, X, Depth, Depth_rgb), (10,450), font, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)


        key = cv2.waitKey(30)
        if key == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
        rate.sleep()
    pipeline.stop()


if __name__ == '__main__':
    main()
