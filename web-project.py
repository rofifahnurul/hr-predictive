from re import I
import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, render_template, request, redirect, url_for
#from flask_mysql_connector import MySQL
from flask_mysqldb import MySQL
from cluster_process import * 
import MySQLdb.cursors
from werkzeug.utils import secure_filename
import os
import pickle
import pandas as pd
from apyori import apriori
import json

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
mysql = MySQL(app)

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
    return render_template("datapenilaian.html")

#Create route to data penilaian to show employee name 
@app.route("/datapenilaian", methods=['GET','POST'])
def datapenilaian():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM nilai2021")
    userDetails = cur.fetchall()
    return render_template('datapenilaian.html', userDetails=userDetails)

#Create route to clustering result to show clustering result from database
@app.route("/clusteringResult", methods=['GET','POST'])
def clusteringResult():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM nilai2021")
    userDetails = cur.fetchall()
    return render_template('clustering-result.html', userDetails=userDetails)

#Create route to clustering process (input data and process it to database)
app.config['UPLOAD_FOLDER'] = '/Users/agussuyono/documents/project-skripsi/file'
@app.route('/clustering', methods=['GET','POST'])
def clustering():
    status = 0
    
    #collect fata from uploaded file
    if request.method == 'POST':
        if request.files:
            file = request.files["file"]
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
            print("Image saved")
            #get ext : file.filename.rsplit('.', 1)[1].lower()
            status = 1
            #return file.filename.rsplit('.', 1)[0]
    if status == 1:
        read_file(file.filename)
        path = "/Users/agussuyono/documents/project-skripsi/file/"+(file.filename)
        data = pd.read_excel(path)
        data_numeric = data.iloc[:,2:10]
        #preprocess(file.filename)
        #return redirect(request.url)

        '''
        Clustering Process
        '''
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

            '''
            Clustering result is added to database 
            '''
            cur.execute("INSERT INTO nilai2021(nik,kpi,performance,competency,learning,kerjaIbadah,apresiasi,lebihCepat,aktifBersama,cluster) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(nik,kpi,performance,competency,learning,ki,apresiasi,lc,ab,cluster))
            mysql.connection.commit()
        return redirect(url_for('clusteringResult'))
   # return render_template("clustering.html", 
    #column_names=data_numeric.columns.values, row_data=list(data_numeric.values.tolist()),zip = zip)
    return render_template("clustering.html",menu="data",submenu="clustering",text="sukses")

#route for create association from database
@app.route("/asosiasiData")
def asosiasiData():
    #make connection and sql query
    conn = mysql.connection
    cur = conn.cursor()
    cur.execute("SELECT * FROM nilai2021")
    columnNames  = cur.description

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

    records1 = []
    for i in range(0, len(data1)):
        records1.append([str(data1.values[i,j]) for j in range(0, 8)])
    associationRules_1 = apriori(records1, min_support=0.55, min_confidence=0.9, min_length = 2)
    associationResults_1 = list(associationRules_1)

    records2 = []
    for i in range(0, len(data2)):
        records2.append([str(data2.values[i,j]) for j in range(0, 8)])
    associationRules_2 = apriori(records2, min_support=0.55, min_confidence=0.9, min_length = 2)
    associationResults_2 = list(associationRules_2)

    records3 = []
    for i in range(0, len(data3)):
        records3.append([str(data3.values[i,j]) for j in range(0, 8)])
    associationRules_3 = apriori(records3, min_support=0.55, min_confidence=0.9, min_length = 2)
    associationResults_3 = list(associationRules_3)

    records4 = []
    for i in range(0, len(data4)):
        records4.append([str(data4.values[i,j]) for j in range(0, 8)])
    associationRules_4 = apriori(records4, min_support=0.55, min_confidence=0.9, min_length = 2)
    associationResults_4 = list(associationRules_4)
    

    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, frozenset):
                return list(obj)
            return json.JSONEncoder.default(self, obj)
    #data = json.dumps(list(data_result), cls=SetEncoder)
    return json.dumps(list(associationResults_2), cls=SetEncoder)


@app.route("/asosiasi",methods=['GET','POST'])
def asosiasi():
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
    return render_template("asosiasi.html", menu="data",submenu="asosiasi")
 

@app.route('/insert', methods = ['POST'])
def insert():
    if request.method == "POST":
        name = request.form['name']
        cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM test")
        #id = cur.lastrowid
        cur.execute("INSERT INTO test(name) VALUES(%s)",(name))
        
        mysql.connection.commit()
        return redirect(url_for('datapenilaian'))

@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    #flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM test WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('datapenilaian'))











@app.route('/datauser')
def datauser():
    #cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        name = userDetails['name']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO test(id,name) VALUES( %s)",(id, name))
        mysql.connection.commit()
        cur.close()
        return 'success'
   #nilai = cur.fetchall()
    
    #return render_template("datapenilaian.html", menu="data",submenu="penilaian", data="nilai")


#def allowed_file(filename):
 #   return '.' in filename and \
  #         filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#@app.route("/clustering",methods=["POST"])
#def get_input_values():
#   val = request.form['my_form']

@app.route("/predict",methods=["POST","GET"])
def predict():
    if request.method == 'GET':
        return 'The url /predict is acessed directly. Go to the main page first'
    if request.method == 'POST':
        input_val = request.form
        if input_val != None:
            vals = []
            for key, value in input_val.items():
                vals.append(float(value))

        with open ('centroids.pkl','rb') as file:
            centroid = pickle.load(file)

#def clustering():
    #return render_template("clustering.html", menu="data",submenu="clustering")

@app.route("/prosescluster", methods=["POST"])
def prosescluster():
    cluster = request.form['cluster']
    return redirect(url_for('clustering'))



if __name__ == "__main__":
    app.run(debug=True)