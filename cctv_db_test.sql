ALTER TABLE recognition MODIFY entry_exit_input VARCHAR(50) NULL;
ALTER TABLE recognition MODIFY vehicle_type VARCHAR(50) NULL;

DROP PROCEDURE IF EXISTS InsertRandom;

TRUNCATE TABLE recognition;

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

        -- entry_exit_input 랜덤 선택 ('entry', 'exit', 또는 NULL)
        SET random_entry_exit = CASE
            WHEN RAND() < 0.4 THEN 'entry'
            WHEN RAND() < 0.8 THEN 'exit'
            ELSE NULL
        END;

        -- vehicle_type 랜덤 선택 ('light', 'disabled', 'illegal', 'normal', 또는 NULL)
        SET random_vehicle_type = CASE
            WHEN RAND() < 0.2 THEN 'light'
            WHEN RAND() < 0.4 THEN 'disabled'
            WHEN RAND() < 0.6 THEN 'illegal'
            WHEN RAND() < 0.8 THEN 'normal'
            ELSE NULL
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

call InsertRandom(5000);