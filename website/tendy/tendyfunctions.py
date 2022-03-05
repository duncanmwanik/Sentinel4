from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import imutils
import cv2
import os
import shutil
import datetime
from imutils import paths
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

import pyrebase
from getpass import getpass


#-----------  Initializing Firebase Functions -------------------START
firebaseconfig = {
    "apiKey": "AIzaSyCVEt5pXbBBWayikudil_YZDMX5GoA5Wos",
    "authDomain": "sentinel-b625c.firebaseapp.com",
    "databaseURL": "https://sentinel-b625c-default-rtdb.firebaseio.com",
    "projectId": "sentinel-b625c",
    "storageBucket": "sentinel-b625c.appspot.com",
    "messagingSenderId": "115615795651",
    "appId": "1:115615795651:web:107d63b8eefec5d4859576",
    "measurementId": "G-C4LP5G2GNS",
    "serviceAccount": "firebase/sentinel.json"
   } #------ Firebase Credentials Dictionary


firebase = pyrebase.initialize_app(firebaseconfig)
authorize = firebase.auth()
ref = firebase.database() #------ Firebase Reference for Realtime Database
storage = firebase.storage() #------ Firebase Reference for Firebase Storage

#-----------  Initializing Firebase Functions -------------------END

 
# -------------Face Recognition Code-----------------------------------START

def face_recognition(frame, channel, usd): #---- Function to Recognize Faces in Video
    facedetector_path = 'website/00models/openface_nn4.small2.v1.t7'
    rec_path = 'website/tendy/files/' + usd + '/' + channel + '/recognizer.pickle '
    le_path = 'website/tendy/files/' + usd + '/' + channel + '/le.pickle '
    conf = 0.7
    # load our serialized face detector from disk
    protoPath = "website/00models/deploy.prototxt"
    modelPath = "website/00models/caffe.caffemodel"
    detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

    # load our serialized face embedding model from disk
    embedder = cv2.dnn.readNetFromTorch(facedetector_path)
    # load the actual face recognition model along with the label encoder
    recognizer = pickle.loads(open(rec_path, "rb").read())
    le = pickle.loads(open(le_path, "rb").read())
    frame = imutils.resize(frame, width=600)
    (h, w) = frame.shape[:2]

    # construct a blob from the image
    imageBlob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)), 1.0, (300, 300),
        (104.0, 177.0, 123.0), swapRB=False, crop=False)

    # apply OpenCV's deep learning-based face detector to localize
    # faces in the input image
    detector.setInput(imageBlob)
    detections = detector.forward()

    names = []

    # loop over the detections
    for i in range(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with
        # the prediction
        confidence = detections[0, 0, i, 2]

        # filter out weak detections
        if confidence > conf:
            # compute the (x, y)-coordinates of the bounding box for
            # the face
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # extract the face ROI
            face = frame[startY:endY, startX:endX]
            (fH, fW) = face.shape[:2]

            # ensure the face width and height are sufficiently large
            if fW < 20 or fH < 20:
                continue

            # construct a blob for the face ROI, then pass the blob
            # through our face embedding model to obtain the 128-d
            # quantification of the face
            faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255,
                (96, 96), (0, 0, 0), swapRB=True, crop=False)
            embedder.setInput(faceBlob)
            vec = embedder.forward()

            # perform classification to recognize the face
            preds = recognizer.predict_proba(vec)[0]
            j = np.argmax(preds)
            proba = preds[j]
            name = le.classes_[j]

            # draw the bounding box of the face along with the
            # associated probability
            if proba > 0.5:
                names.append(name)
                text = "{}: {:.2f}%".format(name, proba * 100)
                y = startY - 10 if startY - 10 > 10 else startY + 10
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                    (0, 0, 255), 2)
                cv2.putText(frame, text, (startX, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
    return frame, names

 # -------------Face Recognition Code-----------------------------------END


 # -------------Face Recognition Model Training Code-----------------------------------START
def face_train(usd, channel): #---- Function to Train Face Recognition Model
    embeddings_file_path = 'website/tendy/files/' + usd + '/' + channel + '/embeddings.pickle'
    rec_path = 'website/tendy/files/' + usd + '/' + channel + '/recognizer.pickle'
    le_path = 'website/tendy/files/' + usd + '/' + channel + '/le.pickle'
    facedetector_path = 'website/00models/openface_nn4.small2.v1.t7'
    conf = 0.5
    dataset_path = 'website/tendy/files/' + usd + '/' + channel + '/dataset/dataset'

    # load our serialized face detector from disk
    print("[INFO] loading face detector...")
    protoPath = "website/00models/deploy.prototxt"
    modelPath = "website/00models/caffe.caffemodel"
    detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

    # load our serialized face embedding model from disk
    # print("[INFO] loading face recognizer...")
    embedder = cv2.dnn.readNetFromTorch(facedetector_path)

    # grab the paths to the input images in our dataset
    # print("[INFO] quantifying faces...")
    imagePaths = list(paths.list_images(dataset_path))

    # initialize our lists of extracted facial embeddings and
    # corresponding people names
    knownEmbeddings = []
    knownNames = []

    # initialize the total number of faces processed
    total = 0

    # loop over the image paths
    for (i, imagePath) in enumerate(imagePaths):
        # extract the person name from the image path
        # print("[INFO] processing image {}/{}".format(i + 1, len(imagePaths)))
        name = imagePath.split(os.path.sep)[-2]

        # load the image, resize it to have a width of 600 pixels (while
        # maintaining the aspect ratio), and then grab the image
        # dimensions
        image = cv2.imread(imagePath)
        image = imutils.resize(image, width=600)
        (h, w) = image.shape[:2]

        # construct a blob from the image
        imageBlob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0, (300, 300),
            (104.0, 177.0, 123.0), swapRB=False, crop=False)

        # apply OpenCV's deep learning-based face detector to localize
        # faces in the input image
        detector.setInput(imageBlob)
        detections = detector.forward()

        # ensure at least one face was found
        if len(detections) > 0:
            # we're making the assumption that each image has only ONE
            # face, so find the bounding box with the largest probability
            i = np.argmax(detections[0, 0, :, 2])
            confidence = detections[0, 0, i, 2]

            # ensure that the detection with the largest probability also
            # means our minimum probability test (thus helping filter out
            # weak detections)
            if confidence > conf:
                # compute the (x, y)-coordinates of the bounding box for
                # the face
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # extract the face ROI and grab the ROI dimensions
                face = image[startY:endY, startX:endX]
                (fH, fW) = face.shape[:2]

                # ensure the face width and height are sufficiently large
                if fW < 20 or fH < 20:
                    continue

                # construct a blob for the face ROI, then pass the blob
                # through our face embedding model to obtain the 128-d
                # quantification of the face
                faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255,
                    (96, 96), (0, 0, 0), swapRB=True, crop=False)
                embedder.setInput(faceBlob)
                vec = embedder.forward()

                # add the name of the person + corresponding face
                # embedding to their respective lists
                knownNames.append(name)
                knownEmbeddings.append(vec.flatten())
                total += 1

    print("[INFO] serializing {} encodings...".format(total))
    data = {"embeddings": knownEmbeddings, "names": knownNames}
    f = open(embeddings_file_path, "wb")
    f.write(pickle.dumps(data))
    f.close()

    # load the face embeddings
    # print("[INFO] loading face embeddings...")
    data = pickle.loads(open(embeddings_file_path, "rb").read())

    # encode the labels
    # print("[INFO] encoding labels...")
    le = LabelEncoder()
    labels = le.fit_transform(data["names"])

    # train the model used to accept the 128-d embeddings of the face and
    # then produce the actual face recognition
    print("[INFO] training face model...")
    recognizer = SVC(C=1.0, kernel="linear", probability=True)
    recognizer.fit(data["embeddings"], labels)

    # write the actual face recognition model to disk
    f = open(rec_path, "wb")
    f.write(pickle.dumps(recognizer))
    f.close()

    # write the label encoder to disk
    f = open(le_path, "wb")
    f.write(pickle.dumps(le))
    f.close()
    print("[INFO] Success training face model...")

    # Saving created files to firebase storage
    try:
        # Saving recognizer.pickle
        path = usd + "/tendy/" + channel + '/' + 'recognizer.pickle'
        rec_path = 'website/tendy/files/' + usd + '/' + channel + '/recognizer.pickle'
        storage.child(path).put(rec_path)
        print('Saved Recognizer.pickle to Storage')


        # Saving le.pickle
        path = usd + "/tendy/" + channel + '/' + 'le.pickle'
        le_path = 'website/tendy/files/' + usd + '/' + channel + '/le.pickle'
        storage.child(path).put(le_path)
        print('Saved Le.pickle to Storage')

    except Exception as e:
        print(str(e))

    # Delete the user directory in server space
    path = 'website/tendy/files/' + usd
    shutil.rmtree(path)

# -------------Face Recognition Model Training Code-----------------------------------END


# -------------Class to Process Each Channel's Video-----------------------------------START
class ChanFeed:
    def __init__(self, channel, url, fr, usd):
        self.channel = channel
        self.url = url
        self.usd = usd
        if fr == 'True':
            self.fr=True
        else:
            self.fr=False

    def feed(self): #---- Function to get video from the channel's urls and perform analysis
        if self.url == "0":
            stream = 0
        else:
            stream = self.url

        cap = cv2.VideoCapture(stream)
        # Get already existing names in a day in the database
        try:
            date = str(datetime.datetime.now())[:10]
            path = self.usd + '/tendy/channels/' + self.channel + '/' + date
            lsd = ref.child(path).get().val()
            name_list = lsd.split('-')
            print(name_list)
            path = self.usd + '/tendy/channels/' + self.channel
            all = ref.child(path).shallow().get().val()
            for i in all:
                if i not in ['name', 'url', 'fr', date]:
                    ref.child(path).child(i).remove()
            print(name_list)
        except Exception as e:
            print('Empty List')
            # print(str(e))
            name_list = []
            path = self.usd + '/tendy/channels/' + self.channel
            all = ref.child(path).shallow().get().val()
            for i in all:
                if i not in ['name', 'url', 'fr', date]:
                    ref.child(path).child(i).remove()

        while True:
            success, frame = cap.read()
            if not success:
                return 'website/console/static/img/novideo.jpg'
            else:
                save = frame
                if self.fr == True:
                    path = 'website/tendy/files/' + self.usd + '/' + self.channel + '/recognizer.pickle'
                    if os.path.exists(path) is True:
                        frame, names = face_recognition(frame, self.channel, self.usd)
                        if names:
                            for i in names:
                                print(F'Found {i}')
                                if i != 'unknown' and i not in name_list:
                                    name_list.append(i)
                                    listToStr = '-'.join([elem for elem in name_list])
                                    try:
                                        date = str(datetime.datetime.now())[:10]
                                        data = { date: listToStr }
                                        path = self.usd + '/tendy/channels/' + self.channel + '/'
                                        ref.child(path).update(data)
                                    except Exception as e:
                                        print('List Not Updated!')
                                        print(str(e))

                                    name = self.channel
                                    x = datetime.datetime.now()
                                    date = str(x)
                                    timestamp = date.translate({ord(c): "" for c in "!@#$%^&*()[]{};:-,./<>?\|`~=_+ "})
                                    alert_id = timestamp + '_' + i + '_' + name
                                    alert_id = alert_id.translate({ord(c): "_" for c in "!@#$%^&*()[]{};:-,./<>?\|`~=_+ "})
                                    time = date[11:16]
                                    date_only = date[:10]
                                    print('###  ' + alert_id + '  --- ')
                                    
                                    imgpath = 'temp/' + alert_id + '.jpg'
                                    cv2.imwrite(imgpath, save)
                                    print('Image saved to disk!!')

                                    try:
                                        path = self.usd + "/tendy/logs/" + name + '/' + alert_id + '.jpg'
                                        storage.child(path).put(imgpath)
                                        link = storage.child(path).get_url(None)

                                        data =  { 'channel': name, 'message': i, 'time': time,
                                        'date': date_only, 'link': link, 'alert_id': alert_id}
                                        path = self.usd + "/tendy/logs/" + date_only + '/' + alert_id + "/"
                                        ref.child(path).update(data)
                                        print('Success! Logged Alert!')
                                    except Exception as e:
                                        print('ERROR! : ' + str(e))
                                    os.remove(imgpath)
                                
                                else:
                                    pass


                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# -------------Class to Process Each Channel's Video-----------------------------------END
