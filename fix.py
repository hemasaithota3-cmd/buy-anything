import sqlite3
conn=sqlite3.connect('orders.db')
c=conn.cursor()
c.execute("UPDATE products SET image_url='images/Brown-eggs.webp' WHERE name='Eggs'")
c.execute("UPDATE products SET image_url='images/rice.webp' WHERE name='Rice'")
c.execute("UPDATE products SET image_url='images/sasi_milk.png' WHERE name='Sasi Milk'")
conn.commit()
conn.close()
