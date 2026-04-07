sudo bash setup.sh
# => Chạy tạo file init để tạo database cho jira và confluence

docker compose -f docker-compose.prod.yaml up -d

# => File này đã setup cấu hình kết nối jira và confluence vào database luôn rồi không cần setup ở màn hình Wizard


# CRACK Jira <Replace Server ID> sau tham số -s

docker exec jira java -jar /atlassian-agent.jar -d -m sieupham3057@gmail.com -o mrgoldOrganization -p jira -s BMQA-FADP-AQ4D-ARBX

# CRACK Confluence <Replace Server ID> sau tham số -s

docker exec confluence java -jar /atlassian-agent.jar -d -m sieupham3057@gmail.com -o mrgoldOrganization -p conf -s B3RW-WQZI-AO81-N7WK

# Crack Plugin cho Jira <Replace App Key> sau tham số -p

docker exec jira java -jar /atlassian-agent.jar -d -m sieupham3057@gmail.com -o mrgoldOrganization -p AppKey -s BMQA-FADP-AQ4D-ARBX

# Crack Plugin cho Confluence <Replace App Key> sau tham số -p

docker exec confluence java -jar /atlassian-agent.jar -d -m sieupham3057@gmail.com -o mrgoldOrganization -p AppKey -s BMQA-FADP-AQ4D-ARBX


============================================================
============================================================
============================================================

atlassian@atlassianserver:/atlassian/F-Atlassiance$ cat .env
# ============================================================

# PostgreSQL superuser (dùng để tạo DB qua init.sql)
POSTGRES_PASSWORD=postgres@Atlassian2026

# Jira DB password — phải khớp với init.sql
JIRA_DB_PASSWORD=Jira@Atlassian2026

# Confluence DB password — phải khớp với init.sql
CONFLUENCE_DB_PASSWORD=Confluence@Atlassian2026

# Domain — thay bằng domain thật của công ty
JIRA_DOMAIN=jira.techplus.vn
CONFLUENCE_DOMAIN=confluence.techplus.vn
