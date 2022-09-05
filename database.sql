CREATE database hr;
use hr;
CREATE TABLE nilai2021(
    -> id INT NOT NULL AUTO_INCREMENT,
    -> nik VARCHAR(15) NULL,
    -> kpi FLOAT NULL,
    -> performance FLOAT NULL,
    -> competency FLOAT NULL,
    -> learning FLOAT NULL,
    -> kerjaIbadah FLOAT NULL,
    -> apresiasi FLOAT NULL,
    -> lebihCepat FLOAT NULL, 
    -> aktifBersama FLOAT NULL,
    -> PRIMARY KEY(id));