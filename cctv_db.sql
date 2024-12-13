CREATE DATABASE cctv_db;

use cctv_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    name VARCHAR(80) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL
);

CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entry_count INT DEFAULT 0,
    exit_count INT DEFAULT 0,
    current_parking_count INT DEFAULT 0,
    start_time DATETIME NULL,  -- DATETIME 형식
    end_time DATETIME NULL,    -- DATETIME 형식
    total_fee INT DEFAULT 0,   -- 총 요금을 정수로 설정
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_name VARCHAR(80)      -- 사용자 이름으로 참조
);

CREATE TABLE entry_recognition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exit_recognition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE light_vehicle_recognition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE disabled_vehicle_recognition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE illegal_parking_vehicle_recognition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

DELIMITER //

CREATE PROCEDURE InsertSampleData1()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 10 DO
        INSERT INTO illegal_parking_vehicle_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (CONCAT('27가 ', LPAD(i, 4, '0')), CONCAT('010-', LPAD(i, 4, '0'), '-', LPAD(i, 4, '0')), NOW());
        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;

DELIMITER //

CREATE PROCEDURE InsertSampleData2()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 10 DO
        INSERT INTO entry_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (CONCAT('27가 ', LPAD(i, 4, '0')), CONCAT('010-', LPAD(i, 4, '0'), '-', LPAD(i, 4, '0')), NOW());
        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;

DELIMITER //
CREATE PROCEDURE InsertSampleData3()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 10 DO
        INSERT INTO exit_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (CONCAT('27가 ', LPAD(i, 4, '0')), CONCAT('010-', LPAD(i, 4, '0'), '-', LPAD(i, 4, '0')), NOW());
        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;

DELIMITER //
CREATE PROCEDURE InsertSampleData4()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 10 DO
        INSERT INTO disabled_vehicle_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (CONCAT('27가 ', LPAD(i, 4, '0')), CONCAT('010-', LPAD(i, 4, '0'), '-', LPAD(i, 4, '0')), NOW());
        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;

DELIMITER //
CREATE PROCEDURE InsertSampleData5()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 100 DO
        INSERT INTO light_vehicle_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (CONCAT('27가 ', LPAD(i, 4, '0')), CONCAT('010-', LPAD(i, 4, '0'), '-', LPAD(i, 4, '0')), NOW());
        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;

CALL InsertSampleData5();
DROP PROCEDURE IF EXISTS InsertSampleData5;

DELETE FROM illegal_parking_vehicle_recognition 
WHERE id NOT IN (
    SELECT id 
    FROM (
        SELECT id 
        FROM disabled_vehicle_recognition 
        ORDER BY recognition_time DESC 
        LIMIT 10
    ) AS temp
);