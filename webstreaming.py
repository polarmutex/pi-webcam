"""
TODO fix this reference
taken from piimagesearch
"""

from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2

# initialize the output frame and a lock used to ensure therad-safe exchange of the output frames (usefuk when multiple browers/tabs are viewing the stream)
output_frame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)

# initialize the video stream and allow the camera sensor to warmup
vs = VideoStream(usePiCamera=1, resolution=(1280,780)).start()
time.sleep(2.0)

@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")

def run_webcam():
    # grab global reference to the videostream, output frame, and lock variables
    global vs, output_frame, lock

    # loop over frames from the video stream
    while True:
        # read the next frame from the video stream
        frame = vs.read()

        frame = imutils.rotate(frame, 90)

        #print(frame.shape)

        # grab the current timestamp and draw it on the frame
        timestamp = datetime.datetime.now()
        cv2.putText(frame, 
                timestamp.strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (0,0,255),
                1)

        # acquire the lock, set the putput frame, and release the lock
        with lock:
            output_frame = frame.copy()

def generate():
    # grab the global refernece to the output frame and lock variables
    global output_frame, lock

    # loop over frames from the output stream
    while True:
        # wait till the lock is aquired
        with lock:
            # check if the output frame is available, otherwise skip the iteration of the loop
            if output_frame is None:
                continue

            # encode the frame in JPEG format
            (flag, encoded_img) = cv2.imencode(".jpg", output_frame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

            # yield the output frame in the byte format
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_img) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media typw (mime type)
    return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == "__main__":
    # construct the arguement parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True, help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True, help="port of the device (1024 to 65535)")

    args = vars(ap.parse_args())

    # start a thread that will perform webcam
    t = threading.Thread(target=run_webcam)
    t.daemon = True
    t.start()

    # start flask app
    app.run(
            host=args["ip"],
            port=args["port"],
            debug=True,
            use_reloader=False)

    # release the video stream pointer
    vs.stop()

