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
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
import os    
import time
import datetime
import exifread
import json
import boto3  
import MySQLdb

app = Flask(__name__, static_url_path="")

UPLOAD_FOLDER = os.path.join(app.root_path,'static','media')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
BASE_URL="www.r4ndo22.net"
AWS_ACCESS_KEY="AKIAVCQ6IU4HCDJMHLWV"
AWS_SECRET_KEY="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"
REGION="us-east-2"
BUCKET_NAME="422photobucket"
##DB_HOSTNAME="mysql-db-instance.cm4jqnr18t4s.us-east-2.rds.amazonaws.com"
##DB_USERNAME = 'admin'
##DB_PASSWORD = 'adminpass'
##DB_NAME = 'photogallerydb'
CUR_USER = ''

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                          aws_secret_access_key=AWS_SECRET,
                          region_name=REGION)

user = dynamodb.Table('User')
photo = dynamodb.Table('photogallery')


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
    tags = exifread.process_file(f)
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
            ".s3-website-us-east-2.amazonaws.com/"+ path_filename 



@app.route('/', methods=['GET', 'POST'])
def home_page():
    response = photo.scan()

    items = response['Items']
    print(items)

    display = "display: block;"
    if CUR_USER == '':
        display = "display: none;"
    return render_template('index.html', photos=items, d=display)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    global CUR_USER
    CUR_USER = ''
    return redirect('/')

@app.route('/add', methods=['GET', 'POST'])
def add_photo():
    if CUR_USER != '':
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
                        #"UserID": userID
                        "ExifData": json.dumps(ExifData)
                    }
                )

            return redirect('/')
        else:
            return render_template('form.html')
    else:
        return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    global CUR_USER
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if password == '' or username == '':
            ##Stop here
            print("No password")
            return

        success = False

        response=user.scan(FilterExpression=Attr('username').eq(str(username)))
        item = response['Items']

        ##Find what elements are obtained and how to reference them
        if item == password:
            success = True
        
        if not success:
            print("Username or Password incorrect")
            return
        
        print("debug message #4")
        ## If no errors set CUR_USER to username
        CUR_USER = username
        print(CUR_USER)
        return redirect('/')
    elif CUR_USER != '':
        return redirect('/')
    else:
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm password']

        if password == '' or confirm == '' or username == '':
            print("Missing field")
            return

        if password != confirm:
            ##Error handling
            print("Error")
            return
        else:
            results = user.scan(FilterExpression=Attr('username').eq(str(username)))
            item = results['Items']
            if item :
                ## Username exists
                print("Registration error")
                return render_template('register.html')

            user.put_item(
                Item={
                    "UserID": 11, ##Setup auto assignment
                    "Username": username,
                    "Password": password, ##Maybe make it secure
                }
            )
            return redirect('/login')
    elif CUR_USER != '':
        return redirect('/')
    else:
        return render_template('register.html')



@app.route('/<int:photoID>', methods=['GET'])
def view_photo(photoID):    
    response = photo.scan(
        FilterExpression=Attr('PhotoID').eq(str(photoID))
    )

    items = response['Items']
    print(items[0])
    tags=items[0]['Tags'].split(',')
    exifdata=items[0]['ExifData']
    
    return render_template('photodetail.html', photo=items[0], 
                            tags=tags, exifdata=exifdata)

@app.route('/search', methods=['GET'])
def search_page():
    query = request.args.get('query', None)    

    response= photo.scan(
        FilterExpression=Attr('Title').contains(str(query)) |
                        Attr('Description').contains(str(query)) |
                        Attr('Tags').contains(str(query))
    )
    items = response['Items']
    return render_template('search.html', photos=items, 
                            searchquery=query)

if __name__ == '__main__':
    app.run(debug=True, host="172.31.28.76", port=5001)
