import os
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.core.files.storage import FileSystemStorage
import dropbox
from django.conf import settings
from home.models import Setting
import requests
import json
from pygdrive3 import service
import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer

# Dropbox file upload
class TransferData:
    def __init__(self, access_token):
        self.access_token = access_token

    def upload_file(self, file_from, file_to):
        # Create Dropbox
        dbx = dropbox.Dropbox(self.access_token)
        with open(file_from, 'rb') as f:
            try:
                # File upload to the dropbox
                dbx.files_upload(f.read(), file_to)
            except Exception as e:
                print(str(e))
        os.remove(file_from)
# Create your views here.
def index(request):
    response = redirect('/home/')
    return response

def home(request):
    return render(request, 'home.html')

def setting(request):
    setting = Setting.objects.first()
    return render(request, 'setting.html', {'setting': setting})

def savesetting(request):
    success = False
    setting = Setting.objects.first()
    if request.method == 'POST':
        access_token = request.POST['dropbox']
        g_access_token = request.POST['g_access_token']
        g_projectId = request.POST['g_projectId']

        o_tenent = request.POST['o_tenent']
        o_client = request.POST['o_client']
        o_security = request.POST['o_security']
        Setting.objects.filter(pk=setting.pk).update(dropbox=access_token, google_token=g_access_token,
                                                     google_projectid=g_projectId, one_tenant=o_tenent, one_client=o_client, one_security=o_security)

        setting = Setting.objects.first()
        success = True
    if request.method == 'GET':
        setting = Setting.objects.first()
    return render(request, 'setting.html', {'success': success, 'setting': setting})


def upload(request):
    if request.method == 'POST':
        message = 'Files are uploaded successfully to the '
        state = False
        try:
            localdriver = 'off'
            dropboxdriver = 'off'
            googledriver = 'off'
            onedriver = 'off'
            # Local Driver
            if 'localdriver' not in request.POST:
                localdriver = 'off'
            else:
                localdriver = request.POST['localdriver']
            # Dropbox Driver
            if 'dropboxdriver' not in request.POST:
                dropboxdriver = 'off'
            else:
                dropboxdriver = request.POST['dropboxdriver']
            # google Driver
            if 'googledriver' not in request.POST:
                googledriver = 'off'
            else:
                googledriver = request.POST['googledriver']

            # One Driver
            if 'onedriver' not in request.POST:
                onedriver = 'off'
            else:
                onedriver = request.POST['onedriver']

            # Upload logic to the local Driver
            if localdriver == 'on':
                uploadTolocal(request.FILES)
                message = message + 'local driver. '
                state = True
            # Upload logic to the local Driver
            if dropboxdriver == 'on':
                uploadTodropbox(request.FILES)
                message = message + 'dropbox driver. '
                state = True
            if googledriver == 'on':
                result = uploadTogoogledriver(request.FILES)
                if result == True:
                    message = message + 'google driver. '
                    state = True
                else:
                    message = "Fail"
            if onedriver == 'on':
                uploadToonedriver(request.FILES)
                message = message + 'one driver. '
                state = True

        except:
            message = 'Upload failed!'
        return render(request, 'home.html', {'success': state, 'message': message})
    if request.method == 'GET':
        response = redirect('/home/')
        return response

# upload the files to the local Driver
def uploadTolocal(files):
    files = files.getlist('files')
    for file in files:
        # create File storage
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)


def uploadTodropbox(files):
    files = files.getlist('files')
    # get the access_token from the database
    setting = Setting.objects.first()
    access_token = setting.dropbox
    # Create Transferdata
    transferData = TransferData(access_token)
    for file in files:
        file_to = '/dropbox-driver/' + file.name #The full path to upload the file to, including the file name
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_from = os.path.join(settings.MEDIA_ROOT, filename)
        transferData.upload_file(file_from, file_to)

def uploadTogoogledriver(files):
    files = files.getlist('files')
    setting = Setting.objects.first()
    access_token = setting.google_token
    parentId = setting.google_projectid
    print(access_token)
    # access_token = "ya29.a0AfH6SMDtJ0np6PAiqRJD1W5XJTF_6GIxPHyxravBtGMAesdXvE9pTPRuGBaB2nwmNTW95LQwSY73V5YItjmNbV74V5-elx3aqdOz5sZfwpv_iRCZP0SHRQA3_6an2cseZDp9cu5cqskUJVi9T8z0Cz4tZ8AQo9dOYfo"
    # parentId = "quickstart-1593747205709"
    headers = {
        "Authorization": "Bearer " + access_token}
    for file in files:
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        # file_metadata = {
        #     'name': 'google-driver',
        #     'mimeType': 'application/vnd.google-apps.folder'
        # }
        # response = requests.post( 'https://www.googleapis.com/drive/v3/files?uploadType=multipart', headers = headers, params = file_metadata)
        para = {
            "name": filename,
            "parents": parentId
        }
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': ('image/jpeg', open(os.path.join(settings.MEDIA_ROOT, filename), "rb"))
        }
        r = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers,
            files=files
        )
        print(r.text)
        if r.status_code == 200 or r.status_code == 201:
            os.remove(filename)
            return True
        else:
            return False


def uploadToonedriver(files):
    files = files.getlist('files')
    setting = Setting.objects.first()
    tenentid = setting.one_tenant
    clientid = setting.one_client
    client_secret = setting.one_client
    data = {'grant_type': "client_credentials",
            'resource': "https://graph.microsoft.com",
            'client_id': clientid,
            'client_secret': client_secret,
            'redirect_url': "http://localhost:8000"}

    URL = "https://login.windows.net/" + tenentid + "/oauth2/token?api-version=1.0"
    r = requests.post(url=URL, data=data)
    j = json.loads(r.text)
    TOKEN = j["access_token"]
    # URL = "https://graph.microsoft.com/v1.0/users/72d60c35-5c41-4c62-bd8c-dc58561188ad/drive/root:/fotos/HouseHistory"
    URL = "https://graph.microsoft.com/v1.0/" + tenentid + "/drive/drive/root"
    headers = {'Authorization': "Bearer " + TOKEN}
    r = requests.get(URL, headers=headers)
    j = json.loads(r.text)
    for file in files:
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        fileHandle = open(os.path.join(settings.MEDIA_ROOT, filename))
        r = requests.put(URL + "/" + filename + ":/content", data=fileHandle, headers=headers)
        fileHandle.close()
        if r.status_code == 200 or r.status_code == 201:
            print("succeeded, removing original file...")
    # r = requests.put(URL + "/" + filename + ":/content", data=fileHandle, headers=headers)
    # print(r.text)
    # try:
    #     pass
    #     # response = requests.put(url)
    #     # print(response.text)
    # except Exception as e:
    #     print(e)
