INSERT INTO entry_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES ('1234AB', '010-1234-5678', '2024-06-12 10:00:00', 'static/images/entry_1234AB.jpg');

INSERT INTO exit_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES ('1234AB', '010-1234-5678', '2024-06-12 10:30:00', 'static/images/exit_1234AB.jpg');

TRUNCATE TABLE recognition_categories;

select * from recognition_categories;

INSERT INTO setting (fee_per_10_minutes, total_parking_slots, total_floors)
VALUES (1000, 50, 5);


INSERT INTO entry_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES 
('1234AB', '010-1234-5678', '2024-06-12 09:00:00', 'static/images/entry_1234AB.jpg'),
('5678CD', '010-5678-1234', '2024-06-12 09:30:00', 'static/images/entry_5678CD.jpg');

INSERT INTO exit_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES 
('1234AB', '010-1234-5678', '2024-06-12 12:00:00', 'static/images/exit_1234AB.jpg'),
('5678CD', '010-5678-1234', '2024-06-12 11:30:00', 'static/images/exit_5678CD.jpg');

SELECT 
    e.vehicle_number AS 차량번호,
    TIMESTAMPDIFF(MINUTE, e.recognition_time, x.recognition_time) AS 주차시간_분,
    (FLOOR(TIMESTAMPDIFF(MINUTE, e.recognition_time, x.recognition_time) / 10) * s.fee_per_10_minutes) AS 총_요금
FROM 
    entry_recognition e
JOIN 
    exit_recognition x ON e.vehicle_number = x.vehicle_number
CROSS JOIN 
    setting s
WHERE 
    e.recognition_time <= x.recognition_time;
SELECT * FROM entry_recognition;
SELECT * FROM exit_recognition;
SELECT * FROM setting;

INSERT INTO entry_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES
('1234AB', '010-1234-5678', '2024-06-12 09:00:00', 'static/images/entry_1234AB.jpg'),
('5678CD', '010-5678-1234', '2024-06-12 09:30:00', 'static/images/entry_5678CD.jpg'),
('9012EF', '010-9012-3456', '2024-06-12 10:00:00', 'static/images/entry_9012EF.jpg');

INSERT INTO exit_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES
('1234AB', '010-1234-5678', '2024-06-12 12:00:00', 'static/images/exit_1234AB.jpg'),
('5678CD', '010-5678-1234', '2024-06-12 11:30:00', 'static/images/exit_5678CD.jpg');

SELECT 
    COUNT(DISTINCT e.vehicle_number) AS 현재_주차수
FROM 
    entry_recognition e
LEFT JOIN 
    exit_recognition x 
ON 
    e.vehicle_number = x.vehicle_number
WHERE 
    x.vehicle_number IS NULL OR e.recognition_time > x.recognition_time;

INSERT INTO entry_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES
('1234AB', '010-1234-5678', '2024-06-12 09:00:00', 'static/images/entry_1234AB.jpg'),
('5678CD', '010-5678-1234', '2024-06-12 09:30:00', 'static/images/entry_5678CD.jpg'),
('9012EF', '010-9012-3456', '2024-06-12 10:00:00', 'static/images/entry_9012EF.jpg');

INSERT INTO exit_recognition (vehicle_number, phone_number, recognition_time, image_path)
VALUES
('1234AB', '010-1234-5678', '2024-06-12 12:00:00', 'static/images/exit_1234AB.jpg'),
('5678CD', '010-5678-1234', '2024-06-12 11:30:00', 'static/images/exit_5678CD.jpg');

INSERT INTO reports (user_name, start_time, end_time, entry_count, exit_count, current_parking_count, total_fee)
VALUES 
('test_user', '2024-06-12 08:00:00', NULL, 0, 0, 0, 0); -- 출근


INSERT INTO reports (user_name, start_time, end_time, entry_count, exit_count, current_parking_count, total_fee)
VALUES 
('admin', '2024-06-12 08:00:00', NULL, 0, 0, 0, 0); -- 출근

SELECT * FROM entry_recognition ORDER BY created_at DESC LIMIT 10;
