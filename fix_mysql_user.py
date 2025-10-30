import pymysql

# ---- CONFIG ----
host = "shuttle.proxy.rlwy.net"
port = 36857
admin_user = "root"           # Your admin username
admin_password = "LamineYamal10!"  # Your root password
target_user = "api_user"
target_password = "LamineYamal10!"
database = "country_exchange_db"

try:
    conn = pymysql.connect(
        host=host,
        port=port,
        user=admin_user,
        password=admin_password
    )
    cursor = conn.cursor()
    print("✅ Connected as admin")

    # 1. Drop the user if it exists (to remove wrong auth plugin)
    cursor.execute(f"DROP USER IF EXISTS '{target_user}'@'%';")
    print(f"🗑️ Dropped old user '{target_user}' if existed")

    # 2. Recreate the user with the right authentication plugin
    cursor.execute(
        f"CREATE USER '{target_user}'@'%' IDENTIFIED WITH mysql_native_password BY '{target_password}';"
    )
    print(f"✅ Recreated user '{target_user}' with mysql_native_password")

    # 3. Grant privileges
    cursor.execute(
        f"GRANT ALL PRIVILEGES ON {database}.* TO '{target_user}'@'%';"
    )
    print(f"✅ Granted all privileges on {database}")

    # 4. Flush privileges
    cursor.execute("FLUSH PRIVILEGES;")
    print("🔁 Privileges flushed")

    conn.commit()
    conn.close()
    print("🎉 Done — user is now fully ready to connect!")

except Exception as e:
    print("❌ Error:", e)
