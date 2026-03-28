import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "agent_credit_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Agents 表：保存账号密码、当前积分
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        points INTEGER NOT NULL DEFAULT 0 CHECK(points >= 0),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Tasks 表：保存挂出的任务
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        reward_points INTEGER NOT NULL CHECK(reward_points > 0),
        status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employer_id) REFERENCES agents (id)
    )
    ''')

    # 3. Reputation Records 表：交易记录及信誉评价
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reputation_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        employer_id INTEGER NOT NULL,
        worker_id INTEGER NOT NULL,
        points_transferred INTEGER NOT NULL,
        rating INTEGER CHECK(rating >= 0 AND rating <= 10), -- 0~10分评价
        comment TEXT, -- 文字评价
        completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks (id),
        FOREIGN KEY (employer_id) REFERENCES agents (id),
        FOREIGN KEY (worker_id) REFERENCES agents (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("数据库初始化完成！")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def demo_workflow():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 清空旧数据以便演示
    cursor.executescript("DELETE FROM reputation_records; DELETE FROM tasks; DELETE FROM agents;")

    # 1. 注册两个 Agent
    cursor.execute("INSERT INTO agents (username, password_hash, points) VALUES (?, ?, ?)", 
                   ("EmployerAgent", hash_password("pass123"), 1000))
    employer_id = cursor.lastrowid

    cursor.execute("INSERT INTO agents (username, password_hash, points) VALUES (?, ?, ?)", 
                   ("WorkerAgent", hash_password("pass456"), 50))
    worker_id = cursor.lastrowid

    print(f"创建了雇主 Agent(ID:{employer_id}, 1000积分) 和 劳工 Agent(ID:{worker_id}, 50积分)")

    # 2. 雇主发布一个任务
    reward = 200
    cursor.execute("INSERT INTO tasks (employer_id, title, description, reward_points) VALUES (?, ?, ?, ?)",
                   (employer_id, "帮我爬取某个网站的数据", "需要提供完整结构化数据", reward))
    task_id = cursor.lastrowid
    print(f"雇主发布了任务(ID:{task_id})，悬赏 {reward} 积分")

    # 3. 劳工接单并完成任务（此处简化直接标记完成）
    # 更新任务状态
    cursor.execute("UPDATE tasks SET status = 'COMPLETED' WHERE id = ?", (task_id,))
    
    # 扣除雇主积分，增加劳工积分 (利用事务保证一致性)
    cursor.execute("UPDATE agents SET points = points - ? WHERE id = ?", (reward, employer_id))
    cursor.execute("UPDATE agents SET points = points + ? WHERE id = ?", (reward, worker_id))
    
    # 4. 雇主给劳工打分，生成信誉交易记录
    rating = 9
    comment = "做得非常好，数据很干净！"
    cursor.execute('''
    INSERT INTO reputation_records (task_id, employer_id, worker_id, points_transferred, rating, comment)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (task_id, employer_id, worker_id, reward, rating, comment))
    
    conn.commit()
    print(f"交易完成！雇主给劳工打了 {rating} 分，并评价：{comment}")

    # 5. 查询验证结果
    cursor.execute("SELECT username, points FROM agents")
    print("\n当前所有 Agent 的积分：")
    for row in cursor.fetchall():
        print(f"- {row[0]}: {row[1]} 积分")

    cursor.execute('''
    SELECT AVG(rating), COUNT(id) FROM reputation_records WHERE worker_id = ?
    ''', (worker_id,))
    avg_rating, total_tasks = cursor.fetchone()
    print(f"\n劳工 Agent 的历史信誉统计：")
    print(f"- 完成任务数：{total_tasks}")
    print(f"- 平均评分：{avg_rating:.1f}/10")

    conn.close()

if __name__ == "__main__":
    init_db()
    demo_workflow()
