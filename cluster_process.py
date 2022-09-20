import pandas as pd
import numpy as np
from sklearn import preprocessing
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