import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select
    

def obstacle_detection(img, rgb_thresh=(160, 160, 160)):
        color_select = np.zeros_like(img[:,:,0])
        above_thresh = (img[:,:,0] < rgb_thresh[0]) \
                    & (img[:,:,1] < rgb_thresh[1]) \
                    & (img[:,:,2] < rgb_thresh[2])
            
        color_select[above_thresh] = 1
        #obstacle = np.nonzero(color_select)
        return color_select

def rock_detection(img, rgb_rock_low=(130, 130, 0), rgb_rock_hi=(160, 160, 40)):
        color_select = np.zeros_like(img[:,:,0])
        above_thresh = ~((img[:,:,0] > rgb_rock_low[0]) & (img[:,:,0] < rgb_rock_hi[0])\
                    & (img[:,:,1] > rgb_rock_low[1])  & (img[:,:,1] < rgb_rock_hi[1])\
                    & (img[:,:,2] > rgb_rock_low[2])  & (img[:,:,2] < rgb_rock_hi[2]))
        color_select[above_thresh] = 1
        #rock_pos = np.nonzero(color_select)
        return color_select

# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[0]).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def pix_to_world(xpix, ypix, x_rover, y_rover, yaw_rover, world_size, scale):
    # Map pixels from rover space to world coords
    yaw = yaw_rover * np.pi / 180
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_((((xpix * np.cos(yaw)) - (ypix * np.sin(yaw)))/scale) + x_rover), 
                            0, world_size - 1)
    y_pix_world = np.clip(np.int_((((xpix * np.sin(yaw)) + (ypix * np.cos(yaw)))/scale) + y_rover), 
                            0, world_size - 1)
  
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    
    ## 1) Define source and destination points for perspective transform
    # Define calibration box in source (actual) and destination (desired) coordinates
    # These source and destination points are defined to warp the image
    # to a grid where each 10x10 pixel square represents 1 square meter
    # The destination box will be 2*dst_size on each side
    dst_size = 5 
    # Set a bottom offset to account for the fact that the bottom of the image 
    # is not the position of the rover but a bit in front of it
    # this is just a rough guess, feel free to change it!
    bottom_offset = 6
    image = Rover.img
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                      [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                      [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset], 
                      [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                      ])
                      
    ## 2) Apply perspective transform
    
    warped = perspect_transform(image, source, destination)
    
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    
    terrain = color_thresh(warped)
    obstacle = obstacle_detection(warped)
    rock = rock_detection(warped)
    
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)

    Rover.vision_image[:,:,0] = terrain * 255
    Rover.vision_image[:,:,1] = obstacle * 255
    Rover.vision_image[:,:,2] = rock * 255
    
    # 5) Convert map image pixel values to rover-centric coords
    
    rTerrain = rover_coords(terrain)
    rObstacle = rover_coords(obstacle)
    rRock = rover_coords(rock)
    
    # 6) Convert rover-centric pixel values to world coordinates

    scale = 10
    # Get navigable pixel positions in world coords
    #####PB
    wTerrain = pix_to_world(rTerrain[0],rTerrain[1], Rover.pos[0], 
                                    Rover.pos[1], Rover.yaw, 
                                    Rover.worldmap.shape[0], scale)
    wObstacle = pix_to_world(rObstacle[0],rObstacle[1], Rover.pos[0], 
                                    Rover.pos[1], Rover.yaw, 
                                    Rover.worldmap.shape[0], scale)
    wRock = pix_to_world(rRock[0],rRock[1], Rover.pos[0], 
                                    Rover.pos[1], Rover.yaw, 
                                    Rover.worldmap.shape[0], scale)
    
    # 7) Update Rover worldmap (to be displayed on right side of screen)

    
    wTerrain = np.flipud(wTerrain)
    Rover.worldmap[wTerrain[0],wTerrain[1],2] += 1    
    Rover.worldmap[wRock[0],wRock[1],1] += 1

    # 8) Convert rover-centric pixel positions to polar coordinates
    
    Rover.nav_dists, Rover.nav_angles = to_polar_coords(rTerrain[0],rTerrain[1])
    
    # Update Rover terrain, a variable that has information about where the Rover can navigate
    Rover.terrain = terrain
    
    
    
    
    
    return Rover