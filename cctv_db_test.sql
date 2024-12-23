ALTER TABLE recognition MODIFY entry_exit_input VARCHAR(50) NULL;
ALTER TABLE recognition MODIFY vehicle_type VARCHAR(50) NULL;

DROP PROCEDURE IF EXISTS InsertRandom;

TRUNCATE TABLE recognition;

DROP PROCEDURE IF EXISTS InsertRandom;

DELIMITER //

CREATE PROCEDURE InsertEntryData(IN total_rows INT)
BEGIN
    DECLARE i INT DEFAULT 0; -- 반복문을 위한 카운터
    DECLARE han_char VARCHAR(14) DEFAULT '가나다라마바사아자차카타파하'; -- 받침 없는 한글 목록
    DECLARE han_len INT DEFAULT CHAR_LENGTH(han_char); -- 한글 목록의 길이
    DECLARE random_hangul CHAR(1); -- 선택된 한글
    DECLARE random_vehicle_type VARCHAR(10); -- vehicle_type 필드 값

    -- entry 번호를 먼저 삽입
    WHILE i < total_rows DO
        -- 한글 중 랜덤으로 1글자 선택
        SET random_hangul = SUBSTRING(han_char, FLOOR(1 + RAND() * han_len), 1);

        -- vehicle_type은 entry일 때만 설정
        SET random_vehicle_type = CASE
            WHEN RAND() < 0.2 THEN 'light'
            WHEN RAND() < 0.4 THEN 'disabled'
            WHEN RAND() < 0.6 THEN 'illegal'
            WHEN RAND() < 0.8 THEN 'normal'
            ELSE NULL
        END;

        -- entry 차량 번호 삽입
        INSERT INTO recognition (vehicle_number, phone_number, recognition_time, entry_exit_input, vehicle_type)
        VALUES (
            CONCAT(
                LPAD(FLOOR(RAND() * 90 + 10), 2, '0'), -- 숫자 두 자리 (10~99)
                random_hangul, -- 미리 정의된 한글 중 랜덤 선택
                ' ', -- 띄어쓰기
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            CONCAT(
                '010-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0'), -- 숫자 네 자리 (1000~9999)
                '-', 
                LPAD(FLOOR(RAND() * 9000 + 1000), 4, '0') -- 숫자 네 자리 (1000~9999)
            ),
            NOW(),
            'entry', -- entry 입력
            random_vehicle_type
        );

        SET i = i + 1; -- 반복문 증가
    END WHILE;

END;
//

DELIMITER ;



DELIMITER //

CREATE PROCEDURE InsertExitData()
BEGIN
    DECLARE selected_exit_count INT; -- 선택된 exit 차량 수
    DECLARE vehicle_ids TEXT; -- vehicle_id 목록을 저장할 변수
    DECLARE query VARCHAR(1000); -- 동적 쿼리 저장할 변수

    -- entry 차량 수의 70% 계산
    SET selected_exit_count = (SELECT FLOOR(COUNT(*) * 0.7) FROM recognition WHERE entry_exit_input = 'entry');

    -- 동적 쿼리로 entry 차량의 id 목록을 랜덤으로 선택하여 하나의 문자열로 합침
    SET query = CONCAT(
        'SELECT GROUP_CONCAT(id ORDER BY RAND() LIMIT ', selected_exit_count, ') INTO @vehicle_ids FROM recognition WHERE entry_exit_input = "entry"'
    );

    -- 동적 쿼리 실행
    PREPARE stmt FROM query;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- vehicle_ids가 비어있지 않으면 exit으로 업데이트
    IF @vehicle_ids IS NOT NULL AND @vehicle_ids != '' THEN
        UPDATE recognition
        SET entry_exit_input = 'exit'
        WHERE FIND_IN_SET(id, @vehicle_ids) > 0;
    END IF;
END //

DELIMITER ;

DESCRIBE recognition;
DROP PROCEDURE IF EXISTS InsertExitData;

select * from recognition;
CALL InsertEntryData(5000); -- 예시로 5000개의 입차 데이터를 삽입
CALL InsertExitData();
