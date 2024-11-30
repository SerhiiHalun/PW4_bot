import sqlite3


def populate_quadcopters():
    conn = sqlite3.connect('app_db.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO quadcopters (name, price, flight_time, range, camera_quality, portability, description) VALUES
        ('DJI Mavic Air 2', 25000, 34, 10000, '4K', 'висока', 'Компактний і потужний дрон з відмінною якістю відео і дальністю польоту.'),
        ('DJI Mini 2', 15000, 31, 6000, '4K', 'висока', 'Легкий і портативний дрон з хорошою якістю відео та доступною ціною.'),
        ('DJI Phantom 4 Pro', 50000, 30, 7000, '4K', 'низька', 'Професійний дрон з потужною камерою і стабільною роботою.'),
        ('Autel Robotics EVO Lite+', 40000, 40, 12000, '6K', 'середня', 'Високоякісний дрон з потужною камерою і великою дальністю польоту.'),
        ('Parrot Anafi', 20000, 25, 4000, '4K', 'висока', 'Компактний дрон з гарною якістю відео та легким управлінням.'),
        ('DJI Inspire 2', 150000, 27, 5000, '5.2K', 'низька', 'Професійний дрон для кінематографії з можливістю зйомки у високій роздільній здатності.'),
        ('Fimi X8 SE', 17000, 33, 8000, '4K', 'середня', 'Дрон з хорошим співвідношенням ціна-якість, відмінною дальністю польоту та камерою.'),
        ('Hubsan Zino Pro', 12000, 23, 4000, '4K', 'висока', 'Доступний дрон з хорошою якістю відео та компактним дизайном.'),
        ('Ryze Tello', 5000, 13, 100, 'HD', 'висока', 'Маленький дрон для початківців з базовою камерою і простим управлінням.'),
        ('PowerVision PowerEgg X', 30000, 30, 6000, '4K', 'середня', 'Унікальний дрон, який може використовуватись як камера з ручним управлінням.'),
        ('DJI Matrice 300 RTK', 75000, 55, 15000, '6K', 'низька', 'Промисловий дрон з можливістю використання різних камер та датчиків.'),
        ('Yuneec Typhoon H Plus', 45000, 28, 10000, '4K', 'середня', 'Дрон з шістьма роторами, відмінною стабілізацією та якістю відео.'),
        ('Skydio 2', 35000, 23, 5000, '4K', 'висока', 'Дрон з розширеними функціями автономного польоту та уникнення перешкод.'),
        ('DJI FPV Combo', 30000, 20, 6000, '4K', 'середня', 'Дрон для високошвидкісних польотів та захоплюючих FPV відео.'),
        ('Holy Stone HS720', 10000, 26, 1600, '2K', 'висока', 'Бюджетний дрон з гарною якістю відео та стабілізацією.'),
        ('Potensic D88', 12000, 20, 1500, '2K', 'висока', 'Дрон з доступною ціною, хорошою камерою і легкою портативністю.'),
        ('EACHINE EX4', 8000, 25, 1000, '1080p', 'висока', 'Компактний дрон для початківців з непоганою камерою та стабілізацією.'),
        ('JJRC X11', 7000, 18, 1200, '1080p', 'висока', 'Доступний дрон з базовою камерою, ідеально підходить для новачків.'),
        ('Autel EVO II', 60000, 40, 9000, '8K', 'середня', 'Професійний дрон з найвищою якістю відео та великою дальністю польоту.'),
        ('Walkera Voyager 5', 100000, 40, 20000, '4K', 'низька', 'Промисловий дрон з потужною камерою та великим радіусом дії.'),
        ('Parrot Bebop 2', 11000, 25, 2000, '1080p', 'висока', 'Дрон середнього рівня з гарною камерою та портативністю.')
    ''')
    conn.commit()
    conn.close()