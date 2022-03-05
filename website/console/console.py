from flask import Flask, render_template, url_for, redirect, request, Response, Blueprint, flash
from werkzeug.utils import secure_filename

from website.console.consolefunctions import *
import os
import zipfile

import pyrebase #------ For Firebase functions
from getpass import getpass 


console = Blueprint('console',__name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='console.static')


firebase = pyrebase.initialize_app(firebaseconfig) #------ Initializing FIrebase Credentials
authorize = firebase.auth()
storage = firebase.storage()
ref = firebase.database() #------ Firebase Reference for Realtime Database


def makeOneTrue(one): # --------- Converting "1" to Boolean for Form CheckBoxes
    if one == '1':
        one = True
    return one

demoMax = 0

@console.route('/video_feed/<name>/<path:url>/<ar>/<fr>/<pd>/<usd>') # --- Get Video For Each Channel
def video_feed(name, url, ar, fr, pd, usd):
    name = ChanFeed(name, url, ar, fr, pd, usd) # --- Create a Class ChanFeed for each Channel
    return Response(name.feed(), mimetype='multipart/x-mixed-replace; boundary=frame')


@console.route("/consol/<user_id>",methods=['POST', 'GET']) # --- Console Home Route
def console_page(user_id):
    usd = user_id

    # Get channel details and the username
    channel_path = "/" + usd +"/console/channels/"
    try:
        channels = ref.child(channel_path).get().val()  # --- Get the User Channels List

        mainlist = [0] # --- List of Channels to be passed to console page render
        if channels != None:
            mainlist.clear()
            for key,channel in channels.items():
                diction = {'name' : channel['name'], 'url' : channel['url'], 
                    'ar' : channel['ar'], 'fr' : channel['fr'], 'pd' : channel['pd'], 'usd': user_id}
                mainlist.append(diction)
                print(channel['url'])
        else:
            print('Found Zero Channels!!')

    except Exception as e:
        print(str(e))

    # Get neccessary files for face recognition if available
    try:
        # Create necessary directories for each channel [key]
        try:
            user_directory = 'website/console/files/' + usd
            os.makedirs(user_directory)
        except:
            pass

        path1 = usd + "/console/recognizer.pickle"
        path2 = usd + "/console/le.pickle"
        rec_path = 'website/console/files/' + usd + '/recognizer.pickle'
        le_path = 'website/console/files/' + usd + '/le.pickle'
        storage.child(path1).download(rec_path) # Download file from Firebase Storage
        storage.child(path2).download(le_path)
    except:
        print('Failed to Download User Files')
    
    return render_template('console.html', mainlist=mainlist, usd=usd)

    
@console.route('/add_channel',methods=['POST', 'GET']) # --- Route to Add a New Channel
def add_channel():
    if request.method == 'POST':
        usd = request.form['channel-user-id']
        name = request.form['channel-name']
        url = request.form['channel-url']
        try:
            ar = request.form['ar-checkbox']
            ar = makeOneTrue(ar)
        except:
            ar = False
        try:
            fr = request.form['fr-checkbox']
            fr = makeOneTrue(fr)
        except:
            fr = False
        try:
            pd = request.form['pd-checkbox']
            pd = makeOneTrue(pd)
        except:
            pd = False

        data =  { 'name': name, 'url': url, 'ar': ar, 'fr': fr, 'pd': pd}

        try:
            path = "/" + usd + "/console/channels/" + name + "/"
            ref.child(path).update(data) # --- Add the New Channel
            print("SUCCESS! Added New Channel! : " + name)
            return redirect(url_for('console.console_page', user_id=usd))
        except Exception as e:
            print("ERROR Adding Channel! : " + name + ':' + str(e))
            return ('', 204)
            

@console.route('/update_channel',methods=['POST', 'GET']) # --- Route to Update a Channel
def update_channel():
    if request.method == 'POST':
        usd = request.form['user-id']
        oldname = request.form['channel-old-name-edit']
        name = request.form['channel-name-edit']
        url = request.form['channel-url-edit']
        try:
            ar = request.form['ar-checkbox-edit']
            ar = makeOneTrue(ar)
        except:
            ar = False
        try:
            fr = request.form['fr-checkbox-edit']
            fr = makeOneTrue(fr)
        except:
            fr = False
        try:
            pd = request.form['pd-checkbox-edit']
            pd = makeOneTrue(pd)
        except:
            pd = False

        print( name + '-' + url + '-' + str(ar) + '-' + str(fr) + '-' + str(pd))
        data =  { 'name': name, 'url': url, 'ar': ar, 'fr': fr, 'pd': pd}

        try:
            if oldname == name:
                path = "/" + usd + "/console/channels/" + oldname + "/"
                ref.child(path).update(data) # --- Update channel if name hasn't been changed
            else:
                path = "/" + usd + "/console/channels/" + name + "/"
                ref.child(path).update(data) # --- Add the New Named Channel
                path = "/" + usd + "/console/channels/"
                ref.child(path).child(oldname).remove() # --- Remove the Old Channel
            return redirect(url_for('console.console_page', user_id=usd))

        except Exception as e:
            print("ERROR Updating Channel!\n:" + str(e))
            return ('', 204)

        

@console.route('/delete_channel',methods=['GET', 'POST']) # --- Route to Delete a Channel
def delete_channel():

    if request.method == 'POST':
        usd = request.form['delete-user-id']
        name = request.form['delete-name']

        while True:
            try:
                prefix = usd + '/console/logs/' + name
                files = storage.list_files(prefix=prefix)
                for file in files:
                    url = storage.child(file.name).get_url(None)
                    fname = url.split("%2F")[-1].split('?')[0]
                    channel = fname.split('.')[0].split('_')[-1]
                    print(fname)
                    if channel==name:
                        path3 = usd + '/console/logs/' + name + '/' + fname
                        storage.delete(path3)
                print('Images deleted successfully!')
            except Exception as e:
                print(str(e))
                print('Error Deleting Images!')
                # break
            
            try:
                # Get logs to delete
                logs_path = "/" + usd +"/console/logs/"
                logs = ref.child(logs_path).get().val()
                for date, lgs in logs.items():
                    for alert_id, alert in lgs.items():
                        if alert['channel'] == name:
                            path = "/" + usd + "/console/logs/" + date + '/'
                            ref.child(path).child(alert_id).remove()
                print('Logs deleted successfully!')
            except Exception as e:
                print(str(e))
                print('Error Deleting Logs!')
                
            try:
                path = "/" + usd + "/console/channels/"
                ref.child(path).child(name).remove()
            except Exception as e:
                print(str(e))
                print('Error Deleting Channel!')
                break
                
            print('SUCCESS Deleting Channel! : ' + name)
            return redirect(url_for('console.console_page', user_id=usd))

        print('ERROR Deleting Channel!\n:' + str(e))
        return ('', 204)


ALLOWED_EXTENSIONS = set(['zip']) #--- Only ZIP Files Allowed
def allowed_file(filename): #---Function To Check Only For ZIP Files
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@console.route('/train_face_console', methods=['GET', 'POST']) #---Route to Train the Face Recognition Model
def train_face_console():
    if request.method == 'POST':
        usd = request.form['usd-console']
        file = request.files['file']
        if file.filename != '':
            if file and allowed_file(file.filename):
                UPLOAD_FOLDER = 'website/console/files/' + usd + '/dataset'
                FOLDER = 'website/console/files/' + usd
                try:
                    shutil.rmtree(FOLDER) # Remove existing user directories in the server
                except Exception as e:
                    print(str(e))

                os.makedirs(UPLOAD_FOLDER) # Create new user dir in the server
                # filename = secure_filename(file.filename) #--- WerkZeugeeeeeeeeeeer :)
                filename = 'dataset.zip'
                file.save(os.path.join(UPLOAD_FOLDER, filename)) #--- Save the Uploaded Zip File

                try:
                    zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r') #--- Unzip the Uploaded File
                    zip_ref.extractall(UPLOAD_FOLDER)
                    zip_ref.close()

                    # Create necessary files in the user dire in the server for training face rec model
                    shutil.copyfile('files/face/embeddings.pickle', 'website/console/files/' + usd + '/embeddings.pickle')
                    shutil.copyfile('files/face/recognizer.pickle', 'website/console/files/' + usd + '/recognizer.pickle')
                    shutil.copyfile('files/face/le.pickle', 'website/console/files/' + usd + '/le.pickle')

                    face_train(usd) #--- Train the Model
                except Exception as e:
                    print('Failed To Train Model! \n' + str(e))

                return redirect(url_for('console.console_page', user_id=usd))

            else:
                print('Bad File!') # Refuse all files but zip

        return ('', 204) #--- Do Nothing if File is Bad
        