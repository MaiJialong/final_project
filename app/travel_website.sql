CREATE DATABASE travel_website;

USE travel_website;

CREATE TABLE bookings (
  ssn INT(9) PRIMARY KEY,
  name TEXT,
  age INT,
  phone INT(10),
  tour_date DATE,
  destination TEXT
);

INSERT INTO bookings (ssn, name, age, phone, tour_date, destination)
VALUES (123456789, 'John Doe', 30, 1234567890, '2024-12-10', 'Kyoto');
