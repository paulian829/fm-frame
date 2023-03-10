import cv2
from imutils.video import WebcamVideoStream, VideoStream
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from playsound import playsound
import time
import _thread
import requests
import base64
import json
import uuid


class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0.
        print('test if initated succesfully')
        # self.stream = WebcamVideoStream(
        #     src='rtsp://tapocamera:123456@192.168.1.100:554/stream1').start()
        self.stream = WebcamVideoStream(
            src=0).start()
        prototxtPath = "face_detector/deploy.prototxt"
        weightsPath = "face_detector/res10_300x300_ssd_iter_140000.caffemodel"
        self.faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)
        self.soundOn = False
        self.reset_sound = False

        print("[INFO] loading face mask detector model...")
        filen = "mask_detector.model"
        self.maskNet = load_model(filen)
        print("Face mask model loaded")

    def __del__(self):
        self.stream.stop()

    def predict(self, frame, faceNet, maskNet):
        # grab the dimensions of the frame and then construct a blob
        # from it
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
                                     (104.0, 177.0, 123.0))

        # pass the blob through the network and obtain the face detections
        faceNet.setInput(blob)
        detections = faceNet.forward()
        # initialize our list of faces, their corresponding locations,
        # and the list of predictions from our face mask network
        faces = []
        locs = []
        preds = []

        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with
            # the detection
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the confidence is
            # greater than the minimum confidence
            if confidence > 0.8:  # Adjust this value to adjust confident threshold
                # compute the (x, y)-coordinates of the bounding box for
                # the object
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # ensure the bounding boxes fall within the dimensions of
                # the frame
                (startX, startY) = (max(0, startX), max(0, startY))
                (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

                # extract the face ROI, convert it from BGR to RGB channel
                # ordering, resize it to 224x224, and preprocess it
                face = frame[startY:endY, startX:endX]
                face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                face = cv2.resize(face, (224, 224))
                face = img_to_array(face)
                face = preprocess_input(face)

                # add the face and bounding boxes to their respective
                # lists
                faces.append(face)
                locs.append((startX, startY, endX, endY))
        # only make a predictions if at least one face was detected
        if len(faces) > 0:
            print(len(faces))
            # for faster inference we'll make batch predictions on *all*
            # faces at the same time rather than one-by-one predictions
            # in the above `for` loop
            faces = np.array(faces, dtype="float32")
            preds = maskNet.predict(faces, batch_size=32)
        # return a 2-tuple of the face locations and their corresponding
        # locations
        return (locs, preds)

    def get_frame(self):
        print(self.stream)
        image = self.stream.read()

        # load face detect model from disk
        # prototxtPath = "face_detector/deploy.prototxt"
        # weightsPath = "face_detector/res10_300x300_ssd_iter_140000.caffemodel"
        # faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

        # load the face mask detector model from disk
        # print("[INFO] loading face mask detector model...")
        # filen = "mask_detector.model"
        # maskNet = load_model(filen)
        # print("Face mask model loaded")
        while True:
            # detect faces in the frame and determine if they are wearing a
            # face mask or not
            try:
                (locs, preds) = VideoCamera.predict(
                    self, image, self.faceNet, self.maskNet)
            except:
                (locs, preds) = VideoCamera.predict(
                    self, image, self.faceNet, self.maskNet)
            # loop over the detected face locations and their corresponding
            # locations
            # print(locs,preds)
            if len(locs) == 0:
                print('reset')
                self.soundOn = False
            for (box, pred) in zip(locs, preds):
                # unpack the bounding box and predictions
                (startX, startY, endX, endY) = box
                (mask, withoutMask) = pred

                # determine the class label and color we'll use to draw
                # the bounding box and text
                label = "Mask" if mask > withoutMask else "No Mask"
                color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
                print(label)
                if label == 'Mask':
                    self.soundOn = False
                else:
                    if self.soundOn == False:
                        self.soundOn = True
                        cv2.imwrite('test.jpg', image)
                        _thread.start_new_thread(
                            threaded_api_call, ('Thread-name', 2))

                # include the probability in the label
                label = "{}: {:.2f}%".format(
                    label, max(mask, withoutMask) * 100)

                # display the label and bounding box rectangle on the output
                # frame
                cv2.putText(image, label, (startX, startY - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
                cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)

            # Convert to JPG encoding
            ret, jpeg = cv2.imencode('.jpg', image)

            data = []
            data.append(jpeg.tobytes())
            return data


def threaded_api_call(thread_name, delay):
    """
    https://stackoverflow.com/questions/29104107/upload-image-using-post-form-data-in-python-requests

    https://www.tutorialspoint.com/python3/python_multithreading.htm

    https://stackoverflow.com/questions/534839/how-to-create-a-guid-uuid-in-python1

    """
    playsound('warning sound.mp3')

    # Change this depending on API ENDPOINT
    api = 'https://fmthesis.pythonanywhere.com/add_image/'
    image_file = 'test.jpg'

    with open(image_file, "rb") as f:
        im_bytes = f.read()
    im_b64 = base64.b64encode(im_bytes).decode("utf8")

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    print(im_b64)
    payload = json.dumps(
        {"file": im_b64, "filename": str(uuid.uuid4()) + '.jpg'})
    response = requests.post(api, data=payload, headers=headers)
    try:
        data = response.json()
        print(data)
    except requests.exceptions.RequestException:
        print(response.text)
