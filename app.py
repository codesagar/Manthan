import os
from flask import Flask, request, redirect, url_for ,Response, render_template, jsonify
from werkzeug import secure_filename
from azure.storage.blob import BlockBlobService, PublicAccess
import string
import random
import requests, json, csv
import unicodedata
from pymongo import MongoClient
import JSONEncoder
import ast
import re
from json2html import *
from bson import json_util, ObjectId
from json import dumps, loads
from datetime import datetime
import csv

app = Flask(__name__, instance_relative_config=True)

app.config.from_pyfile('config.py')

storage_key = app.config['STORAGE_KEY']
hp_api_key = app.config['HP_API_KEY']


blob_service = BlockBlobService(account_name='projectmanthan', account_key= storage_key)
blob_service.create_container('reports', public_access='container')


ALLOWED_EXTENSIONS = set(['jpeg','png',"jpg"])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if request.form['submit'] == 'Upload Report':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                fileextension = filename.rsplit('.',1)[1]
                Randomfilename = id_generator()
                filename = Randomfilename + '.' + fileextension
                #blob_service=initilizeAzure()
                try:
                    blob_service.create_blob_from_stream(
                    'reports',
                    filename,
                    file,
                    )
                except Exception:
                    print 'Exception=' , Exception 
                    pass
                #file.save(os.path.join(app.config['UPLOAD_FOLDER'], Randomfilename + '.' + fileextension))
                ref =  'http://projectmanthan.blob.core.windows.net/reports/' + filename
                apikey = hp_api_key
                url = 'https://api.havenondemand.com/1/api/sync/ocrdocument/v1?url=' + ref + '&apikey='+apikey
                r = requests.get(url)
                rtext=r.text
                rtext=unicodedata.normalize('NFKD', rtext).encode('ascii','ignore')
                text=str(rtext)
                text=text.replace(" ","")
                keys = ["Hemoglobin","RBC","WBC","Neutrophils","Lymphocytes","Eosinophils","Monocytes","Basophils","Platelet Count","MCV","MCH","MCHC","RDW"]
                keyalternative = {"Hemoglobin":["haemoglobin","hmnog","hemoglo"],"RBC":["r.b.c","r.e.c"],"Monocytes":["monocyt"],"WBC":["wb.c","w.b.c","wec","w.e.c"],"Basophils":["basoph"],"MCV":["m.c.v"],"Platelet Count":["plateletcount","plateletscount","totalplatelet"],"MCHC":["m.c.h.c","mc.h.c."],"MCH":["m.c.h"],"RDW":["r.d.w"]}
                text = text.lower()
                value = []
                FinalResult = {}
                # if text.find('date'):
                #     cnt = text.find('date')
                #     while ord(str(text[cnt])) >= 58 or ord(str(text[cnt])) < 47:
                #             cnt += 1
                #     start = cnt
                #     for t in range(start, start+10):
                #             value.append(text[t])
                #     FinalResult['date']="".join(map(str, value)).replace("i","/")
                #     value=[]   
                print text
#		dt = re.search(r'[date:]*([0-9]{1,2}[\/-]([0-9]{1,2}|[a-z]{3})[\/-][0-9]{0,4})', text).group(1)                 
 #               dt = dt.replace("/","-")
  #              if bool(re.match('[\d/-]+$', dt)):
   #                 FinalResult['Date'] = str(datetime.strptime(dt,'%d-%m-%Y').date())
    #            else:
     #               FinalResult['Date'] = str(datetime.strptime(dt,'%d-%b-%Y').date())
                result = text.find("result")
                print text
                text = text[result:]
                fl=0
                for k in keys:
                    if k.lower() in text:
                        cnt=text.find(k.lower())
                        print k
                        print 'at'
                        print cnt
                        while ord(str(text[cnt])) >= 58 or ord(str(text[cnt])) < 47:
                            cnt += 1        
                        start = cnt
                        print 'value'
                        print cnt
                        while ((ord(str(text[cnt])) < 58 and ord(str(text[cnt])) > 45) or (ord(str(text[cnt])) == 44)):
                            cnt += 1
                        end = cnt

                        for t in range(start, end):
                            value.append(text[t])
                        FinalResult[k]="".join(map(str, value))
                        value=[]
                                
                        
                    elif k in keyalternative:
                        for kalt in keyalternative[k]:
                            if fl==0 and kalt.lower() in text:
                                fl=1
                                cnt=text.find(kalt.lower())
                                print k
                                print cnt
                                while ord(str(text[cnt])) >= 58 or ord(str(text[cnt])) < 47:
                                    cnt += 1
                                print 'value'
                                print cnt        
                                start = cnt
                                while ((ord(str(text[cnt])) < 58 and ord(str(text[cnt])) > 45) or (ord(str(text[cnt])) == 44)):
                                    cnt += 1
                                end = cnt

                                for t in range(start, end):
                                    value.append(text[t])
                                FinalResult[k]="".join(map(str, value))
                                value=[]
                                fl=0
                FinalResult["uID"]=request.form["id"]
                client = MongoClient()
                db = client.reports
                response=db.reports.insert(FinalResult)
                return redirect(url_for('getByMobileNo',ID=request.form["id"]))
        else:
            return redirect(url_for('getByMobileNo',ID=request.form["id"]))
        x = url_for('getByMobileNo')
        print x
    return render_template('index.html')
   
@app.route('/getReports/<ID>')
def getByMobileNo(ID):
    client = MongoClient()
    db = client.reports
    aggregate = []
    response = db.reports.find({"uID":ID})
    aggregate = json.loads(json_util.dumps(response))
    print aggregate[0]
    agg = {}
    agg['sample'] = aggregate
    for ids in agg['sample']:
    	del ids['_id']
        del ids['uID']
    table = json2html.convert(json = agg)
    
    table = table.replace('<table border="1"><tr><th>sample</th><td>','')
    table = table.replace('</td></tr></table></td></tr></table>','</td></tr></table>')
    table = table.replace('table border','table class="alt" border')
    return render_template('results.html',table_tags=table)
    # '''
    # <!doctype html>
    # <form action="http://projectmanthan.analytix.me/">
    # <h3><input style="display: inline" type="submit" value="Home">
    # Reports for ''' + ID + ''' &emsp;</h3>
    # </form>
    # '''+table+'''
    # '''


def id_generator(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def initilizeAzure():
        blob_service = BlobService(account_name='projectmanthan', account_key= storage_key)
        blob_service.create_container('reports', x_ms_blob_public_access='container')
        return blob_service

if __name__ == '__main__':
    app.run(debug=True)

