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

TRUNCATE TABLE entry_recognition;

DELIMITER //
CREATE PROCEDURE InsertRandom1(IN total_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0; -- 반복문을 위한 카운터
    DECLARE han_char VARCHAR(20) DEFAULT '가나다라마바사아자차카타파하'; -- 한글 목록
    DECLARE han_len INT DEFAULT CHAR_LENGTH(han_char); -- 한글 목록의 길이
    DECLARE random_hangul CHAR(1); -- 선택된 한글

    WHILE i < total_rows DO
        -- 한글 중 랜덤으로 1글자 선택
        SET random_hangul = SUBSTRING(han_char, FLOOR(1 + RAND() * han_len), 1);

        -- 데이터 삽입
        INSERT INTO entry_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (
            -- 차량 번호
            CONCAT(
                LPAD(FLOOR(RAND() * 90 + 10), 2, '0'), -- 숫자 두 자리 (10~99)
                random_hangul, -- 미리 정의된 한글 중 랜덤 선택
                ' ', -- 띄어쓰기
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 핸드폰 번호
            CONCAT(
                '010-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0'), -- 숫자 네 자리 (1000~9999)
                '-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 현재 시간
            NOW()
        );

        SET i = i + 1; -- 반복문 증가
    END WHILE;
END;
//DELIMITER ;

DELIMITER //
CREATE PROCEDURE InsertRandom2(IN total_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0; -- 반복문을 위한 카운터
    DECLARE han_char VARCHAR(20) DEFAULT '가나다라마바사아자차카타파하'; -- 한글 목록
    DECLARE han_len INT DEFAULT CHAR_LENGTH(han_char); -- 한글 목록의 길이
    DECLARE random_hangul CHAR(1); -- 선택된 한글

    WHILE i < total_rows DO
        -- 한글 중 랜덤으로 1글자 선택
        SET random_hangul = SUBSTRING(han_char, FLOOR(1 + RAND() * han_len), 1);

        -- 데이터 삽입
        INSERT INTO exit_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (
            -- 차량 번호
            CONCAT(
                LPAD(FLOOR(RAND() * 90 + 10), 2, '0'), -- 숫자 두 자리 (10~99)
                random_hangul, -- 미리 정의된 한글 중 랜덤 선택
                ' ', -- 띄어쓰기
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 핸드폰 번호
            CONCAT(
                '010-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0'), -- 숫자 네 자리 (1000~9999)
                '-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 현재 시간
            NOW()
        );

        SET i = i + 1; -- 반복문 증가
    END WHILE;
END;
//DELIMITER ;


DELIMITER //
CREATE PROCEDURE InsertRandom3(IN total_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0; -- 반복문을 위한 카운터
    DECLARE han_char VARCHAR(20) DEFAULT '가나다라마바사아자차카타파하'; -- 한글 목록
    DECLARE han_len INT DEFAULT CHAR_LENGTH(han_char); -- 한글 목록의 길이
    DECLARE random_hangul CHAR(1); -- 선택된 한글

    WHILE i < total_rows DO
        -- 한글 중 랜덤으로 1글자 선택
        SET random_hangul = SUBSTRING(han_char, FLOOR(1 + RAND() * han_len), 1);

        -- 데이터 삽입
        INSERT INTO light_vehicle_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (
            -- 차량 번호
            CONCAT(
                LPAD(FLOOR(RAND() * 90 + 10), 2, '0'), -- 숫자 두 자리 (10~99)
                random_hangul, -- 미리 정의된 한글 중 랜덤 선택
                ' ', -- 띄어쓰기
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 핸드폰 번호
            CONCAT(
                '010-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0'), -- 숫자 네 자리 (1000~9999)
                '-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 현재 시간
            NOW()
        );

        SET i = i + 1; -- 반복문 증가
    END WHILE;
END;
//DELIMITER ;

DELIMITER //
CREATE PROCEDURE InsertRandom4(IN total_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0; -- 반복문을 위한 카운터
    DECLARE han_char VARCHAR(20) DEFAULT '가나다라마바사아자차카타파하'; -- 한글 목록
    DECLARE han_len INT DEFAULT CHAR_LENGTH(han_char); -- 한글 목록의 길이
    DECLARE random_hangul CHAR(1); -- 선택된 한글

    WHILE i < total_rows DO
        -- 한글 중 랜덤으로 1글자 선택
        SET random_hangul = SUBSTRING(han_char, FLOOR(1 + RAND() * han_len), 1);

        -- 데이터 삽입
        INSERT INTO disabled_vehicle_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (
            -- 차량 번호
            CONCAT(
                LPAD(FLOOR(RAND() * 90 + 10), 2, '0'), -- 숫자 두 자리 (10~99)
                random_hangul, -- 미리 정의된 한글 중 랜덤 선택
                ' ', -- 띄어쓰기
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 핸드폰 번호
            CONCAT(
                '010-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0'), -- 숫자 네 자리 (1000~9999)
                '-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 현재 시간
            NOW()
        );

        SET i = i + 1; -- 반복문 증가
    END WHILE;
END;
//DELIMITER ;

DELIMITER //
CREATE PROCEDURE InsertRandom5(IN total_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0; -- 반복문을 위한 카운터
    DECLARE han_char VARCHAR(20) DEFAULT '가나다라마바사아자차카타파하'; -- 한글 목록
    DECLARE han_len INT DEFAULT CHAR_LENGTH(han_char); -- 한글 목록의 길이
    DECLARE random_hangul CHAR(1); -- 선택된 한글

    WHILE i < total_rows DO
        -- 한글 중 랜덤으로 1글자 선택
        SET random_hangul = SUBSTRING(han_char, FLOOR(1 + RAND() * han_len), 1);

        -- 데이터 삽입
        INSERT INTO illegal_parking_vehicle_recognition (vehicle_number, phone_number, recognition_time)
        VALUES (
            -- 차량 번호
            CONCAT(
                LPAD(FLOOR(RAND() * 90 + 10), 2, '0'), -- 숫자 두 자리 (10~99)
                random_hangul, -- 미리 정의된 한글 중 랜덤 선택
                ' ', -- 띄어쓰기
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 핸드폰 번호
            CONCAT(
                '010-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0'), -- 숫자 네 자리 (1000~9999)
                '-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            -- 현재 시간
            NOW()
        );

        SET i = i + 1; -- 반복문 증가
    END WHILE;
END;
//DELIMITER ;

CALL InsertRandom5(100);

DELETE FROM disabled_vehicle_recognition 
WHERE id NOT IN (
    SELECT id 
    FROM (
        SELECT id 
        FROM disabled_vehicle_recognition 
        ORDER BY recognition_time DESC 
        LIMIT 10
    ) AS temp
);

TRUNCATE TABLE users;

SELECT * FROM users WHERE username = admin;

TRUNCATE TABLE users;

INSERT INTO users (username, password, email, name, phone, role) 
VALUES 
('admin', '$2b$12$frfPuO51upyvC6UNoqTLFOWpJmUptEuwSLHaWjsoV.CHJrsBCGJSi', 'admin@example.com', '관리자', '010-0000-0000', 'admin');

