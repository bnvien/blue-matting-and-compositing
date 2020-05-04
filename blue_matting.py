import argparse
import numpy as np
import cv2 as cv
import os

parser = argparse.ArgumentParser()
# Input Option
parser.add_argument("--video_path", dest='video_path', nargs='?', help="Path to the video to be processed")
parser.add_argument("--bg_path", dest='bg_path', nargs='?', help="Path to the new background image")
parser.add_argument("--bg_color", dest='bg_color', nargs='?', help="Blue or green screen. E.g.: green")
parser.add_argument("--a1", dest='a1', nargs='?', help="Value for a1 - a hyperparameter to control the matting quality")
parser.add_argument("--a2", dest='a2', nargs='?', help="Value for a2 - a hyperparameter to control the matting quality")
args = parser.parse_args()

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

def extractFrames(video_path):
    """ Extract frames from a given video and write to files in folder 'tmp\frame'
    Input:
    - video_path: (str) path to the input video
    
    Returns:
    - fps: fps of the video
    - width: (int) width of the frames
    - height: (int) height of the frames
    """
    # load the input video
    video_capture = cv.VideoCapture(video_path)
    # get fps, width and height
    fps = video_capture.get(cv.CAP_PROP_FPS)
    width = int(video_capture.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv.CAP_PROP_FRAME_HEIGHT))
    
    if video_capture.isOpened():
        # get the total number of frames in the input video
        frame_num = int(video_capture.get(cv.CAP_PROP_FRAME_COUNT))
        for i in range(frame_num):
            # read each frame
            success, frame = video_capture.read() 
            # Save frame as a png image
            cv.imwrite("tmp\\frame\\frame" + str(i).zfill(6) +".png", frame)
    return fps, width, height

def combineImages(image_folder, video_name, fps, width, height):
    """ Combine all png images in a given folder to create a soundless video,
    then write the video to an mp4 file.
    
    Inputs:
    - image_folder: (str) the path to the folder
    - video_name: (str) desire name for the output video
    - fps: (float) desire fps of the output video
    - width: (int) width of the images
    - height: (int) heigh of the images
    """
    # select codec openh264 ('avc1') codec; mpeg-4 codec can be also be used ('mp4v')
    fourcc = cv.VideoWriter_fourcc(*'avc1')
    # create VideoWrite obj
    video = cv.VideoWriter("results\\" + video_name, fourcc, fps, (width, height))
    # load of image filenames
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    
    for image in images:
        # write every image to the video
        video.write(cv.imread(os.path.join(image_folder, image)))

    video.release()

if __name__ == '__main__':
    if args.video_path is None:
        print("Please enter the path to the video to be processed in the argument --video_path")
    else:
        video_path = args.video_path
    if args.bg_path is None:
        print("Please enter the path to the new background image in the argument --bg_path")
    else:
        bg_path = args.bg_path
    if args.bg_color is None:
        print("Please specify which screen is being used in the argument --bg_color")
    else:
        bg_color = args.bg_color
    if args.a1 is None:
        a1 = 1.0
    else:
        a1 = args.a1
    if args.bg_color is None:
        a2 = 1.0
    else:
        a2 = args.a2
    
    # check if folder tmp exists. If not create one
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    # check if folder 'tmp\frame' exists. If not create one to store temporary frames
    if not os.path.exists("tmp\\frame"):
        os.makedirs("tmp\\frame")
    # check if folder 'tmp\composite' exists. If not create one to store temporary composite images
    if not os.path.exists("tmp\\composite"):
        os.makedirs("tmp\\composite")
    # check if output folder exists. If not create one
    if not os.path.exists("results"):
        os.makedirs("results")
    
    print("Processing..")
    # first extract images from the video to folder 'tmp\frame'
    fps, width, height = extractFrames(video_path)
    print("Frame extraction is done!")

    print("Processing..")
    # then composite frames with the chosen background and write composite images to folder 'tmp\composite'
    for file in [file for file in os.listdir("tmp\\frame") if file.endswith('.png')]:
        composite_img = composite("tmp\\frame\\" + file, bg_path, bg_color=bg_color, a1=float(a1), a2=float(a2))
        # convert from rgb to bgr image
        composite_img = composite_img[:,:,::-1]
        # write composite image to file
        cv.imwrite("tmp\\composite\\" + os.path.basename(file), composite_img)
    print("Image matting and compositing is done!")

    print("Processing..")
    output_name = 'composite_video_' + os.path.splitext(os.path.basename(video_path))[0] + '.mp4'
    # combine all composite images into a video named 'composite_video.mp4'
    combineImages('tmp\\composite', output_name, fps, width, height)
    print("The process has finished! Please look for the file " + output_name)