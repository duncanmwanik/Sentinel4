from flask import Flask, render_template, url_for, redirect, request, Response, Blueprint, flash
import pyrebase
from website.counter.counter_functions import *


counter = Blueprint('counter', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='counter.static')

# ----------------------- Initializing Firebase Functions
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

# ------------------------ Initializing Firebase Functions


def makeOneTrue(one): # --------- Converting "1" to Boolean
    if one == '1':
        one = True
    return one

@counter.route('/video_feed_counter/<channel>/<path:url>/<cc>/<usd>') # --- Get Video For Each Channel
def video_feed(channel, url, cc, usd):
    name = ChanFeed(channel, url, cc, usd) # --- Create a Class ChanFeed for each Channel
    return Response(name.feed(), mimetype='multipart/x-mixed-replace; boundary=frame')


@counter.route("/counter/<user_id>",methods=['POST', 'GET']) # --- Console Home Route
def counter_page(user_id):
    usd = user_id

    # Get channel details and the username
    channel_path = "/" + usd +"/counter/channels/"
    username_path = "/" + usd +"/details/"
    try:
        channels = ref.child(channel_path).get().val()  # --- Get the User Channels List
        username = ref.child(username_path).child('username').get().val() # --- Get the Username

        mainlist = [] # --- List of Channels to be passed to console page render
        if channels != None:
            for key,channel in channels.items():
                diction = {'name' : channel['name'], 'url' : channel['url'], 'cc' : channel['cc'], 'usd': usd}
                mainlist.append(diction)
        else:
            print('Found Zero Channels!!')

    except Exception as e:
        print(str(e))


    return render_template('counter.html', mainlist=mainlist, usd=usd)


@counter.route('/add_channel_counter',methods=['POST', 'GET']) # --------- ADDING A CHANNEL
def add_channel():
    if request.method == 'POST':
        usd = request.form['channel-user-id']
        name = request.form['channel-name']
        url = request.form['channel-url']
        try:
            cc = request.form['cc-checkbox']
            cc = makeOneTrue(cc)
        except:
            cc = False

        print( name + '-' + url + '-' + str(cc))
        data =  { 'name': name, 'url': url, 'cc': cc}

        try:
            # Add channel to RDB
            path = "/" + usd + "/counter/channels/" + name + "/"
            ref.child(path).update(data)
            print("SUCCESS! Added New Channel!")
        except:
            print("ERROR!")

        return redirect(url_for('counter.counter_page', user_id=usd))

@counter.route('/update_channel_counter',methods=['POST', 'GET']) # --------- ADDING A CHANNEL
def update_channel():
    if request.method == 'POST':
        usd = request.form['user-id']
        oldname = request.form['channel-old-name-edit']
        name = request.form['channel-name-edit']
        url = request.form['channel-url-edit']
        try:
            cc = request.form['cc-checkbox-edit']
            cc = makeOneTrue(cc)
        except:
            cc = False

        print( name + '-' + url)
        data =  { 'name': name, 'url': url, 'cc': cc}

        try:
            # Update channel to RDB
            if oldname == name:
                path = "/" + usd + "/counter/channels/" + oldname + "/"
                ref.child(path).update(data)
            
            # Delete old channel and create new one in RDB
            else:
                path = "/" + usd + "/counter/channels/" + name + "/"
                ref.child(path).update(data)
                path = "/" + usd + "/counter/channels/"
                ref.child(path).child(oldname).remove()
    
        except:
            print("ERROR UPDATING!")

        return redirect(url_for('counter.counter_page', user_id=usd))


@counter.route('/delete_channel_counter',methods=['GET', 'POST']) # --------- DELETING A CHANNEL
def delete_channel():

    if request.method == 'POST':
        usd = request.form['delete-user-id']
        name = request.form['delete-name']
        print('*************************')
        print(name)
        print('******************DELETED')
        while True:
            try:
                # Get logs to delete
                logs_path = "/" + usd +"/counter/logs/"
                logs = ref.child(logs_path).get().val()
                for date, lgs in logs.items():
                    for alert_id, alert in lgs.items():
                        if alert_id == name:
                            path = "/" + usd + "/counter/logs/" + date + '/'
                            ref.child(path).child(alert_id).remove()
                print('Logs deleted successfully!')
            except Exception as e:
                print(str(e))
                print('Error Deleting Logs!')
                break
            
            try:
                path = "/" + usd + "/counter/channels/"
                ref.child(path).child(name).remove()
            except Exception as e:
                print(str(e))
                print('Error Deleting Channel!')
                break
            
            return redirect(url_for('counter.counter_page', user_id=usd))

        print('Error Deleting Channel!')
        return ('', 204)

@counter.route('/flash_test') # --------- DELETING A CHANNEL
def flash_test():
    flash('This Fucking Works!')
    print('Shit Worked!')
    return ('', 204)