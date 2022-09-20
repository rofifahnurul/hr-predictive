import pandas as pd
import numpy as np
from sklearn import preprocessing
import pickle
from sklearn.decomposition import PCA 
def kmeans(data,data_numeric):
    #with open ('centroids.pkl','rb') as file:
    #    centroid = pickle.load(file)
    #    columnC = centroid.columns
    #path = "/Users/agussuyono/documents/hr-predictive/centroid.csv"
    #centroid = pd.read_csv(path)
    K=4
    Centroids = data_numeric.sample(n=K)
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
            if flag == 0:                              
                print("Masuk",pos)
            else:
                print("update",pos,row[1],row[2],row[3],row[4])

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
        
        #Centroids = data_numeric.groupby(["cluster"]).mean()[[column[0],column[1],column[2],column[3],
        #column[4],column[5],column[6],column[7]]]
  

    return tes, Centroids, data, data_numeric

def compPCA(data,data_cluster):
    pca = PCA(n_components=3)
    xPCA = pca.fit_transform(data)
    xPCA = pd.DataFrame(xPCA)
    xPCA.columns=["pc1","pc2","pc3"]
    xPCA["y"]=data_cluster
    return xPCA

'''
def read_file(filename):
    path = "/Users/agussuyono/documents/project-skripsi/file/"+filename
    df = pd.read_excel(path)
    array = df.values
    X = array[:,2:9]
    min_max_scaler = preprocessing.MinMaxScaler(feature_range=(0,1)) #inisialisasi normalisasi MinMax
    data = min_max_scaler.fit_transform(X) #transformasi MinMax untuk fitur
    dataset = pd.DataFrame({'NIK':array[:,1],'PK':data[:,0],'COMPETENCY':data[:,1],'LEARNING POINT':data[:,2],'Kerja Ibadah':data[:,3],'Apresiasi':data[:,4],'Lebih cepat':data[:,5],'Aktif bersama':data[:,6],})
    filename_split=filename.rsplit('.', 1)[0]
    path = r'/Users/agussuyono/documents/project-skripsi/csv/normalize'+filename_split+".csv"
    dataset.to_csv(path, index = None, header=True)
    return df
'''

