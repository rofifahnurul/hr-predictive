from concurrent.futures import process
import re
import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, render_template, request, redirect, url_for,session
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

def statistic(data,cluster, year):
    df = pd.DataFrame(data.loc[data['cluster'] == cluster]).describe()
    #cluster2 = pd.DataFrame(data.loc[data['cluster'] == 2]).describe()
    #cluster3 = pd.DataFrame(data.loc[data['cluster'] == 3]).describe()
    #cluster4 = pd.DataFrame(data.loc[data['cluster'] == 4]).describe()
    
    conn = mysql.connection
    cur = conn.cursor()

    count = df.to_numpy()[0][2]
    mean = df.to_numpy()[1]

    #for i in range(len(mean)-2):
    #    print("mean",mean[i+1])
    #    cluster = 1
    cur.execute('INSERT INTO statistic(cluster, count, kpiMean, performanceMean, competencyMean, learningMean, kerjaIbadahMean, apresiasiMean, lebihCepatMean, aktifBersamaMean, tahun ) VALUES (%s, % s, %s,%s,%s,%s,%s,%s,%s,%s, %s)', (cluster, count, mean[1],mean[2],mean[3],mean[4],mean[5],mean[6],mean[7],mean[8],year))
    
    mysql.connection.commit()

def insertItem(cluster,tahun):
    conn = mysql.connection
    cur = conn.cursor()
    cur.execute("SELECT * FROM asosiasi WHERE cluster = %s" ,cluster)
    details = cur.fetchall()
    columnNames  = cur.description
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
    
def insertSQLRules(associationRules,cluster,minSupp, minConf,tahun):
    listCol = []
    colNames = ["kpi","performance","learning","competency","learning","kerjaIbadah","apresiasi","lebihCepat","aktifBersama"]
    
    for row in associationRules:
       
        left = row[0]
        if len(left)>1:
            for i in range(len(left)-1):
                left = left[i]+ ", " + left[i+1]
            print("left",left)
        
        right = row[1]
      
        if len(right)>1:
            for i in range(len(right)-1):
                right= right[i]+ ", " + right[i+1]
            
        support = round(row[5],3)
        confidence = round(row[2],3)
        lift = round(row[3],3)
        conviction = row[4] 
    
        #print("right",len(right))
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO asosiasi (leftHand,rightHand,support,confidence,lift,conviction,minSupp,minConf,cluster,tahun) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(left,right,support,confidence,lift,conviction,minSupp,minConf,cluster,tahun))
        mysql.connection.commit()
    
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

#Create function to convert/process dataset for association

#Create route for main page
@app.route("/")
def main():
     # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template("index.html",username=session['username'])
    # User is not loggedin redirect to login page
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
        if request.method == 'POST':
            dataSelect = request.form['dataSelect']
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
                #conn = mysql.connection
                #cur = conn.cursor()     
                #cur.execute("SELECT * FROM penilaian")
                year = dataSelect
                dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
                data = pd.DataFrame(dataResult)
                data_numeric = data.iloc[:,2:10]
                    
                K=4
                Centroids = data_numeric.sample(n=K)
                tes = data_numeric.sample(n=K)
                    
                centroidFix, dataFix, data_numerics = kmeansScratch(K,data_numeric, Centroids,data)

                for index, row in dataFix.iterrows():
                    cluster = row['cluster']
                    id = row['id']
                    #Clustering result is added to database   
                    cur = mysql.connection.cursor()        
                    cur.execute("UPDATE penilaian SET cluster = %s WHERE id = %s",(cluster,id))
                    mysql.connection.commit()

                statistic(dataFix,1,year)
                statistic(dataFix,2,year)
                statistic(dataFix,3,year)
                statistic(dataFix,4,year)

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
            count2022 = donutClusterYear(2022)
            count2023 = donutClusterYear(2023)
   
            meanList2022 = linechartYear(2022)
            meanList2023 = linechartYear(2023)
            return render_template('clustering-result.html', meanList2022 = meanList2022, userDetails=userDetails,count2022=count2022,meanList2023 = meanList2023, count2023 = count2023)

    else:
        return redirect(url_for('login'))


   
#Create route to asosiasi process 
@app.route("/associationProcess", methods=['GET','POST'])
def associationProcess():
    if 'loggedin' in session: 
        #make connection and sql query
        if request.method == 'POST':
            dataSelect = request.form['dataSelect']
            conn = mysql.connection
            cur = conn.cursor()   

            if dataSelect == "Semua data":
                result = cur.execute("SELECT * FROM penilaian")
            else:
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
                min_support = 0.55
                min_confidence = 0.9

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
            
            cluster1 = data[data['cluster'] == 1]
            cluster2 = data[data['cluster'] == 2]
            cluster3 = data[data['cluster'] == 3]
            cluster4 = data[data['cluster'] == 4]

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
                if row['cluster'] == 1:
                    listItem1.append(row)
                if row['cluster'] == 2:
                    listItem2.append(row)
                if row['cluster'] == 3:
                    listItem3.append(row)
                if row['cluster'] == 4:
                    listItem4.append(row)
            print(items)
            #return "succces"
            return render_template('associationResult.html',submenu=associationResult,details = details, count = count,listItem1 = listItem1,listItem2 = listItem2, listItem3 = listItem3, listItem4 = listItem4, username=session['username'])
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
    xPCA = compPCA(data_numeric,data_cluster)
    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, frozenset):
                return list(obj)
            return json.JSONEncoder.default(self, obj)
    #json_list = json.loads(json.dumps(list(xPCA.T.to_dict().values())))
    result = xPCA.to_json(orient="records")
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


'''
@app.route("/donutCluster")
def donutCluster():  
    conn = mysql.connection
    cur = conn.cursor()   
    cur.execute("SELECT * FROM penilaian")
    columnNames  = cur.description
    dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
    data = pd.DataFrame(dataResult)

    cluster1 = pd.DataFrame(data.loc[data['cluster'] == 1])
    cluster2 = pd.DataFrame(data.loc[data['cluster'] == 2])
    cluster3 = pd.DataFrame(data.loc[data['cluster'] == 3])
    cluster4 = pd.DataFrame(data.loc[data['cluster'] == 4])
    
    #counts = {'cluster':[len(cluster1),len(cluster2),len(cluster3),len(cluster4)]}
    count = [len(cluster1),len(cluster2),len(cluster3),len(cluster4)]
    
    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, frozenset):
                return list(obj)
            return json.JSONEncoder.default(self, obj)
    return count

def linechartYear(year):   
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, tahun, cluster, nik, kpiNorm, performanceNorm, competencyNorm, learningNorm, kerjaIbadahNorm, apresiasiNorm, lebihCepatNorm, aktifBersamaNorm FROM penilaian WHERE tahun = %s",(year))
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

  
        elif request.method == 'POST':
            year = request.form['eachYear']          
            conn = mysql.connection
            cur = conn.cursor() 
            result = cur.execute("SELECT * FROM penilaian WHERE cluster is NOT NULL AND tahun = %s",(year))
            userDetails = cur.fetchall()
            count = donutClusterYear(year)
            meanList = linechartYear(year)

            return render_template('clustering-result-2022.html', userDetails=userDetails,count=count,meanList=meanList,year= year)


                if len(association_rules1) == 0:
                    checkIncreaseRules(rules,data,min_support,min_confidence):
                elif len(association_rules1)>5:
                    association_rules1,min_support_new,min_confidence_new = checkReduceRules(association_rules1,data1,min_support,min_confidence)
                    insertSQLRules(association_rules1, 1, min_support_new,min_confidence_new,tahun)  
                else:
                    insertSQLRules(association_rules1, 1, min_support,min_confidence,tahun)
                    
                if len(association_rules2)>5:
                    association_rules2,min_support_new,min_confidence_new = checkRules(association_rules2,data2,min_support,min_confidence)
                    insertSQLRules(association_rules2, 2, min_support_new,min_confidence_new,tahun)  
                else:
                    insertSQLRules(association_rules2, 2, min_support,min_confidence,tahun)
                    
                print("awal :", len(association_rules3))
                if len(association_rules3)>5:
                    association_rules3,min_support_new,min_confidence_new = checkRules(association_rules3,data3,min_support,min_confidence)
                    insertSQLRules(association_rules3, 3, min_support_new,min_confidence_new,tahun)
                    print("if more :", len(association_rules3))  
                else:
                    insertSQLRules(association_rules3, 3, min_support,min_confidence,tahun)
                    print("less :", len(association_rules3))

                if len(association_rules4)>5:
                    association_rules4,min_support_new,min_confidence_new = checkRules(association_rules4,data4,min_support,min_confidence)
                    insertSQLRules(association_rules4, 4, min_support_new,min_confidence_new,tahun)  
                else:
                    insertSQLRules(association_rules1, 4, min_support,min_confidence,tahun)
'''
if __name__ == "__main__":
    app.run(debug=True)