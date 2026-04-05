#!/bin/bash

set -e  # Dừng ngay nếu có lỗi

echo "=== Tạo thư mục ==="
mkdir -p /srv/atlassian/postgres/init

echo "=== Tạo file init.sql ==="
cat > /srv/atlassian/postgres/init/init.sql << 'SQL'
-- Tạo user cho Jira
CREATE USER jira WITH PASSWORD 'Jira@Atlassian2026';
-- Tạo user cho Confluence
CREATE USER confluence WITH PASSWORD 'Confluence@Atlassian2026';

-- Tạo database cho Jira
CREATE DATABASE jira_db
    OWNER jira
    ENCODING 'UNICODE'
    LC_COLLATE 'C'
    LC_CTYPE 'C'
    TEMPLATE template0;

-- Tạo database cho Confluence
CREATE DATABASE confluence_db
    OWNER confluence
    ENCODING 'UNICODE'
    LC_COLLATE 'C'
    LC_CTYPE 'C'
    TEMPLATE template0;

-- Cấp quyền
GRANT ALL PRIVILEGES ON DATABASE jira_db TO jira;
GRANT ALL PRIVILEGES ON DATABASE confluence_db TO confluence;
SQL

echo "=== Cấp quyền file init.sql ==="
chmod 644 /srv/atlassian/postgres/init/init.sql

echo ""
echo "✅ Xong! Kiểm tra:"
ls -la /srv/atlassian/postgres/init/
