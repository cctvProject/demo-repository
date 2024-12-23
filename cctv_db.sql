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

CREATE TABLE recognition (
    id INT AUTO_INCREMENT PRIMARY KEY, -- 고유 ID
    vehicle_number VARCHAR(20) NOT NULL, -- 차량 번호
    phone_number VARCHAR(20), -- 핸드폰 번호
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP, -- 인식 시간
    entry_exit_input VARCHAR(10), -- 입차 또는 출차
    vehicle_type VARCHAR(10), -- 차량 종류
    image_path VARCHAR(255) -- 이미지 경로 (옵션)
);

TRUNCATE TABLE entry_recognition;

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

CREATE TABLE category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) UNIQUE NOT NULL,
    description VARCHAR(255)
);

TRUNCATE TABLE users;

SELECT * FROM illegal_parking_vehicle_recognitioninquiries;

INSERT INTO users (username, password, email, name, phone, role) 
VALUES 
('admin', '$2b$12$frfPuO51upyvC6UNoqTLFOWpJmUptEuwSLHaWjsoV.CHJrsBCGJSi', 'admin@example.com', '관리자', '010-0000-0000', 'admin');

SHOW VARIABLES LIKE 'character_set%';
ALTER DATABASE cctv_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE category CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

SHOW DATABASES;

CREATE TABLE category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) UNIQUE NOT NULL,
    description VARCHAR(255)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

DELIMITER //

CREATE PROCEDURE InsertRandom(IN total_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0; -- 반복문을 위한 카운터
    DECLARE han_char VARCHAR(20) DEFAULT '가나다라마바사아자차카타파하'; -- 한글 목록
    DECLARE han_len INT DEFAULT CHAR_LENGTH(han_char); -- 한글 목록의 길이
    DECLARE random_hangul CHAR(1); -- 선택된 한글
    DECLARE random_entry_exit CHAR(5); -- entry_exit_input 필드 값
    DECLARE random_vehicle_type VARCHAR(10); -- vehicle_type 필드 값

    WHILE i < total_rows DO
        -- 한글 중 랜덤으로 1글자 선택
        SET random_hangul = SUBSTRING(han_char, FLOOR(1 + RAND() * han_len), 1);

        -- entry_exit_input 랜덤 선택 ('entry' 또는 'exit')
        SET random_entry_exit = IF(RAND() < 0.5, 'entry', 'exit');

        -- vehicle_type 랜덤 선택 ('light', 'disabled', 'illegal', 'normal')
        SET random_vehicle_type = CASE
            WHEN RAND() < 0.25 THEN 'light'
            WHEN RAND() < 0.5 THEN 'disabled'
            WHEN RAND() < 0.75 THEN 'illegal'
            ELSE 'normal'
        END;

        -- 데이터 삽입
        INSERT INTO recognition (vehicle_number, phone_number, recognition_time, entry_exit_input, vehicle_type)
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
            NOW(),
            -- 랜덤 entry_exit_input
            random_entry_exit,
            -- 랜덤 vehicle_type
            random_vehicle_type
        );

        SET i = i + 1; -- 반복문 증가
    END WHILE;
END;
//

CALL InsertRandom(1000); -- 10개의 랜덤 데이터 삽입

INSERT INTO users (username, password, email, name, phone, role)
VALUES ('admin', '$2b$12$tXpmbHqehJd.xDKR2ZskLejU1wTSKm1Q0sF44yi1lt38UIEG605eK', 'admin@example.com', '관리자', '010-1234-5678', 'admin');

select * from users;