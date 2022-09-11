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
def create_check(cluster,column_name,data):
  result = []
  for value in cluster[column_name]:
    avg = cluster[column_name].mean()
    if float(value) >= float(avg):
      string = str(column_name)+">=" + str(cluster[column_name].mean())
      result.append(string) 
      
    else:
      string = str(column_name)+"<" + str(cluster[column_name].mean())
      result.append(string)
  column_new = str(column_name) + "_check"
  cluster[column_new] = result 
  data[column_new]=result


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
        return render_template('datapenilaian.html', userDetails=userDetails,username=session['username'])
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
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
                msg="File already saved"
                #get ext : file.filename.rsplit('.', 1)[1].lower()
                status = 1
                #return file.filename.rsplit('.', 1)[0]
            
        if status == 1:
            read_file(file.filename)
            path = "/Users/agussuyono/documents/hr-predictive/file/"+(file.filename)
            data = pd.read_excel(path)

            column = data.columns
            for i in range(len(data)):
                nik = data.loc[i, column[1]]
                kpi = data.loc[i, column[2]]
                performance = data.loc[i, column[3]]
                competency = data.loc[i, column[4]]
                learning = data.loc[i, column[5]]
                ki = data.loc[i, column[6]]
                apresiasi = data.loc[i, column[7]]
                lc = data.loc[i, column[8]]
                ab = data.loc[i, column[9]]
                
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO penilaian(tahun,nik,kpi,performance,competency,learning,kerjaIbadah,apresiasi,lebihCepat,aktifBersama) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(year,nik,kpi,performance,competency,learning,ki,apresiasi,lc,ab))
                mysql.connection.commit()
            return redirect(url_for('datapenilaian'))

        return redirect(url_for('datapenilaian'))
    else:
        return redirect(url_for('login'))

#Create route to data penilaian to show employee name 
@app.route("/clusterProcess", methods=['GET','POST'])
def clusterProcess():
    if 'loggedin' in session: 
        if request.method == 'POST':
            dataSelect = request.form['dataSelect']
            conn = mysql.connection
            cur = conn.cursor()   

            if dataSelect == "Semua data":
                result = cur.execute("SELECT * FROM penilaian")
                if not result:
                    msg = "Table is empty"
                    return render_template('datapenilaian.html')
                else:
                    cur.execute("SELECT * FROM penilaian")
                    columnNames  = cur.description
                    dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
                    data = pd.DataFrame(dataResult)
                    data_numeric = data.iloc[:,2:10]
                   

                    data, data_numeric = kmeans(data,data_numeric)

                    cur = mysql.connection.cursor()

                    #cur.execute("SELECT * FROM test")
                    #id = cur.lastrowid
                    column = data.columns
                    for i in range(len(data)):
                        id = data.loc[i, column[0]]
                        cluster = data.loc[i, column[10]]

                        #Clustering result is added to database           
                        cur.execute("UPDATE penilaian SET cluster = %s WHERE id = %s",(cluster,id))
                        mysql.connection.commit()

                    return redirect(url_for('clusteringResult'))

            else:
                year = dataSelect
                result = cur.execute("SELECT * FROM penilaian WHERE tahun = %s" ,year)
                if not result:
                    msg = "Table is empty"
                    return render_template('datapenilaian.html')
                else:
                    
                    cur.execute("SELECT * FROM penilaian WHERE tahun = %s" ,year)
                    columnNames  = cur.description
                    dataResult = [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
                    data = pd.DataFrame(dataResult)
                    data_numeric = data.iloc[:,2:10]

                    data, data_numeric = kmeans(data,data_numeric)

                    cur = mysql.connection.cursor()

                    #cur.execute("SELECT * FROM test")
                    #id = cur.lastrowid
                    column = data.columns
                    for i in range(len(data)):
                        id = data.loc[i, column[0]]
                        cluster = data.loc[i, column[10]]

                        #Clustering result is added to database           
                        cur.execute("UPDATE penilaian SET cluster = %s WHERE id = %s",(cluster,id))
                        mysql.connection.commit()

                    return redirect(url_for('clusteringResult'))

        return redirect(url_for('clusteringResult'))
    else:
        return redirect(url_for('login'))


#Create route to clustering result to show clustering result from database
@app.route("/clusteringResult", methods=['GET','POST'])
def clusteringResult():
    if 'loggedin' in session:   
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM penilaian")
        userDetails = cur.fetchall()
        conn = mysql.connection
        cur = conn.cursor()
        cur.execute("SELECT * FROM penilaian")
        columnNames  = cur.description
        if not result:
            msg = "Table is empty"
            return render_template('clustering-result.html', userDetails=userDetails)
        else:
      
            return render_template('clustering-result.html', userDetails=userDetails)
    else:
        return redirect(url_for('login'))
        



'''
#Create route to clustering result to show clustering result from database
@app.route("/clusteringResult", methods=['GET','POST'])
def clusteringResult():
    if 'loggedin' in session:   
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM penilaian")
        userDetails = cur.fetchall()
        conn = mysql.connection
        cur = conn.cursor()
        cur.execute("SELECT * FROM penilaian")
        columnNames  = cur.description
        if not result:
            msg = "Table is empty"
            return render_template('clustering-result.html', userDetails=userDetails)
        else:

            #add to dataframe
            df= [{columnNames[index][0]: column for index, column in enumerate(value)} for value in cur.fetchall()]
            df= pd.DataFrame(df)
            x = df.iloc[:,2:-1]
            pca = PCA(n_components=3)
            X_pca = pca.fit_transform(x)
            var = pca.explained_variance_ratio_.cumsum()
            fig1 = px.bar(range(1,len(var)+ 1), var,title='Cumulative explained variance')
            graph1JSON = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
         
            return render_template('clustering-result.html', userDetails=userDetails,graph1JSON=graph1JSON)
    else:
        return redirect(url_for('login'))
        

@app.route('/clusteringProcess', methods=['GET','POST'])
def clusteringProcess():
    date = ""
    if 'loggedin' in session:   
        status = 0
    
        #collect data from uploaded file
        if request.method == 'POST':
            year = request.form['year']
            conn = mysql.connection
            cur = conn.cursor()
            result = cur.execute("SELECT * FROM penilaian")
            
            cur.execute("SELECT * FROM penilaian WHERE tahun = ?",year)
            columnNames  = cur.description

          
       

       
            #Clustering Process
       
            with open ('centroids.pkl','rb') as file:
                centroid = pickle.load(file)

            diff = 1
            j=0
            K=4

            XD=data_numeric
            i=1
            for index1, row_c in centroid.iterrows():
                ED=[]
                for index2, row_d in XD.iterrows():
                    d1 = (row_d["PK"]-row_c["PK"])**2
                    d2 = (row_d["PERFORMANCE"]-row_c["PERFORMANCE"])**2
                    d3 = (row_d["COMPETENCY"]-row_c["COMPETENCY"])**2
                    d4 = (row_d["LEARNING POINT"]-row_c["LEARNING POINT"])**2
                    d5 = (row_d["Kerja Ibadah"]-row_c["Kerja Ibadah"])**2
                    d6 = (row_d["Apresiasi"]-row_c["Apresiasi"])**2
                    d7 = (row_d["Lebih cepat"]-row_c["Lebih cepat"])**2
                    d8 = (row_d["Aktif bersama"]-row_c["Aktif bersama"])**2
                    d = np.sqrt(d1+d2+d3+d4+d5+d6+d7+d8)
                    ED.append(d)
                data_numeric[i]=ED
                i=i+1

            C=[]
            for index,row in data_numeric.iterrows():
                min_dist=row[1]
                pos=1
                for i in range(K):
                    if row[i+1] < int(min_dist):
                        min_dist = row[i+1]
                        pos=i+1
                C.append(pos)
            data_numeric["Cluster"]=C
            data["Cluster"] =C
            cur = mysql.connection.cursor()
            #cur.execute("SELECT * FROM test")
            #id = cur.lastrowid
            column = data.columns
            for i in range(len(data)):
                nik = data.loc[i, column[1]]
                kpi = data.loc[i, column[2]]
                performance = data.loc[i, column[3]]
                competency = data.loc[i, column[4]]
                learning = data.loc[i, column[5]]
                ki = data.loc[i, column[6]]
                apresiasi = data.loc[i, column[7]]
                lc = data.loc[i, column[8]]
                ab = data.loc[i, column[9]]
                cluster = data.loc[i, column[10]]

              
                #Clustering result is added to database 
          
                cur.execute("INSERT INTO penilaian(tahun,nik,kpi,performance,competency,learning,kerjaIbadah,apresiasi,lebihCepat,aktifBersama,cluster) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(year,nik,kpi,performance,competency,learning,ki,apresiasi,lc,ab,cluster))
                mysql.connection.commit()

           
            return redirect(url_for('clusteringResult'))
          
        # return render_template("clustering.html", 
        #column_names=data_numeric.columns.values, row_data=list(data_numeric.values.tolist()),zip = zip)
        return render_template("clustering.html",menu="data",submenu="clustering",text="sukses",username=session['username'],date=date)
     
    else:
        return redirect(url_for('login'))
#Create route to clustering process (input data and process it to database)
app.config['UPLOAD_FOLDER'] = '/Users/agussuyono/documents/hr-predictive/file'
@app.route('/clustering', methods=['GET','POST'])
def clustering():
    date = ""
    if 'loggedin' in session:   
        status = 0
    
        #collect data from uploaded file
        if request.method == 'POST':
    
            date = request.form['date']
            date = date.split("/")
            date = date[2].split(" ")

            #get year using int(date[0])
            year = int(date[0])
            if request.files:
                file = request.files["file"]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
                msg="File already saved"
                #get ext : file.filename.rsplit('.', 1)[1].lower()
                status = 1
                #return file.filename.rsplit('.', 1)[0]
            
        if status == 1:
            read_file(file.filename)
            path = "/Users/agussuyono/documents/hr-predictive/file/"+(file.filename)
            data = pd.read_excel(path)
            data_numeric = data.iloc[:,2:10]
            #preprocess(file.filename)
            #return redirect(request.url)


            #Clustering Process
       
            with open ('centroids.pkl','rb') as file:
                centroid = pickle.load(file)

            diff = 1
            j=0
            K=4

            XD=data_numeric
            i=1
            for index1, row_c in centroid.iterrows():
                ED=[]
                for index2, row_d in XD.iterrows():
                    d1 = (row_d["PK"]-row_c["PK"])**2
                    d2 = (row_d["PERFORMANCE"]-row_c["PERFORMANCE"])**2
                    d3 = (row_d["COMPETENCY"]-row_c["COMPETENCY"])**2
                    d4 = (row_d["LEARNING POINT"]-row_c["LEARNING POINT"])**2
                    d5 = (row_d["Kerja Ibadah"]-row_c["Kerja Ibadah"])**2
                    d6 = (row_d["Apresiasi"]-row_c["Apresiasi"])**2
                    d7 = (row_d["Lebih cepat"]-row_c["Lebih cepat"])**2
                    d8 = (row_d["Aktif bersama"]-row_c["Aktif bersama"])**2
                    d = np.sqrt(d1+d2+d3+d4+d5+d6+d7+d8)
                    ED.append(d)
                data_numeric[i]=ED
                i=i+1

            C=[]
            for index,row in data_numeric.iterrows():
                min_dist=row[1]
                pos=1
                for i in range(K):
                    if row[i+1] < int(min_dist):
                        min_dist = row[i+1]
                        pos=i+1
                C.append(pos)
            data_numeric["Cluster"]=C
            data["Cluster"] =C
            cur = mysql.connection.cursor()
            #cur.execute("SELECT * FROM test")
            #id = cur.lastrowid
            column = data.columns
            for i in range(len(data)):
                nik = data.loc[i, column[1]]
                kpi = data.loc[i, column[2]]
                performance = data.loc[i, column[3]]
                competency = data.loc[i, column[4]]
                learning = data.loc[i, column[5]]
                ki = data.loc[i, column[6]]
                apresiasi = data.loc[i, column[7]]
                lc = data.loc[i, column[8]]
                ab = data.loc[i, column[9]]
                cluster = data.loc[i, column[10]]

              
                Clustering result is added to database 
             
                cur.execute("INSERT INTO penilaian(tahun,nik,kpi,performance,competency,learning,kerjaIbadah,apresiasi,lebihCepat,aktifBersama,cluster) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(year,nik,kpi,performance,competency,learning,ki,apresiasi,lc,ab,cluster))
                mysql.connection.commit()

           
            return redirect(url_for('clusteringResult'))
          
        # return render_template("clustering.html", 
        #column_names=data_numeric.columns.values, row_data=list(data_numeric.values.tolist()),zip = zip)
        return render_template("clustering.html",menu="data",submenu="clustering",text="sukses",username=session['username'],date=date)
     
    else:
        return redirect(url_for('login'))
'''
#route for create association from database
@app.route("/asosiasiData")
def asosiasiData():
    if 'loggedin' in session: 
        #make connection and sql query
        conn = mysql.connection
        cur = conn.cursor()
        result = cur.execute("SELECT * FROM penilaian")
        cur.execute("SELECT * FROM penilaian")
        columnNames  = cur.description

        if not result:
            msg = "Table is empty"
            return render_template('asosiasiData.html')

        else:
            #add to dataframe
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

            '''
            Make association rules for each cluster
    
            '''
            #for i in range(0, len(data3)):
            #    records3.append([str(data3.values[i,j]) for j in range(0, 8)])
            #associationRules_3 = apriori(records3, min_support=0.55, min_confidence=0.9, min_length = 2)
            #associationResults_3 = list(associationRules_3)

            records1 = np.array(data1)
            freq_items1, item_support_dict1 = aprioriFunc(records1, min_support = 0.55)
            association_rules1 = create_rules(freq_items1, item_support_dict1, min_confidence = 0.9)

            records2 = np.array(data2)
            freq_items2, item_support_dict2 = aprioriFunc(records2, min_support = 0.55)
            association_rules2 = create_rules(freq_items2, item_support_dict2, min_confidence = 0.9)

            records3 = np.array(data3)
            freq_items3, item_support_dict3 = aprioriFunc(records3, min_support = 0.55)
            association_rules3 = create_rules(freq_items3, item_support_dict3, min_confidence = 0.9)
    
            records4 = np.array(data4)
            freq_items4, item_support_dict4 = aprioriFunc(records4, min_support = 0.55)
            association_rules4 = create_rules(freq_items4, item_support_dict4, min_confidence = 0.9)
    

            class SetEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, frozenset):
                        return list(obj)
                    return json.JSONEncoder.default(self, obj)
            #data = json.dumps(list(data_result), cls=SetEncoder)
            #return "aturan asosiasi", json.dumps(list(association_rules3['0']), cls=SetEncoder)
            #return "aturan asosiasi" + str(list(association_rules3[0][0]))
            return render_template('asosiasiData.html',submenu=asosiasiData, details1=list(association_rules1),details2=list(association_rules2),details3=list(association_rules3),details4=list(association_rules4),username=session['username'])
    else:
        return redirect(url_for('login'))


@app.route("/asosiasi",methods=['GET','POST'])
def asosiasi():
    if 'loggedin' in session: 
        status = 0
        if request.method == 'POST':
            if request.files:
                file = request.files["file"]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
                print("Asosiasi saved")
                #get ext : file.filename.rsplit('.', 1)[1].lower()
                status = 1
        if status == 1:
            #read_file(file.filename)
            path = "/Users/agussuyono/documents/project-skripsi/file/"+(file.filename)
            #data = pd.read_excel(path)
            data = pd.read_csv(path)
            records = []
            for i in range(0, 601):
                records.append([str(data.values[i,j]) for j in range(0, 9)])

            association_rules = apriori(records, min_support=0.4, min_confidence=0.9)
            association_results = list(association_rules)
        
            class SetEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, frozenset):
                        return list(obj)

                    return json.JSONEncoder.default(self, obj)
        
        
            return json.dumps(association_results, cls=SetEncoder)
        return render_template("asosiasi.html", menu="data",submenu="asosiasi",username=session['username'])
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