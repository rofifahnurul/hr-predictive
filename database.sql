CREATE database hr;
use hr;
CREATE TABLE penilaian(
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
    -> tahun INT,
    -> PRIMARY KEY(id));

CREATE TABLE accounts(
    -> id INT(11) NOT NULL AUTO_INCREMENT,
    -> username varchar(50) NOT NULL,
    -> password varchar(255) NOT NULL,
    -> PRIMARY KEY (id)
    -> );

CREATE TABLE centroid(
    -> id INT NOT NULL AUTO_INCREMENT,
    -> kpi FLOAT NULL,
    -> performance FLOAT NULL,
    -> competency FLOAT NULL,
    -> learning FLOAT NULL,
    -> kerjaIbadah FLOAT NULL,
    -> apresiasi FLOAT NULL,
    -> lebihCepat FLOAT NULL,
    -> aktifBersama FLOAT NULL,
    -> cluster INT NULL,
    -> primary key (id));
