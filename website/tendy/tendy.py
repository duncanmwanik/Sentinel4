from flask import Flask, render_template, url_for, redirect, request, Response, Blueprint
import pyrebase
from website.tendy.tendyfunctions import *
import shutil
import os
import zipfile

tendy = Blueprint('tendy', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='tendy.static')

# Realtime Database Configuration
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
ref = firebase.database()
storage = firebase.storage()


def makeOneTrue(one): # --------- Converting "1" to Boolean
    if one == '1':
        one = True
    return one

@tendy.route('/video_feed_tendy/<channel>/<path:url>/<fr>/<usd>') # --- Get Video For Each Channel
def video_feed(channel, url, fr, usd):
    name = ChanFeed(channel, url, fr, usd) # --- Create a Class ChanFeed for each Channel
    return Response(name.feed(), mimetype='multipart/x-mixed-replace; boundary=frame')


@tendy.route("/tendy/<user_id>",methods=['POST', 'GET']) # --- Console Home Route
def tendy_page(user_id):
    usd = user_id

    # Get channel details and the username
    channel_path = "/" + usd +"/tendy/channels/"
    username_path = "/" + usd +"/details/"
    try:
        channels = ref.child(channel_path).get().val()  # --- Get the User Channels List
        username = ref.child(username_path).child('username').get().val() # --- Get the Username

        mainlist = [] # --- List of Channels to be passed to console page render
        if channels != None:
            for key,channel in channels.items():
                diction = {'name' : channel['name'], 'url' : channel['url'], 'fr' : channel['fr'], 'usd': usd}
                mainlist.append(diction)
        else:
            print('Found Zero Channels!!')

    except Exception as e:
        print(str(e))


    # Download all user files in the server space
    try:
        channels = ref.child(channel_path).get().val()  # --- Get the channel List
        if channels != None:
            for key,channel in channels.items():
                # Create necessary directories for each channel [key]
                try:
                    user_directory = 'website/tendy/files/' + usd + '/' + key
                    os.makedirs(user_directory)
                except:
                    print('Directory Already Exists!!')
                    
                path1 = usd + "/tendy/" + key + '/' + 'recognizer.pickle'
                path2 = usd + "/tendy/" + key + '/' + 'le.pickle'
                rec_path = 'website/tendy/files/' + usd + '/' + key + '/recognizer.pickle'
                le_path = 'website/tendy/files/' + usd + '/' + key + '/le.pickle'
                try:
                    storage.child(path1).download(rec_path) 
                    storage.child(path2).download(le_path)
                except:
                    print('No Files ...')
        else:
            print('No channel data ...')

    except Exception as e:
        print(str(e))

    
    return render_template('tendy.html', mainlist=mainlist, usd=usd)


@tendy.route('/add_channel_tendy',methods=['POST', 'GET']) # --------- ADDING A CHANNEL
def add_channel():
    if request.method == 'POST':
        usd = request.form['channel-user-id']
        name = request.form['channel-name']
        url = request.form['channel-url']
        try:
            fr = request.form['fr-checkbox']
            fr = makeOneTrue(fr)
        except:
            fr = False

        print( name + '-' + url)
        data =  { 'name': name, 'url': url, 'fr': fr}

        try:
            # Add channel to RDB
            path = "/" + usd + "/tendy/channels/" + name + "/"
            ref.child(path).update(data)
            print("SUCCESS! Added New Channel!")
        except:
            print("ERROR!")

        return redirect(url_for('tendy.tendy_page', user_id=usd))

@tendy.route('/update_channel_tendy',methods=['POST', 'GET']) # --------- ADDING A CHANNEL
def update_channel():
    if request.method == 'POST':
        usd = request.form['user-id']
        oldname = request.form['channel-old-name-edit']
        name = request.form['channel-name-edit']
        url = request.form['channel-url-edit']
        try:
            fr = request.form['fr-checkbox-edit']
            fr = makeOneTrue(fr)
        except:
            fr = False

        print( name + '-' + url)
        data =  { 'name': name, 'url': url, 'fr': fr}

        try:
            # Update channel to RDB
            if oldname == name:
                path = "/" + usd + "/tendy/channels/" + oldname + "/"
                ref.child(path).update(data)
            
            # Delete old channel and create new one in RDB
            else:
                path = "/" + usd + "/tendy/channels/" + name + "/"
                ref.child(path).update(data)
                path = "/" + usd + "/tendy/channels/"
                ref.child(path).child(oldname).remove()

        except:
            print("ERROR UPDATING!")

        return redirect(url_for('tendy.tendy_page', user_id=usd))


@tendy.route('/delete_channel_tendy',methods=['GET', 'POST']) # --------- DELETING A CHANNEL
def delete_channel():

    if request.method == 'POST':
        usd = request.form['delete-user-id']
        name = request.form['delete-name']
        print('*************************')
        print(name)
        print('******************DELETING')

        while True:
            try:
                # Deleting images and files from storage
                prefix = usd + '/tendy/logs/' + name
                files = storage.list_files(prefix=prefix)
                for file in files:
                    url = storage.child(file.name).get_url(None)
                    fname = url.split("%2F")[-1].split('?')[0]
                    channel = fname.split('.')[0].split('_')[-1]
                    print(fname)
                    if channel==name:
                        path3 = usd + '/tendy/logs/' + name + '/' + fname
                        storage.delete(path3)
                print('Images deleted successfully!')
            except Exception as e:
                print(str(e))
                print('Error Deleting Images!')
                break

            try:
                # Delete FaceRecognition models
                le_path = usd + '/tendy/' + name + '/le.pickle'
                rec_path = usd + '/tendy/' + name + '/recognizer.pickle'
                storage.delete(le_path)
                storage.delete(rec_path)
            except Exception as e:
                print('Error Deleting Face Models')
                
            try:
                # Get logs to delete
                logs_path = "/" + usd +"/tendy/logs/"
                logs = ref.child(logs_path).get().val()
                for date, lgs in logs.items():
                    for alert_id, alert in lgs.items():
                        if alert['channel'] == name:
                            path = "/" + usd + "/tendy/logs/" + date + '/'
                            ref.child(path).child(alert_id).remove()
                print('Logs deleted successfully!')
            except Exception as e:
                print('Error Deleting Logs!')

            try:
                # Remove channel completely
                path = "/" + usd + "/tendy/channels/"
                ref.child(path).child(name).remove()
            except Exception as e:
                print('Error Deleting Channel!')
                break

            print('SUCCESS Deleting Channel! : ' + name)
            return redirect(url_for('tendy.tendy_page', user_id=usd))
     
        print('Error Deleting Channel!')
        return ('', 204)


ALLOWED_EXTENSIONS = set(['zip']) #--- Only ZIP Files Allowed
def allowed_file(filename): #---Function To Check Only For ZIP Files
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@tendy.route('/train_face_tendy', methods=['GET', 'POST']) #---Route to Train the Face Recognition Model
def train_face_tendy():
    if request.method == 'POST':
        usd = request.form['id-tendy']
        channel = request.form['channel-train']
        file = request.files['file']
        print('#########' + usd + '----' + channel)
        if file.filename != '':
            if file and allowed_file(file.filename):
                UPLOAD_FOLDER = 'website/tendy/files/' + usd + '/' + channel + '/dataset'
                FOLDER = 'website/tendy/files/' + usd + '/' + channel
                try:
                    shutil.rmtree(FOLDER) # Remove existing user directories in the server
                except Exception as e:
                    print(str(e))
                os.makedirs(UPLOAD_FOLDER) # Create new user dir in the server
                # filename = secure_filename(file.filename) #--- WerkZeugeeeeeeeeeeer :)
                filename = 'dataset.zip'
                path = UPLOAD_FOLDER + '/' + filename
                file.save(path) #--- Save the Uploaded Zip File

                try:
                    zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r') #--- Unzip the Uploaded File
                    zip_ref.extractall(UPLOAD_FOLDER)
                    zip_ref.close()
                    
                    # Create necessary files in the user dire in the server for training face rec model
                    shutil.copyfile('files/face/embeddings.pickle', 'website/tendy/files/' + usd + '/' + channel + '/embeddings.pickle')
                    shutil.copyfile('files/face/recognizer.pickle', 'website/tendy/files/' + usd + '/' + channel + '/recognizer.pickle')
                    shutil.copyfile('files/face/le.pickle', 'website/tendy/files/' + usd + '/' + channel + '/le.pickle')
                    face_train(usd, channel) #--- Train the Model
                except Exception as e:
                    print('Failed To Train Model! \n' + str(e))

                return redirect(url_for('tendy.tendy_page', user_id=usd))

            else:
                print('Bad File!') # Refuse all files but zip

        return ('', 204) #--- Do Nothing if File is Bad
        