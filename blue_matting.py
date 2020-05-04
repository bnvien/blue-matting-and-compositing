import numpy as np
import cv2 as cv

def composite(input_img_path, new_bg_path, bg_color="blue", a1=1.0, a2=1.0):
    """ Compute alpha matte of the input image and then compisite the extracted foreground
    object with the new background image.
    
    Inputs:
    - input_img_path: (str) path to the input image
    - new_bg_path: (str) path to the background image
    - bg_color: (str) "blue" or "green", specify blue screen or green screen is being used
    - a1: (positive float) adjustable parameter 1
    - a2: (positive float) adjustable parameter 2
    
	Return:
	- composite_img: (np.ndarray) compisite image
    """
    
    # read input image
    img = cv.imread(input_img_path)
    # convert from bgr to rgb image
    img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    # rescale to [0,1]
    img_rgb = img_rgb/255.0

    # read new background image
    new_bg_img = cv.imread(new_bg_path)
    # resize to backgroudn image to the size of the input image
    new_bg_img = cv.resize(new_bg_img, (img_rgb.shape[1], img_rgb.shape[0]), interpolation=cv.INTER_AREA)
    # convert from bgr to rgb
    new_bg_img_rgb = cv.cvtColor(new_bg_img, cv.COLOR_BGR2RGB)
    # rescale to [0,1]
    new_bg_img_rgb = new_bg_img_rgb/255.0

    # in case the image has blue screen
    if bg_color == 'blue':
        # calculate alpha matte using First Vlahos Form: alpha = 1-a1*(Bf-a2*Gf)
        alpha_matte = 1 - a1*(img_rgb[:,:,2] - a2*img_rgb[:,:,1])

        # clamp alpha matte to [0,1]
        alpha_matte = np.clip(alpha_matte, 0.0, 1.0)

        # create foreground image
        foreground_img = np.zeros_like(img_rgb)
        # extract the foreground object out of the input image
        foreground_img[:,:,0] = img_rgb[:,:,0]*alpha_matte
        foreground_img[:,:,1] = img_rgb[:,:,1]*alpha_matte
        foreground_img[:,:,2] = img_rgb[:,:,2]*alpha_matte

        # clamp blue channel of foreground image to min(Bf, a2Gf)
        foreground_img[:,:,2] = np.minimum(foreground_img[:,:,2], a2*foreground_img[:,:,1])
    
    # in case the image has green screen
    else:                   
        # calculate alpha matte using First Vlahos Form: alpha = 1-a1*(Gf-a2*Bf)
        alpha_matte = 1 - a1*(img_rgb[:,:,1] - a2*img_rgb[:,:,2])

        # clamp alpha matte to [0,1]
        alpha_matte = np.clip(alpha_matte, 0.0, 1.0)

        # create foreground image
        foreground_img = np.zeros_like(img_rgb)
        # extract the foreground object out of the input image
        foreground_img[:,:,0] = img_rgb[:,:,0]*alpha_matte
        foreground_img[:,:,1] = img_rgb[:,:,1]*alpha_matte
        foreground_img[:,:,2] = img_rgb[:,:,2]*alpha_matte

        # clamp green channel of foreground image to min(Gf, a2Bf)
        foreground_img[:,:,1] = np.minimum(foreground_img[:,:,1], a2*foreground_img[:,:,2])

    # alter the new background image by holding out the area that belongs to the foreground object
    background = np.zeros_like(img_rgb)
    background[:,:,0] = new_bg_img_rgb[:,:,0]*(1-alpha_matte)
    background[:,:,1] = new_bg_img_rgb[:,:,1]*(1-alpha_matte)
    background[:,:,2] = new_bg_img_rgb[:,:,2]*(1-alpha_matte)

    # create the composite image
    composite_img = foreground_img + background
    # rescale to [0,255]
    composite_img = (composite_img * 255).astype(np.uint8)
    
    return composite_img
