from concurrent.futures import process
import re
from statistics import mean
import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, render_template, request, redirect, url_for,session, send_file
#from flask_mysql_connector import MySQL
from flask_mysqldb import MySQL
from cluster_process import * 
import MySQLdb.cursors
from werkzeug.utils import secure_filename
import os
import pandas as pd
from apyori import apriori
import json
from aprioriScratch import *
from kmeansScratch import *
import plotly
import plotly.express as px
import plotly.graph_objects as go
from sklearn.decomposition import PCA 

UPLOAD_FOLDER = '/file'
ALLOWED_EXTENSIONS = {'csv', 'xls','xlsx'}

'''
Configure flask app 
Include database, localhost 
'''
app = Flask(__name__)
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='lulu160800'
app.config['MYSQL_DB']='hr'
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'

mysql = MySQL(app)

@app.route('/download_file')
def download_file():
    p = "Template.xlsx"
    return send_file(p,as_attachment=True)

#func to cluster using kmeans
def kmeansScratch(K,data_numeric, Centroids,data):
    columnC = Centroids.columns
    diff = 1
    j=0
    flag = 0
    while (diff!=0):
        XD=data_numeric
        column = XD.columns
        i=1
        for index1, row_c in Centroids.iterrows():
            ED=[]
            for index2, row_d in XD.iterrows():
                d1 = (row_d[column[0]]-row_c[columnC[0]])**2
                d2 = (row_d[column[1]]-row_c[columnC[1]])**2
                d3 = (row_d[column[2]]-row_c[columnC[2]])**2
                d4 = (row_d[column[3]]-row_c[columnC[3]])**2
                d5 = (row_d[column[4]]-row_c[columnC[4]])**2
                d6 = (row_d[column[5]]-row_c[columnC[5]])**2
                d7 = (row_d[column[6]]-row_c[columnC[6]])**2
                d8 = (row_d[column[7]]-row_c[columnC[7]])**2
                d = np.sqrt(d1+d2+d3+d4+d5+d6+d7+d8)
                ED.append(d)
            data_numeric[i]=ED
            i=i+1

        C=[]
             
        
        for index,row in data_numeric.iterrows():
            min_dist=row[1]
            pos=1
            for i in range(K-1):                  
                if row[i+2] < float(min_dist):   
                    min_dist = row[i+2]
                    pos=i+2
            C.append(pos)
            #if flag == 0:                              
            #    print("Masuk",pos)
            #else:
                #print("update",pos,row[1],row[2],row[3],row[4])

        flag+=1
        data_numeric["cluster"]=C
        data["cluster"] =C

        Centroids_new = data_numeric.groupby(["cluster"]).mean()[[column[0],column[1],column[2],column[3],
        column[4],column[5],column[6],column[7]]]

        if j == 0:
            diff=1
            j=j+1
        else:
            diff = (Centroids_new[column[0]] - Centroids[column[0]]).sum() 
            + (Centroids_new[column[1]] - Centroids[column[1]]).sum() 
            + (Centroids_new[column[2]] - Centroids[column[2]]).sum() 
            + (Centroids_new[column[3]] - Centroids[column[3]]).sum() 
            + (Centroids_new[column[4]] - Centroids[column[4]]).sum() 
            + (Centroids_new[column[5]] - Centroids[column[5]]).sum() 
            + (Centroids_new[column[6]] - Centroids[column[6]]).sum() 
            + (Centroids_new[column[7]] - Centroids[column[7]]).sum()
            print(diff.sum())                             
        Centroids = data_numeric.groupby(["cluster"]).mean()[[column[0],column[1],column[2],column[3],
        column[4],column[5],column[6],column[7]]]
        
        
    
    return Centroids, data, data_numeric

#function to find statistic value for each cluster
def statistic(data,cluster, year):
    conn = mysql.connection
    cur = conn.cursor()
    
    df  = pd.DataFrame(data.loc[data['cluster'] == cluster]).describe()

    conn = mysql.connection
    cur = conn.cursor()

    count = df.to_numpy()[0][2]
    mean = df.to_numpy()[1]

    cur.execute('INSERT INTO statistic(cluster, count, kpiMean, performanceMean, competencyMean, learningMean, kerjaIbadahMean, apresiasiMean, lebihCepatMean, aktifBersamaMean, tahun ) VALUES (%s, % s, %s,%s,%s,%s,%s,%s,%s,%s, %s)', (cluster, count, mean[0],mean[1],mean[2],mean[3],mean[4],mean[5],mean[6],mean[7],year))
    mysql.connection.commit()

#function to insert item from association rules
def insertItem(cluster,tahun):
    conn = mysql.connection
    cur = conn.cursor()
    cur.execute("SELECT * FROM asosiasi WHERE cluster = %s" ,cluster)
    details = cur.fetchall()

    data = pd.DataFrame(details,columns =['id','leftHand','rightHand','support','confidence','lift','conviction','minSupp','minConf','cluster','tahun'])
    listCol = []
    colNames = ["kpi","performance","learning","competency","learning","kerjaIbadah","apresiasi","lebihCepat","aktifBersama"]
    for column in colNames: 
        for i in data['leftHand']:
            if column in i:
                if column in listCol:
                    pass
                else:
                    listCol.append(column)
                    print("left hand", i, column)
        for i in data['rightHand']:
            if column in i:
                if column in listCol:
                    pass
                else:
                    listCol.append(column)
                    print("right hand", i, column)
                    
    for i in listCol:
        print(i)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO itemAssociation(item, cluster, tahun) VALUES (%s, %s, %s)', (i, cluster, tahun))
        mysql.connection.commit()

#function to add rules to sql   
def insertSQLRules(associationRules,cluster,minSupp, minConf,tahun):

    for row in associationRules:
        left = row[0]
        if len(left)>1:
            y = list(left)
            for i in range(len(y)-1):
                 left = str(y[i])+ "," + str(y[i+1])
            print("left",left)
        
        right = row[1]
        if len(right)>1:
            x = list(right)
            for i in range(len(x)-1):
                 left = str(y[i])+ "," + str(x[i+1])         
        support = row[5]
        confidence = row[2]
        lift = row[3]
        conviction = row[4] 

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO asosiasi (leftHand,rightHand,support,confidence,lift,conviction,minSupp,minConf,cluster,tahun) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(left,right,support,confidence,lift,conviction,minSupp,minConf,cluster,tahun))
        mysql.connection.commit()

#function to check number of rules 
def finalCheck(association_rules,data,min_support,min_confidence,tahun,cluster):
    
    if len(association_rules) == 0:
        association_rulesnew,min_support_new,min_confidence_new = checkIncreaseRules(association_rules,data,min_support,min_confidence)
        insertSQLRules(association_rulesnew, cluster, min_support_new,min_confidence_new,tahun)

    if len(association_rules)>5:
        association_rulesnew,min_support_new,min_confidence_new = checkReduceRules(association_rules,data,min_support,min_confidence)
        insertSQLRules(association_rulesnew, cluster, min_support_new,min_confidence_new,tahun)  

    else:
        insertSQLRules(association_rules, cluster, min_support,min_confidence,tahun)      


@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form :
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
      
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts(username, password) VALUES (% s, % s)', (username, password ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            return redirect(url_for('login',msg=msg))
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

@app.route("/login", methods=['GET','POST'])
def login():
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()

    # If account exists in accounts table in out database
        if account:
        # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
        # Redirect to home page
            return redirect(url_for('main'))
        else:
        # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template("login.html", msg=msg)

@app.route('/logout', methods = ['POST'])
def logout():
    if request.method == "POST":
        # Remove session data, this will log the user out
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        # Redirect to login page
    return redirect(url_for('login'))


#Create route for main page
@app.route("/")
def main():
     # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template("index.html",username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route("/info")
def info():
    if 'loggedin' in session:   
        return render_template('info.html', username=session['username'])
    else:
        return redirect(url_for('login'))
        
#Create route to data penilaian to show employee name 
@app.route("/datapenilaian", methods=['GET','POST'])
def datapenilaian():
    if 'loggedin' in session:   
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM penilaian")
        userDetails = cur.fetchall()
        return render_template('datapenilaian.html', submenu=datapenilaian,userDetails=userDetails,username=session['username'])
    else:
        return redirect(url_for('login'))

#Create route to data penilaian to show employee name 
app.config['UPLOAD_FOLDER'] = '/Users/agussuyono/documents/hr-predictive/file'
@app.route("/uploadFile", methods=['GET','POST'])
def uploadFile():
    if 'loggedin' in session: 
        status = 0

        if request.method == 'POST':
            date = request.form['date']
            date = date.split("/")
            date = date[2].split(" ")

            #get year using int(date[0])
            year = int(date[0])
            if request.files:
                file = request.files["file"]           
                msg="File already saved"
                ext = file.filename.rsplit('.', 1)[1].lower()
                acceptedExt = ['csv','xls','xlsx']
                if ext in acceptedExt:
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
                    status = 1
                #return file.filename.rsplit('.', 1)[0]
            
        if status == 1:
            path = "/Users/agussuyono/documents/hr-predictive/file/"+(file.filename)
            if ext == "csv":
                data = pd.read_csv(path)
            else:
                data = pd.read_excel(path)
            
            column = data.columns
            for i in range(len(data)):
                nik = data.loc[i, column[0]]
                kpi = data.loc[i, column[1]]
                performance = data.loc[i, column[2]]
                competency = data.loc[i, column[3]]
                learning = data.loc[i, column[4]]
                ki = data.loc[i, column[5]]
                apresiasi = data.loc[i, column[6]]
                lc = data.loc[i, column[7]]
                ab = data.loc[i, column[8]]
                
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO penilaian(tahun,nik,kpi,performance,competency,learning,kerjaIbadah,apresiasi,lebihCepat,aktifBersama) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(year,nik,kpi,performance,competency,learning,ki,apresiasi,lc,ab))
                mysql.connection.commit()
            return redirect(url_for('datapenilaian'))

        return redirect(url_for('datapenilaian'))
    else:
        return redirect(url_for('login'))

@app.route("/uploadFileData", methods=['GET','POST'])
def uploadFileData():
    if 'loggedin' in session: 
        status = 0

        if request.method == 'POST':

            if request.files:
                file = request.files["file"]           
                msg="File already saved"
                ext = file.filename.rsplit('.', 1)[1].lower()
                acceptedExt = ['csv','xls','xlsx']
                if ext in acceptedExt:
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
                    status = 1
                #return file.filename.rsplit('.', 1)[0]
            
        if status == 1:
            path = "/Users/agussuyono/documents/hr-predictive/file/"+(file.filename)
            if ext == "csv":
                data = pd.read_csv(path)
            else:
                data = pd.read_excel(path)
            
            data = data.drop_duplicates(subset=['NIK'],keep='first')
            data = data.dropna()
            column = data.columns
            for index,row in data.iterrows():                      
                nik = int(row['NIK'])
                businessUnit= row['BUSINESS_UNIT']
                jobLevel = row['JOB_LEVEL']
                location = row['LOCATION']
                department = row['DEPARTMENT']
                jobPosition = row['JOB_POSITION']
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO dataKaryawan(nik,businessUnit, jobLevel, location, department, jobPosition) VALUES(%s,%s,%s,%s,%s,%s)",(nik, businessUnit, jobLevel, location,department, jobPosition))
                mysql.connection.commit()
                
            return "ok"

        return redirect(url_for('dataKaryawan'))
    else:
        return redirect(url_for('login'))

@app.route("/dataKaryawan", methods=['GET','POST'])
def dataKaryawan():
    if 'loggedin' in session:   
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM dataKaryawan ")
        userDetails = cur.fetchall()
        print(result)
        return render_template('dataKaryawan.html', userDetails=userDetails,username=session['username'])

    else:
        return redirect(url_for('login'))

@app.route("/normalisasi", methods=['GET','POST'])
def normalisasi():
    if 'loggedin' in session:
        dataSelect = request.form['dataSelect']
        if request.method == 'POST':
            conn = mysql.connection
            cur = conn.cursor() 
            if dataSelect == "Semua data":
                result = cur.execute("SELECT id, nik, kpi, performance, competency, learning, kerjaIbadah, apresiasi, lebihCepat, aktifBersama FROM penilaian")
            else:
                year = dataSelect
                result = cur.execute("SELECT id, nik, kpi, performance, competency, learning, kerjaIbadah, apresiasi, lebihCepat, aktifBersama FROM penilaian WHERE tahun = %s",(year))
                
            if not result:
                msg = "Table is empty"
                return render_template('datapenilaian.html')
            else:
                columnNames  = cur.description
                dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
                dataResult = pd.DataFrame(dataResult)

                data_numeric = dataResult.iloc[:,:10]
                    
                array = data_numeric.values
                X = array[:,2:10]
            
                min_max_scaler = preprocessing.MinMaxScaler(feature_range=(0,1)) #inisialisasi normalisasi MinMax
                data = min_max_scaler.fit_transform(X) #transformasi MinMax untuk fitur
                df = pd.DataFrame({'id':array[:,0],'kpi':data[:,0],'performance':data[:,1],'competency':data[:,2],'learning':data[:,3],'kerjaIbadah':data[:,4],'apresiasi':data[:,5],'lebihCepat':data[:,6],'aktifBersama':data[:,7]})
                for index,row in df.iterrows():                      
                    id = int(row['id'])
                    kpiNorm = row['kpi']
                    print("kpiNorm",kpiNorm)
                    performanceNorm = row['performance']
                    competencyNorm = row['competency']
                    learningNorm = row['learning']
                    kerjaIbadahNorm = row['kerjaIbadah']
                    apresiasiNorm = row['apresiasi']
                    lebihCepatNorm = row['lebihCepat']
                    aktifBersamaNorm = row['aktifBersama']
                    cur = mysql.connection.cursor()  
                    cur.execute("UPDATE penilaian SET kpiNorm = %s, performanceNorm = %s, competencyNorm = %s, learningNorm = %s, kerjaIbadahNorm = %s, apresiasiNorm = %s, lebihCepatNorm = %s, aktifBersamaNorm = %s WHERE id = %s",(kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm, lebihCepatNorm, aktifBersamaNorm,id))
                    mysql.connection.commit()
                return redirect(url_for('normalisasiResult'))

            #return redirect(url_for('datapenilaian')) 

        return redirect(url_for('datapenilaian'))
    else:
        return redirect(url_for('login'))

#Create route to data penilaian to show employee name 
@app.route("/normalisasiResult", methods=['GET','POST'])
def normalisasiResult():
    if 'loggedin' in session: 
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT id, tahun, nik, kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm, lebihCepatNorm, aktifBersamaNorm FROM penilaian")
        details = cur.fetchall()
        
        conn = mysql.connection
        cur = conn.cursor()
        if not result:
            msg = "Table is empty"
            return render_template('normalisasiResult.html', details=details)
        else:
            return render_template('normalisasiResult.html', details=details)
        
    else:
        return redirect(url_for('login'))


#Create route to clusterprocess to process clustering
@app.route("/clusterProcess", methods=['GET','POST'])
def clusterProcess():
    if 'loggedin' in session: 
        if request.method == 'POST' and 'k' in request.form :
            dataSelect = request.form['dataSelect']
            k = request.form['k']
            conn = mysql.connection
            cur = conn.cursor()   

            if dataSelect == "Semua data":
                result = cur.execute("SELECT id, nik, kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm,  lebihCepatNorm, aktifBersamaNorm FROM penilaian")
                columnNames  = cur.description
            else:
                year = dataSelect
                result = cur.execute("SELECT id, nik, kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm,  lebihCepatNorm, aktifBersamaNorm FROM penilaian WHERE tahun = %s",(year))
                columnNames  = cur.description
            if not result:
                msg = "Table is empty"
                return render_template('datapenilaian.html')
            else:                  
                   
                #cur.execute("SELECT * FROM penilaian")
                year = dataSelect
                dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
                data = pd.DataFrame(dataResult)
                data_numeric = data.iloc[:,2:10]
                    
                K=int(k)
                Centroids = data_numeric.sample(n=K)
                '''
                Centroids['total'] = Centroids['kpiNorm'] + Centroids['performanceNorm'] + Centroids['competencyNorm'] + Centroids['learningNorm']+Centroids['kerjaIbadahNorm']+Centroids['apresiasiNorm']+Centroids['lebihCepatNorm'] + Centroids['aktifBersamaNorm']
                Centroids.sort_values(['total'],ascending=False,inplace=True)   
                Centroids.drop(['total'],axis=1)
                '''
                centroidFix, dataFix, data_numerics = kmeansScratch(K,data_numeric, Centroids,data)
                
                centroidFix['total'] = centroidFix['kpiNorm'] + centroidFix['performanceNorm'] + centroidFix['competencyNorm'] + centroidFix['learningNorm']+centroidFix['kerjaIbadahNorm']+centroidFix['apresiasiNorm']+centroidFix['lebihCepatNorm'] + centroidFix['aktifBersamaNorm']
                centroidFix.sort_values(['total'],ascending=False,inplace=True)   
                print(centroidFix)
                print(centroidFix.index)
                for index, row in dataFix.iterrows():
                    
                    if row['cluster'] == centroidFix.index[0]:
                        print("From {} to cluster 1 ".format(row['cluster']))
                        cluster = 1
    
                    elif row['cluster'] == centroidFix.index[1]:
                        print("From {} to cluster 2 ".format(row['cluster']))
                        cluster = 2
                    elif row['cluster'] == centroidFix.index[2]:
                        print("From {} to cluster 3 ".format(row['cluster']))
                        cluster = 3
                    elif row['cluster'] == centroidFix.index[3]:
                        print("From {} to cluster 1 ".format(row['cluster']))
                        cluster = 4
                    id = row['id']
                    #Clustering result is added to database   
                    cur = mysql.connection.cursor()        
                    cur.execute("UPDATE penilaian SET cluster = %s WHERE id = %s",(cluster,id))
                    mysql.connection.commit()

                
                conn = mysql.connection
                cur = conn.cursor()  
                result = cur.execute("SELECT kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm,  lebihCepatNorm, aktifBersamaNorm, cluster FROM penilaian WHERE tahun = %s",year)
                details = cur.fetchall()

                data = pd.DataFrame(details,columns =['kpiNorm', 'performanceNorm', 'competencyNorm', 'learningNorm', 'kerjaIbadahNorm', 'apresiasiNorm',  'lebihCepatNorm', 'aktifBersamaNorm','cluster'])

               
                statistic(data,1,year)
                statistic(data,2,year)
                statistic(data,3,year)
                statistic(data,4,year)
            

                return redirect(url_for('clusteringResult'))

            
        return redirect(url_for('clusteringResult'))
    else:
        return redirect(url_for('login'))

#Create route to clustering result to show clustering result from database

def donutClusterYear(year):  
    conn = mysql.connection
    cur = conn.cursor()   
    cur.execute("SELECT id, count, cluster, tahun FROM statistic WHERE tahun = %s",(year))
    columnNames  = cur.description
    dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
    data = pd.DataFrame(dataResult)

    count = data['count'].tolist()
    cluster1 = pd.DataFrame(data.loc[data['cluster'] == 1])
    cluster2 = pd.DataFrame(data.loc[data['cluster'] == 2])
    cluster3 = pd.DataFrame(data.loc[data['cluster'] == 3])
    cluster4 = pd.DataFrame(data.loc[data['cluster'] == 4])
    
    return count
@app.route("/linechartYear", methods=['GET','POST'])
def linechartYear(year):   
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, cluster, kpiMean, performanceMean, competencyMean, learningMean, kerjaIbadahMean, apresiasiMean, lebihCepatMean, aktifBersamaMean FROM statistic WHERE tahun = %s",(year))
    columnNames  = cur.description
    dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
    data = pd.DataFrame(dataResult)

    cluster1 = pd.DataFrame(data.loc[data['cluster'] == 1])
    cluster2 = pd.DataFrame(data.loc[data['cluster'] == 2])
    cluster3 = pd.DataFrame(data.loc[data['cluster'] == 3])
    cluster4 = pd.DataFrame(data.loc[data['cluster'] == 4])
    column = ['kpiMean', 'performanceMean', 'competencyMean', 'learningMean', 'kerjaIbadahMean', 'apresiasiMean', 'lebihCepatMean', 'aktifBersamaMean']

    meanList = []
    for i in column:
        
        meanList.append(data[i].tolist())
    
    #return mean1,mean2,mean3,mean4
    return meanList


@app.route("/clusteringResult", methods=['GET','POST'])
def clusteringResult():
    if 'loggedin' in session:   
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM penilaian WHERE cluster is NOT NULL")
        userDetails = cur.fetchall()
        conn = mysql.connection
        cur = conn.cursor()
        cur.execute("SELECT * FROM penilaian WHERE cluster is NOT NULL")
        columnNames  = cur.description
        count=[]
        meanList=[]
        if not result:
            msg = "Table is empty"           
            return redirect(url_for('normalisasiResult'))
        
        else:
            data = pd.DataFrame(userDetails,columns =['id','nik','kpi','performance','competency','learning','kerjaIbadah','apresiasi','lebihCepat','aktifBersama','cluster','tahun','kpiNorm','performanceNorm','competencyNorm','learningNorm','kerjaIbadahNorm','apresiasiNorm','lebihCepatNorm','aktifBersamaNorm'])
            if data['tahun'].nunique() > 1:
                count2022 = donutClusterYear(2022)
                count2023 = donutClusterYear(2023)

                return render_template('clustering-result.html', meanList2022 = meanList2022, userDetails=userDetails,count2022=count2022,meanList2023 = meanList2023, count2023 = count2023)
            else:
                count2022 = donutClusterYear(2022)
                meanList2022 = linechartYear(2022)
                return render_template('clustering-result.html', meanList2022 = meanList2022, userDetails=userDetails,count2022=count2022)
    else:
        return redirect(url_for('login'))


   
#Create route to asosiasi process 
@app.route("/associationProcess", methods=['GET','POST'])
def associationProcess():
    if 'loggedin' in session: 
        #make connection and sql query
        if request.method == 'POST' and 'minSupp' in request.form and 'minConf' in request.form:
            dataSelect = request.form['dataSelect']
            min_support = float(request.form['minSupp'])
            min_confidence = float(request.form['minConf'])

            conn = mysql.connection
            cur = conn.cursor()   
         
            year = dataSelect
            result = cur.execute("SELECT id, nik, kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm, lebihCepatNorm, aktifBersamaNorm, tahun, cluster FROM penilaian WHERE tahun = %s",(year))
            
            if not result:
                msg = "Table is empty"
                return redirect(url_for('clusteringResult'))
            else:
                
                columnNames  = cur.description
                dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
                data = pd.DataFrame(dataResult)
                column = data.columns
                    
                    #select data
                cluster1 = data.loc[data['cluster'] == 1]
                cluster2 = data.loc[data['cluster'] == 2]
                cluster3 = data.loc[data['cluster'] == 3]
                cluster4 = data.loc[data['cluster'] == 4]

                    #prepare to make a new dataframe (make categorical value for each cluster)
                data1 = pd.DataFrame()
                for i in range (2,10):
                    create_check(cluster1,column[i],data1)
    
                data2 = pd.DataFrame()
                for i in range (2,10):
                    create_check(cluster2,column[i],data2)

                data3 = pd.DataFrame()
                for i in range (2,10):
                    create_check(cluster3,column[i],data3)
    
                data4 = pd.DataFrame()
                for i in range (2,10):
                    create_check(cluster4,column[i],data4)

                status = 0

                association_rules1,freq_item_support1 = generateRules(data1,min_support,min_confidence)    
                association_rules2,freq_item_support1 = generateRules(data2,min_support,min_confidence)    
                association_rules3,freq_item_support1= generateRules(data3,min_support,min_confidence)             
                association_rules4,freq_item_support1 = generateRules(data4,min_support,min_confidence)
                tahun = data['tahun']
                tahun = tahun[0]
                
                finalCheck(association_rules1,data1,min_support,min_confidence,tahun,1)
                finalCheck(association_rules2,data2,min_support,min_confidence,tahun,2)
                finalCheck(association_rules3,data3,min_support,min_confidence,tahun,3)              
                finalCheck(association_rules4,data4,min_support,min_confidence,tahun,4)
                
                
                insertItem(1,tahun)
                insertItem(2,tahun)
                insertItem(3,tahun)
                insertItem(4,tahun)
                    
                return redirect(url_for('associationResult'))

    else:
        return redirect(url_for('login'))



@app.route("/associationResult")
def associationResult():
    if 'loggedin' in session: 
        conn = mysql.connection
        cur = conn.cursor()
        cur.execute("SELECT * FROM asosiasi")
        details = cur.fetchall()
        columnNames  = cur.description
        if not details:
            msg = "Table is empty"
            return render_template('normalisasiResult.html')
        else:
            data = pd.DataFrame(details,columns =['id','leftHand','rightHand','support','confidence','lift','conviction','minSupp','minConf','cluster','tahun'])

            if data['tahun'].nunique() > 1 :
             
                cluster1 = data[(data['cluster'] == 1) & (data['tahun'] == 2022)]
                cluster2 = data[(data['cluster'] == 2) & (data['tahun'] == 2022)]
                cluster3 = data[(data['cluster'] == 3) & (data['tahun'] == 2022)]
                cluster4 = data[(data['cluster'] == 4) & (data['tahun'] == 2022)]

                count = [len(cluster1),len(cluster2),len(cluster3),len(cluster4)]

                cluster1_23 = data[(data['cluster'] == 1) & (data['tahun'] == 2023)]
                cluster2_23 = data[(data['cluster'] == 2) & (data['tahun'] == 2023)]
                cluster3_23 = data[(data['cluster'] == 3) & (data['tahun'] == 2023)]
                cluster4_23 = data[(data['cluster'] == 4) & (data['tahun'] == 2023)]

                count_23 = [len(cluster1_23),len(cluster2_23),len(cluster3_23),len(cluster4_23)]


                cur = conn.cursor()
                cur.execute("SELECT * FROM itemAssociation")
                items = cur.fetchall()
                dataItem = pd.DataFrame(items,columns =['id','item','cluster','tahun'])

                listItem1 = []
                listItem2 = []
                listItem3 = []
                listItem4 = []

                listItem1_23 = []
                listItem2_23 = []
                listItem3_23 = []
                listItem4_23 = []
                for index,row in dataItem.iterrows():
                    if (row['cluster'] == 1) & (row['tahun']==2022) :
                        listItem1.append(row)
                    elif (row['cluster'] == 2) & (row['tahun']==2022) :
                        listItem2.append(row)
                    elif (row['cluster'] == 3) & (row['tahun']==2022) :
                        listItem3.append(row)
                    elif (row['cluster'] == 4) & (row['tahun']==2022) :
                        listItem4.append(row)
                    elif (row['cluster'] == 1) & (row['tahun']==2023) :
                        listItem1_23.append(row)
                    elif (row['cluster'] == 2) & (row['tahun']==2023) :
                        listItem2_23.append(row)
                    elif (row['cluster'] == 3) & (row['tahun']==2023) :
                        listItem3_23.append(row)
                    elif (row['cluster'] == 4) & (row['tahun']==2023) :
                        listItem4_23.append(row)

                print(items)
                #return "succces"
                return render_template('associationResult.html',submenu=associationResult,details = details, count = count, count_23 = count_23, 
                listItem1 = listItem1,listItem2 = listItem2, listItem3 = listItem3, listItem4 = listItem4,
                listItem1_23 = listItem1_23,listItem2_23 = listItem2_23,
                listItem3_23 = listItem3_23,
                listItem4_23=listItem4_23, username=session['username'])
            else:
                cluster1 = data[data['cluster'] == 1 ]
                cluster2 = data[data['cluster'] == 2 ]
                cluster3 = data[data['cluster'] == 3 ]
                cluster4 = data[data['cluster'] == 4 ]

                count = [len(cluster1),len(cluster2),len(cluster3),len(cluster4)]

        
                cur = conn.cursor()
                cur.execute("SELECT * FROM itemAssociation")
                items = cur.fetchall()
                dataItem = pd.DataFrame(items,columns =['id','item','cluster','tahun'])

                listItem1 = []
                listItem2 = []
                listItem3 = []
                listItem4 = []

                for index,row in dataItem.iterrows():
                    if row['cluster'] == 1 and row['tahun']==2022 :
                        listItem1.append(row)
                    elif row['cluster'] == 2 and row['tahun']==2022 :
                        listItem2.append(row)
                    elif row['cluster'] == 3 and row['tahun']==2022 :
                        listItem3.append(row)
                    elif row['cluster'] == 4 and row['tahun']==2022 :
                        listItem4.append(row)
                return render_template('associationResult.html',submenu=associationResult,details = details, count = count,listItem1 = listItem1,listItem2 = listItem2,listItem3 = listItem3, listItem4 = listItem4, username=session['username'])
                
    else:
        return redirect(url_for('login'))


@app.route("/viewPCA")
def viewPCA():  
    conn = mysql.connection
    cur = conn.cursor()   
    cur.execute("SELECT * FROM penilaian WHERE tahun = 2022")
    columnNames  = cur.description
    dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
    data = pd.DataFrame(dataResult)
    data_numeric = data.iloc[:,2:10]
    data_cluster = data.iloc[:,10]
    xPCA,tesPCA = compPCA(data_numeric,data_cluster)
    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, frozenset):
                return list(obj)
            return json.JSONEncoder.default(self, obj)
    #json_list = json.loads(json.dumps(list(xPCA.T.to_dict().values())))
    result = tesPCA.to_json(orient="records")
    parsed = json.loads(result)
    json_list= json.dumps(parsed, indent=4)  
    return json_list


@app.route("/linechart")
def linechart():   
    if 'loggedin' in session: 
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, tahun, cluster, nik, kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm, lebihCepatNorm, aktifBersamaNorm FROM penilaian")
        columnNames  = cur.description
        dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
        data = pd.DataFrame(dataResult)

        cluster1 = pd.DataFrame(data.loc[data['cluster'] == 1])
        cluster2 = pd.DataFrame(data.loc[data['cluster'] == 2])
        cluster3 = pd.DataFrame(data.loc[data['cluster'] == 3])
        cluster4 = pd.DataFrame(data.loc[data['cluster'] == 4])
    
        mean1 = cluster1.describe().loc['mean']
        mean2 = cluster2.describe().loc['mean']
        mean3 = cluster3.describe().loc['mean']
        mean4 = cluster4.describe().loc['mean']

        meanList=[]
        flag=3
        for i in range(8):        
            meanList.append(mean1.values[flag])
            flag+=1
        
        flag=3
        for i in range(8):        
            meanList.append(mean2.values[flag])
            flag+=1

        flag=3
        for i in range(8):        
            meanList.append(mean3.values[flag])
            flag+=1
        flag=3
        for i in range(8):        
            meanList.append(mean4.values[flag])
            flag+=1

        #return mean1,mean2,mean3,mean4
        return meanList
    else:
        return redirect(url_for('login'))

@app.route('/notdash')
def notdash():
   df = pd.DataFrame({
      'Fruit': ['Apples', 'Oranges', 'Bananas', 'Apples', 'Oranges', 
      'Bananas'],
      'Amount': [4, 1, 2, 2, 4, 5],
      'City': ['SF', 'SF', 'SF', 'Montreal', 'Montreal', 'Montreal']
   })
   fig = px.bar(df, x='Fruit', y='Amount', color='City', 
      barmode='group')
   graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
   return render_template('notdash.html', graphJSON=graphJSON)

def countFunc(data,column):
  count=[]
  job = []
  for i in data[column].unique():
    job.append(i)
    countItem = len(data.loc[data[column] == i])
    count.append(countItem)

  df = pd.DataFrame({"column":job,"count":count})
  return df

def countAllCluster(data,column):
  df1 = countFunc(data[0],column)
  df2 = countFunc(data[1],column)
  df3 = countFunc(data[2],column)
  df4 = countFunc(data[3],column)
  return df1,df2,df3,df4

def sortCount(data):
    df1 = data[0].sort_values(by=['count'],ascending=False)
    df2 = data[1].sort_values(by=['count'],ascending=False)
    df3 = data[2].sort_values(by=['count'],ascending=False)
    df4 = data[3].sort_values(by=['count'],ascending=False)
    return df1,df2,df3,df4

def makeFig(data1,data2,data3,data4,nameList,title,x_col,y_col):
  fig = go.Figure(data=[
      go.Bar(name=nameList[0],x=data1[x_col],y=data1[y_col],marker=dict(color = "#d96f72")),
      go.Bar(name=nameList[1],x=data2[x_col],y=data2[y_col],marker=dict(color = "#f2e268")),
      go.Bar(name=nameList[2],x=data3[x_col],y=data3[y_col],marker=dict(color = "#ade872")),
      go.Bar(name=nameList[3],x=data4[x_col],y=data4[y_col],marker=dict(color = "#92b4d6"))
      ])
  
  fig.update_layout(
      updatemenus=[
          dict(
              type="buttons",
               direction="right",
               x=0.57,
               y=1.2,
               buttons=list([
                   dict(label="Both",
                        method="update",
                        args=[{"visible": [True, True, True, True]},
                              {"title": title}]),
                   dict(label=nameList[0],
                        method="update",
                        args=[{"visible": [True, False, False, False]},
                              {"title": title + nameList[0]}]),
                   dict(label=nameList[1],
                        method="update",
                        args=[{"visible": [False, True, False, False]},
                              {"title": title + nameList[1]}]),
                  dict(label=nameList[2],
                        method="update",
                        args=[{"visible": [False, False, True, False]},
                              {"title": title + nameList[2]}]),
                  dict(label=nameList[3],
                        method="update",
                        args=[{"visible": [False, False, False, True]},
                              {"title": title + nameList[3]}]),
               
            ]),
        )
    ])

  # Change the bar mode
  fig.update_layout(barmode='group',title=title)
  return fig

@app.route('/visualisasi')
def visualisasi():
    if 'loggedin' in session: 
        cur = mysql.connection.cursor()
        cur.execute("SELECT tahun, nik, cluster, kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm, lebihCepatNorm, aktifBersamaNorm FROM penilaian")
        columnNames  = cur.description
        dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
        data= pd.DataFrame(dataResult)

        cluster1 = pd.DataFrame(data.loc[data['cluster'] == 1])
        cluster2 = pd.DataFrame(data.loc[data['cluster'] == 2])
        cluster3 = pd.DataFrame(data.loc[data['cluster'] == 3])
        cluster4 = pd.DataFrame(data.loc[data['cluster'] == 4])

        cur = mysql.connection.cursor()
        cur.execute("SELECT nik, businessUnit, jobLevel, location, department, jobPosition FROM dataKaryawan")
        columnNames  = cur.description
        dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
        masterData= pd.DataFrame(dataResult)

        mergedCSV = masterData[['nik','businessUnit','location','department','jobPosition','jobLevel']].merge(cluster1, on = 'nik',how = 'right')
        mergedCSV2 = masterData[['nik','businessUnit','location','department','jobPosition','jobLevel']].merge(cluster2, on = 'nik',how = 'right')
        mergedCSV3 = masterData[['nik','businessUnit','location','department','jobPosition','jobLevel']].merge(cluster3, on = 'nik',how = 'right')
        mergedCSV4 = masterData[['nik','businessUnit','location','department','jobPosition','jobLevel']].merge(cluster4, on = 'nik',how = 'right')

        nameList = ["Cluster 1","Cluster 2", "Cluster 3", "Cluster 4"]
        #Count graph
        
        count = [len(mergedCSV),len(mergedCSV2),len(mergedCSV3),len(mergedCSV4)]
        cluster = ["cluster 1","cluster 2","cluster 3","cluster 4"]

        dataframe = pd.DataFrame({"cluster":cluster,"count":count})

        df1 = dataframe.loc[dataframe['cluster'] == "cluster 1"]
        df2 = dataframe.loc[dataframe['cluster'] == "cluster 2"]
        df3 = dataframe.loc[dataframe['cluster'] == "cluster 3"]
        df4 = dataframe.loc[dataframe['cluster'] == "cluster 4"]

        countFig = go.Figure(data=[
            go.Bar(name='Cluster 1',x=df1['cluster'],y=df1['count'],marker=dict(color = "#d96f72"),text=df1['count'],textposition='outside'),
            go.Bar(name='Cluster 2',x=df2['cluster'],y=df2['count'],marker=dict(color = "#f2e268"),text=df2['count'],textposition='outside'),
            go.Bar(name='Cluster 3',x=df3['cluster'],y=df3['count'],marker=dict(color = "#ade872"),text=df3['count'],textposition='outside'),
            go.Bar(name='Cluster 4',x=df4['cluster'],y=df4['count'],marker=dict(color = "#92b4d6"),text=df4['count'],textposition='outside')
        ])
        countFig.update_layout(barmode='group',title="Jumlah Item (Count)")
        #End Count graph
        
        data = [mergedCSV, mergedCSV2,mergedCSV3,mergedCSV4]
        
        #Job Level
        df1,df2,df3,df4 = countAllCluster(data,'jobLevel')
        jobFig = makeFig(df1,df2,df3,df4,nameList,"Job Level ","column","count")
        
        #Business Unit
        df1,df2,df3,df4 = countAllCluster(data,'businessUnit')
        unitFig = makeFig(df1,df2,df3,df4,nameList,"Business Unit ","column","count")

        #Top 5 Department
        df1,df2,df3,df4 = countAllCluster(data,'department') 
        dataframe = [df1,df2,df3,df4]
        df1Sort,df2Sort,df3Sort,df4Sort = sortCount(dataframe)
        depFig = makeFig(df1Sort.head(5),df2Sort.head(5),df3Sort.head(5),df4Sort.head(5),nameList, "Top 5 Department ","column","count")

         
        cur = mysql.connection.cursor()
        cur.execute("SELECT cluster, kpiMean, performanceMean, competencyMean, learningMean, kerjaIbadahMean, apresiasiMean, lebihCepatMean, aktifBersamaMean FROM statistic WHERE tahun = 2022")
        columnNames  = cur.description
        dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
        dataMean = pd.DataFrame(dataResult)

        cluster1 = pd.DataFrame(dataMean.loc[dataMean['cluster'] == 1])
        cluster2 = pd.DataFrame(dataMean.loc[dataMean['cluster'] == 2])
        cluster3 = pd.DataFrame(dataMean.loc[dataMean['cluster'] == 3])
        cluster4 = pd.DataFrame(dataMean.loc[dataMean['cluster'] == 4])
        column = ['kpiMean', 'performanceMean', 'competencyMean', 'learningMean', 'kerjaIbadahMean', 'apresiasiMean', 'lebihCepatMean', 'aktifBersamaMean']

        df1 = pd.melt(cluster1, id_vars='cluster')
        df2 = pd.melt(cluster2, id_vars='cluster')
        df3 = pd.melt(cluster3, id_vars='cluster')
        df4 = pd.melt(cluster4, id_vars='cluster')

        meanFig = makeFig(df1,df2,df3,df4,nameList,"Rata - rata nilai ","variable","value")

        countGraphJSON = json.dumps(countFig, cls=plotly.utils.PlotlyJSONEncoder)
        jobGraphJSON= json.dumps(jobFig, cls=plotly.utils.PlotlyJSONEncoder)
        unitGraphJSON = json.dumps(unitFig, cls=plotly.utils.PlotlyJSONEncoder)
        depGraphJSON = json.dumps(depFig, cls=plotly.utils.PlotlyJSONEncoder)
        meanGraphJSON = json.dumps(meanFig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('visualisasi.html', countGraphJSON = countGraphJSON, jobGraphJSON = jobGraphJSON, unitGraphJSON = unitGraphJSON, depGraphJSON = depGraphJSON, meanGraphJSON = meanGraphJSON)
    else:
        return redirect(url_for('login'))



@app.route('/insert', methods = ['POST'])
def insert():
    if 'loggedin' in session: 
        if request.method == "POST":
            name = request.form['name']
            cur = mysql.connection.cursor()
            #cur.execute("SELECT * FROM test")
            #id = cur.lastrowid
            cur.execute("INSERT INTO test(name) VALUES(%s)",(name))
        
            mysql.connection.commit()
            return redirect(url_for('datapenilaian'))
    else:
        return redirect(url_for('login'))

@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    if 'loggedin' in session: 
        #flash("Record Has Been Deleted Successfully")
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM penilaian WHERE id=%s", (id_data,))
        mysql.connection.commit()
        return redirect(url_for('datapenilaian'))
    else:
        return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)