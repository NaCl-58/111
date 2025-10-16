import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="个人信息管理系统", page_icon="🌱", layout="wide")

# 数据库配置
BASE_DIR = Path().parent
DB_PATH = BASE_DIR / "data" / "personal_info.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        conn.execute('''
                     CREATE TABLE IF NOT EXISTS personal_info
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         title
                         TEXT
                         NOT
                         NULL,
                         category
                         TEXT,
                         notes
                         TEXT,
                         priority
                         TEXT,
                         status
                         TEXT,
                         tags
                         TEXT,
                         created_at
                         TEXT
                         DEFAULT
                         CURRENT_TIMESTAMP
                     )
                     ''')
        conn.commit()
        conn.close()

    def execute_query(self, query, params=()):
        """执行查询并返回DataFrame"""
        conn = self.get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def execute_update(self, query, params=()):
        """执行更新操作"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id


# 初始化数据库
db = DatabaseManager(DB_PATH)


def main():
    st.title("🌱 个人信息管理系统")
    st.caption("基于SQLite数据库的个人信息管理系统")

    # 侧边栏导航
    menu = st.sidebar.selectbox(
        "导航菜单",
        ["数据总览", "添加信息", "编辑信息", "删除信息"]
    )

    if menu == "数据总览":
        show_data_overview()
    elif menu == "添加信息":
        add_info()
    elif menu == "编辑信息":
        edit_info()
    elif menu == "删除信息":
        delete_info()


def show_data_overview():
    """数据总览"""
    st.header("📊 数据总览")

    # 获取所有数据
    df = db.execute_query("SELECT * FROM personal_info ORDER BY created_at DESC")

    if df.empty:
        st.info("暂无数据，请先添加个人信息")
        return

    # 显示数据
    st.dataframe(df, use_container_width=True)

    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总记录数", len(df))
    with col2:
        st.metric("类别数量", df["category"].nunique())
    with col3:
        st.metric("进行中", len(df[df["status"] == "进行中"]))
    with col4:
        st.metric("高优先级", len(df[df["priority"] == "高"]))


def add_info():
    """添加信息"""
    st.header("➕ 添加个人信息")

    with st.form("add_form", clear_on_submit=True):
        title = st.text_input("标题 *", placeholder="例如：三好学生")

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("类别", ["荣誉", "教育经历", "竞赛", "证书", "账号", "其他"])
            priority = st.selectbox("优先级", ["高", "中", "低"], index=1)
        with col2:
            status = st.radio("状态", ["进行中", "已完成", "待开始"])
            tags = st.text_input("标签", placeholder="用逗号分隔多个标签")

        notes = st.text_area("备注", placeholder="详细描述或补充信息...", height=100)

        submitted = st.form_submit_button("保存信息", type="primary", use_container_width=True)

        if submitted:
            if not title:
                st.error("标题是必填项！")
            else:
                # 使用SQL插入数据
                db.execute_update('''
                                  INSERT INTO personal_info (title, category, notes, priority, status, tags)
                                  VALUES (?, ?, ?, ?, ?, ?)
                                  ''', (title, category, notes, priority, status, tags))

                st.success("信息添加成功！")
                st.rerun()


def edit_info():
    """编辑信息"""
    st.header("✏️ 编辑信息")

    # 获取所有数据用于选择
    df = db.execute_query("SELECT * FROM personal_info ORDER BY created_at DESC")

    if df.empty:
        st.info("暂无数据可编辑")
        return

    # 选择要编辑的记录
    record_options = {f"{row['title']} (ID: {row['id']})": row['id'] for _, row in df.iterrows()}
    selected_record = st.selectbox("选择要编辑的记录", list(record_options.keys()))

    if selected_record:
        record_id = record_options[selected_record]
        record_data = df[df["id"] == record_id].iloc[0]

        # 编辑表单
        with st.form("edit_form"):
            st.write("### 编辑记录")

            title = st.text_input("标题 *", value=record_data["title"])

            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("类别", ["荣誉", "教育经历", "竞赛", "证书", "账号", "其他"],
                                        index=["荣誉", "教育经历", "竞赛", "证书", "账号", "其他"].index(
                                            record_data["category"]))
                priority = st.selectbox("优先级", ["高", "中", "低"],
                                        index=["高", "中", "低"].index(record_data["priority"]))
            with col2:
                status = st.radio("状态", ["进行中", "已完成", "待开始"],
                                  index=["进行中", "已完成", "待开始"].index(record_data["status"]))
                tags = st.text_input("标签", value=record_data["tags"] or "")

            notes = st.text_area("备注", value=record_data["notes"] or "", height=100)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("更新信息", type="primary", use_container_width=True)
            with col2:
                if st.form_submit_button("取消", use_container_width=True):
                    st.rerun()

            if submitted:
                if not title:
                    st.error("标题是必填项！")
                else:
                    # 使用SQL更新数据
                    db.execute_update('''
                                      UPDATE personal_info
                                      SET title    = ?,
                                          category = ?,
                                          notes    = ?,
                                          priority = ?,
                                          status   = ?,
                                          tags     = ?
                                      WHERE id = ?
                                      ''', (title, category, notes, priority, status, tags, record_id))

                    st.success("信息更新成功！")
                    st.rerun()


def delete_info():
    """删除信息"""
    st.header("🗑️ 删除信息")

    # 获取所有数据
    df = db.execute_query("SELECT * FROM personal_info ORDER BY created_at DESC")

    if df.empty:
        st.info("暂无数据可删除")
        return

    # 显示数据表格
    st.dataframe(df, use_container_width=True)

    # 选择删除方式
    delete_option = st.radio("删除方式",
                             ["按ID删除单条记录", "删除所有记录"],
                             horizontal=True)

    if delete_option == "按ID删除单条记录":
        record_id = st.number_input("输入要删除的记录ID", min_value=1, step=1)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("删除指定记录", type="secondary", use_container_width=True):
                # 检查记录是否存在
                check_record = db.execute_query("SELECT * FROM personal_info WHERE id = ?", (record_id,))
                if check_record.empty:
                    st.error(f"ID为 {record_id} 的记录不存在！")
                else:
                    # 使用SQL删除数据
                    db.execute_update("DELETE FROM personal_info WHERE id = ?", (record_id,))
                    st.success(f"ID为 {record_id} 的记录已删除！")
                    st.rerun()

    else:  # 删除所有记录
        st.warning("⚠️ 危险操作：这将删除所有记录！")
        confirm = st.checkbox("我确认要删除所有记录")

        if confirm:
            if st.button("删除所有记录", type="primary", use_container_width=True):
                db.execute_update("DELETE FROM personal_info")
                st.success("所有记录已删除！")
                st.rerun()


# 下载功能
def add_download_section():
    """添加数据下载功能"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("数据导出")

    df = db.execute_query("SELECT * FROM personal_info")
    if not df.empty:
        csv_data = df.to_csv(index=False)
        st.sidebar.download_button(
            label="📥 下载CSV",
            data=csv_data,
            file_name=f"personal_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        # 显示数据库信息
        st.sidebar.markdown("---")
        st.sidebar.subheader("数据库信息")
        st.sidebar.text(f"记录数: {len(df)}")
        st.sidebar.text(f"数据库路径: {DB_PATH}")


if __name__ == "__main__":
    main()
    add_download_section()