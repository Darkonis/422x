'''
MIT License

Copyright (c) 2019 Arshdeep Bahga and Vijay Madisetti

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

#!flask/bin/python
from crypt import methods
import re
#from urllib import response
from flask import Flask, current_app, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os    
import time
import datetime

from itsdangerous import Serializer
import exifread
import json
import boto3  
import MySQLdb

app = Flask(__name__, static_url_path="")
app._static_folder = ''

UPLOAD_FOLDER = os.path.join(app.root_path,'static','media')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
BASE_URL="www.r4ndo22.net"
AWS_ACCESS_KEY=""
AWS_SECRET_KEY=""
REGION="us-east-2"
BUCKET_NAME="422photobucket"

app.secret_key=AWS_SECRET_KEY

##DB_HOSTNAME="mysql-db-instance.cm4jqnr18t4s.us-east-2.rds.amazonaws.com"
##DB_USERNAME = 'admin'
##DB_PASSWORD = 'adminpass'
##DB_NAME = 'photogallerydb'

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                         aws_secret_access_key=AWS_SECRET_KEY,
                         region_name=REGION)

photo = dynamodb.Table('photogallery')

### Helpers ###

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

def getExifData(path_name):
    f = open(path_name, 'rb')
    print f
    tags = exifread.process_file(f)
    print tags
    ExifData={}
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 
                       'Filename', 'EXIF MakerNote'):
            key="%s"%(tag)
            val="%s"%(tags[tag])
            ExifData[key]=val
    return ExifData

def s3uploading(filename, filenameWithPath):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_KEY)
                       
    bucket = BUCKET_NAME
    path_filename = "photos/" + filename
    print path_filename
    s3.upload_file(filenameWithPath, bucket, path_filename)  
    s3.put_object_acl(ACL='public-read', 
                Bucket=bucket, Key=path_filename)

    return "http://"+BUCKET_NAME+\
            ".s3-us-east-2.amazonaws.com/"+ path_filename 

## Creates and attaches a loginmanger to the web server
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

## Loads the user based on their id
@login_manager.user_loader
def load_user(user_id):
    try:
        return User(user_id)
    except:
        return None

## Defines athe user class and assigns relevant information
class User(UserMixin):
    def __init__(self, userid, username=None):
        self.dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                         aws_secret_access_key=AWS_SECRET_KEY,
                         region_name=REGION)
        self.table = self.dynamodb.Table('User')
        self.id = userid
        item = self.table.get_item(Key={'user_email': userid})
        if username:
            self.username = username
        else:
            item = self.table.get_item(Key={'user_email': userid})
            self.username = item['Item']['username']
            self.password_hash = item['Item']['password_hash']

    ## Compares the password hash when logging in
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

## Creates a new user, and returns False if unable to
def new_user(userid, username, password):
   # self.dynamodb = dynamodb
    table = dynamodb.Table("User")
    item = table.get_item(Key={'user_email':userid})
    if 'Item' in item:
        return False

    password_hash = generate_password_hash(password)

    table_item = {
        'user_email': userid,
        'username': username,
        'password_hash' : password_hash,
    }

    table.put_item(Item=table_item)
    return True


### Routes ###

#Homepage
@app.route('/', methods=['GET', 'POST'])
def home_page():
    response = photo.scan()  #Replace with all catagories and subcatagories

    items = response['Items']  #Break it up into catagories and subcatagories
    #print(items)

    ## Two different display options, probably a nested loop of some kind

    display = "display: block;"
    if not current_user:
        display = "display: none;"
    return render_template('index.html', photos=items, d=display)

#Logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/login')

#Adds photos to the database and site
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_photo():

    ## Change to ask the user what item they want to list

    # TODO User choose object
    
    ## Redirect to approptite page

    # TODO Redirect

    if request.method == 'POST':    
        uploadedFileURL=''
        file = request.files['imagefile']
        title = request.form['title']
        tags = request.form['tags']
        description = request.form['description']

        print title,tags,description
        if file and allowed_file(file.filename):
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            print filenameWithPath
            file.save(filenameWithPath)            
            uploadedFileURL = s3uploading(filename, filenameWithPath)
            ExifData=getExifData(filenameWithPath)
            print ExifData
            ts=time.time()
            timestamp = datetime.datetime.\
                        fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

            photo.put_item(
                Item={
                    "PhotoID": str(int(ts*1000)),
                    "CreationTime": timestamp,
                    "Title": title,
                    "Description": description,
                    "Tags": tags,
                    "URL": uploadedFileURL,
                    "UserID": current_user.id,
                    "ExifData": json.dumps(ExifData)
                }
            )

        return redirect('/')
    else:
        return render_template('form.html')

#Add Item page
@app.route('/add/<path:Item>', methods=['GET', 'POST'])
def add_item(Item):
    print(Item)

    ## When reaching page, display a number of options designated by the object
    ## Set values of different fields in the addItem.html, to hide or show the required fields

    # TODO set HTML fields

    ## GET data from HTML page on submit

    ## If missing fields, show error messages

    ## Add item to databases

    ##Redirect to home page

    return redirect('/')




#Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        if password == '' or username == '':
            ##Stop here
            print("No password")
            return redirect('/login')

        user = User(userid)
        if user.verify_password(password):
            login_user(user)
            return redirect('/')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

#Register page
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        userid = request.form["email"]
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm password']

        ## May include more information like phone number or city. Information pending on that.

        if password == '' or confirm == '' or username == '':
            print("Missing field")
            return render_template('register.html')

        if password != confirm:
            ##Error handling
            print("Error")
            return render_template('register.html')
        else:
            if not new_user(userid, username, password):
                render_template('register.html')
            user = User(userid, username)
            return redirect('/login')
    else:
        return render_template('register.html')

#View photo
@app.route('/<int:photoID>', methods=['GET'])
def view_photo(photoID):    

    ##Gut to display item
    
    response = photo.query(
            KeyConditionExpression=Key('PhotoID').eq(str(photoID))
    )
    items = response['Items']
    tags=items[0]['Tags'].split(',')
    exifdata=json.loads(items[0]['ExifData']) 
    return render_template('photodetail.html', photo=items[0], 
                            tags=tags, exifdata=exifdata)

#Search for photos
@app.route('/search', methods=['GET'])
def search_page():
    query = request.args.get('query', None)    

    #Adjust to fit new data.

    response= photo.scan(
        FilterExpression=Attr('Title').contains(str(query)) |
                        Attr('Description').contains(str(query)) |
                        Attr('Tags').contains(str(query))
    )
    print(response)
    items = response['Items']
    return render_template('search.html', photos=items, 
                            searchquery=query)

# View Catagory
@app.route('/<path:Catagory>', methods=['GET'])
def view_Catagory(Catagory):
    print(Catagory)
    ## Show all subcatagories
    ## Show items in catagory, descending time order

    ##return render_template('catagory.html'...)
    return 0

# View Subcatagory
@app.route('/<path:Catagory>/<path:Subcatagory', methods=['GET'])
def view_Subcatagory(Catagory, Subcatagory):
    print(Catagory)
    print(Subcatagory)

    ##Show items in subcatagory, descending time order
    
    ##return render_template('subcatagory.html'...)
    return 0

if __name__ == '__main__':
    app.run(debug=True, host="172.31.28.76", port=5001)
