# 🚀 Deployment Guide for Anonka Bot

## Prerequisites

- Linux server (Ubuntu 20.04+)
- Python 3.9+
- MySQL 5.7+
- SSH access to server
- Telegram Bot Token (from @BotFather)
- Group Chat ID and Topic ID

## Step 1: Get Required IDs from Telegram

### 1.1 Create Telegram Bot

1. Open [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions to create a new bot
4. Copy the API token (example: `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg`)

### 1.2 Get Group Chat ID

1. Create a new Telegram group or use existing one
2. Add your bot to the group as an admin
3. Send a test message to the group
4. Open in browser: `https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getUpdates`
   - Replace `{YOUR_BOT_TOKEN}` with your token
5. Look for `"chat":{"id":-1001234567890}` (negative number)
6. Copy the chat ID

### 1.3 Get Topic ID (Optional, for Topics)

1. Enable Topics in your group settings
2. Create a new topic
3. Send a message to that topic
4. Check getUpdates again for `"message_thread_id":123` value
5. If you want to use main chat, set `GROUP_TOPIC_ID=0`

## Step 2: Deploy on Your Server

### Option A: Automatic Deployment Script

```bash
# SSH into your server
ssh anton@192.168.0.36

# Clone and deploy
curl -sSL https://raw.githubusercontent.com/Mukller/Anonka/main/deploy.sh | bash

# Edit configuration
nano /home/anton/anonka/.env

# Start the bot
systemctl start anonka
systemctl status anonka
```

### Option B: Manual Deployment

```bash
# 1. SSH to server
ssh anton@192.168.0.36

# 2. Install MySQL (if not installed)
sudo apt-get update
sudo apt-get install -y mysql-server

# 3. Create database
mysql -u root -p -e "CREATE DATABASE anonka CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. Clone repository
mkdir -p /home/anton/anonka
cd /home/anton/anonka
git clone https://github.com/Mukller/Anonka.git .

# 5. Create Python environment
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Create and edit .env file
cp .env.example .env
nano .env
# Add:
# BOT_TOKEN=your_token_here
# GROUP_CHAT_ID=your_group_id_here
# GROUP_TOPIC_ID=0
# DB_PASSWORD=your_mysql_root_password

# 8. Initialize database
cd backend
python init_db.py

# 9. Test the bot manually (optional)
cd ..
python -m backend.app.main
# Press Ctrl+C to stop

# 10. Create systemd service
sudo cp /home/anton/anonka/anonka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable anonka
sudo systemctl start anonka

# 11. Check status
systemctl status anonka

# 12. View logs
journalctl -u anonka -f
```

## Step 3: Configuration

Edit `/home/anton/anonka/.env`:

```env
# Telegram Bot
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg
GROUP_CHAT_ID=-1001234567890
GROUP_TOPIC_ID=0

# MySQL Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=anonka
```

## Step 4: Verify Installation

```bash
# Check service status
systemctl status anonka

# View recent logs
journalctl -u anonka -n 50

# Follow logs in real-time
journalctl -u anonka -f

# Test bot
# 1. Send /start to the bot in Telegram
# 2. Send a test message
# 3. Check if it appears in the group
```

## Step 5: Backup and Maintenance

### Daily Backup

```bash
# Create backup script: /home/anton/anonka/backup.sh
#!/bin/bash
BACKUP_DIR="/home/anton/anonka/backups"
mkdir -p $BACKUP_DIR
mysqldump -u root -p anonka > $BACKUP_DIR/anonka_$(date +%Y%m%d_%H%M%S).sql

# Make it executable
chmod +x /home/anton/anonka/backup.sh

# Add to crontab (runs daily at 2 AM)
crontab -e
# Add line: 0 2 * * * /home/anton/anonka/backup.sh
```

### Check Logs

```bash
# Last 50 lines
journalctl -u anonka -n 50

# Last hour
journalctl -u anonka --since "1 hour ago"

# Specific date
journalctl -u anonka --since "2026-05-20"

# With pager (less)
journalctl -u anonka -e
```

### Update Bot

```bash
# 1. Stop the bot
systemctl stop anonka

# 2. Pull latest code
cd /home/anton/anonka
git pull origin main

# 3. Update dependencies (if needed)
source venv/bin/activate
pip install -r requirements.txt

# 4. Start the bot
systemctl start anonka

# 5. Check logs
journalctl -u anonka -f
```

## Troubleshooting

### Bot doesn't respond

```bash
# Check if service is running
systemctl status anonka

# Check logs for errors
journalctl -u anonka -n 100

# Verify token is correct
grep BOT_TOKEN /home/anton/anonka/.env

# Test database connection
mysql -u root -p anonka -e "SELECT COUNT(*) FROM users;"
```

### Database connection error

```bash
# Check MySQL is running
systemctl status mysql

# Verify credentials in .env
cat /home/anton/anonka/.env | grep DB_

# Try connecting manually
mysql -u root -p anonka -e "SELECT 1;"

# Check MySQL bindings
mysql -u root -p -e "SHOW VARIABLES LIKE 'bind_address';"
```

### Messages not appearing in group

1. Check bot has admin permissions in group
2. Verify GROUP_CHAT_ID is correct
3. Check GROUP_TOPIC_ID matches your topic
4. Send /start to bot and check for error messages
5. View logs: `journalctl -u anonka -f`

### Port already in use (if running manually)

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Performance Monitoring

```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check MySQL size
mysql -u root -p -e "SELECT table_schema, ROUND(SUM(data_length+index_length)/1024/1024, 2) AS 'Size in MB' FROM information_schema.TABLES GROUP BY table_schema;"

# Restart bot if needed
systemctl restart anonka
```

## Security

1. **Change MySQL password**
   ```bash
   mysql -u root -p
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_secure_password';
   FLUSH PRIVILEGES;
   ```

2. **Restrict bot permissions in group**
   - Only give "Delete messages" and "Pin messages" permissions

3. **Enable firewall**
   ```bash
   sudo ufw enable
   sudo ufw allow 3306/tcp from 127.0.0.1
   sudo ufw allow 22/tcp  # SSH
   ```

4. **Regular backups**
   - See backup section above

## Support

For issues, visit: https://github.com/Mukller/Anonka/issues
