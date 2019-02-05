import numpy as np

# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
# Define a function to convert from cartesian to polar coordinates

    
def is_clear(Rover):
    #taking the pixels in front of the rover to see if the path is clear
    clear = (np.sum(Rover.terrain[140:150,150:170]) > 130)\
     & (np.sum(Rover.terrain[110:120,150:170]) > 100)\
     & (np.sum(Rover.terrain[150:153,155:165]) > 20)
    return clear 
    
    
def throttle(Rover):
    Rover.brake = 0
    if Rover.vel > Rover.max_vel: #throttle if velocity in under max velocity
        Rover.throttle = 0
    else:
        Rover.throttle = Rover.throttle_set

        
def best_way(Rover):
    avg_angle = np.mean(Rover.nav_angles)
       
    if (avg_angle > 0.1) & (Rover.steer < 10):
        Rover.steer = Rover.steer + 5
    elif (avg_angle < -0.1) & (Rover.steer > -10):
        Rover.steer += Rover.steer - 5
    else:
        Rover.steer = 0
        
    
def stop(Rover):
    Rover.steer = 0
    Rover.throttle = 0
    Rover.brake = 1
    
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!
    
    
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if (Rover.vel): #Moving?
        
            if is_clear(Rover):
                throttle(Rover)
                best_way(Rover)
            else:
                stop(Rover)
        else:
            if is_clear(Rover):
                throttle(Rover)
            else:
                Rover.brake = 0
                Rover.steer = -15.
                
    else:
        Rover.throttle = Rover.throttle_set

    return Rover

